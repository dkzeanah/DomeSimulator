// Real route handlers and real SQLite migrations, isolated from all live services.
// Run: node scripts/test_delivery.mjs (Node 24; esbuild is already a Vite dependency).
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { build } from 'esbuild';

const site = resolve(import.meta.dirname, '..');
const temp = await mkdtemp(join(tmpdir(), 'zeanah-delivery-'));
const sqlite = new DatabaseSync(':memory:');
let checks = 0;
const check = (value, label) => { assert.ok(value,label); checks++; console.log('PASS ' + label); };
class Statement {
  constructor(sql, values = []) { this.sql=sql; this.values=values; }
  bind(...values) { return new Statement(this.sql, values); }
  async first(column) { const row=sqlite.prepare(this.sql).get(...this.values); return column ? row?.[column] ?? null : row ?? null; }
  async all() { return { results:sqlite.prepare(this.sql).all(...this.values),success:true }; }
  async run() { const r=sqlite.prepare(this.sql).run(...this.values); return { success:true,meta:{ changes:Number(r.changes),last_row_id:Number(r.lastInsertRowid) } }; }
}
try {
  for (const name of (await readdir(join(site,'migrations'))).filter(n=>n.endsWith('.sql')).sort())
    sqlite.exec(await readFile(join(site,'migrations',name),'utf8'));
  const bundle=join(temp,'routes.mjs');
  await build({ stdin:{ contents:`export {default as api} from './functions/_lib/routes.ts'; export {loadUser} from './functions/_lib/auth.ts'; export {hmacHex} from './functions/_lib/crypto.ts';`,resolveDir:site },bundle:true,platform:'node',format:'esm',outfile:bundle,logLevel:'silent' });
  const {api,loadUser,hmacHex}=await import(pathToFileURL(bundle).href);
  let available=false;
  const bytes=new TextEncoder().encode('%PDF-1.7\nfixture book\n%%EOF');
  const env={ DB:{ prepare:sql=>new Statement(sql),batch:async stmts=>Promise.all(stmts.map(s=>s.run())) },
    BOOKS:{ head:async()=>available ? {size:bytes.length}:null,get:async()=>available ? {body:bytes,size:bytes.length}:null },
    SESSION_SECRET:'isolated-test-only',TEST_CHECKOUT:'1',PUBLIC_URL:'https://fixture.test',STRIPE_WEBHOOK_SECRET:'isolated-webhook' };
  globalThis.fetch=()=>{ throw new Error('External network forbidden in delivery test'); };
  async function call(method,path,body,cookie='',headers={}) {
    const url=new URL('https://fixture.test/api'+path), match=api.match(method,url.pathname.slice(4));
    assert.ok(match,'Route exists: '+path);
    const request=new Request(url,{method,headers:{...(body ? {'Content-Type':'application/json'}:{}),...headers,...(cookie ? {Cookie:cookie}:{})},body:body ? (typeof body==='string'?body:JSON.stringify(body)):undefined});
    const ctx={request,env,url,params:match.params,user:null,setCookies:[]};
    ctx.user=await loadUser(ctx);
    let response;
    try { response=await match.handler(ctx); } catch(e) { response=new Response(JSON.stringify({error:e.message}),{status:e.status||500}); }
    return {response,data:async()=>response.json()};
  }
  const slug='my-own-home-my-own-dome';
  sqlite.prepare("UPDATE products SET status='live',ships_note=NULL WHERE slug=?").run(slug);
  let r=await call('POST','/checkout',{product:slug,email:'buyer@example.test'});
  check(r.response.status===503 && sqlite.prepare('SELECT COUNT(*) n FROM orders').get().n===0,'missing PDF blocks checkout before creating an order');
  available=true;
  r=await call('POST','/checkout',{product:slug,email:'buyer@example.test'});
  check(r.response.status===201,'guest checkout can buy the available PDF');
  const target=new URL((await r.data()).url,'https://fixture.test'),ref=target.pathname.split('/').at(-1),key=target.searchParams.get('key');
  const orderPath=`/orders/${ref}`, access=`?key=${encodeURIComponent(key)}`;
  check((await call('GET',orderPath+'/download'+access)).response.status===402,'unpaid orders cannot download');
  r=await call('POST',orderPath+'/test-pay'+access,{});
  const paid=(await r.data()).order;
  check(r.response.status===200 && paid.status==='paid' && paid.downloadUrl,'confirmed payment exposes download immediately');
  check(paid.emailDelivery==='queued','purchase queues a transactional download email without marketing consent');
  await call('POST',orderPath+'/test-pay'+access,{});
  await call('GET',orderPath+access);
  check(sqlite.prepare('SELECT COUNT(*) n FROM outbox WHERE dedupe_key IS NOT NULL').get().n===1,'payment retries and receipt refreshes cannot duplicate delivery');
  r=await call('GET',orderPath+'/download'+access);
  check(r.response.status===200 && (await r.response.text()).startsWith('%PDF'),'guest receives PDF bytes without an account');
  check((await call('GET',orderPath+'/download?key=wrong')).response.status===404,'incorrect receipt key cannot access purchase');
  check((await call('GET',orderPath+'/download')).response.status===404,'guessing an order reference does not grant access');
  const receipt=sqlite.prepare('SELECT text FROM outbox WHERE dedupe_key IS NOT NULL').get().text;
  const emailed=receipt.match(/https:\/\/fixture\.test\/api\/orders\/[^\s]+/)[0];
  check((await call('GET',emailed.replace('https://fixture.test/api',''))).response.status===200,'emailed signed link works independently of original checkout key');
  r=await call('POST','/signup',{email:'buyer@example.test',password:'fixture-password-123',displayName:'Fixture buyer'});
  check(r.response.status===201,'buyer can create an account after paying');
  const cookie=r.response.headers.get('set-cookie').split(';')[0];
  r=await call('GET','/me/orders',undefined,cookie);
  check((await r.data()).orders.length===0,'unverified email alone cannot take a guest purchase');
  r=await call('POST',orderPath+'/claim'+access,{},cookie);
  check(r.response.status===200 && (await r.data()).order.owned,'receipt possession attaches the guest order after signup');
  r=await call('GET','/me/orders',undefined,cookie);
  const library=(await r.data()).orders;
  check(library.length===1 && library[0].downloadUrl===orderPath.replace('/orders/','/api/orders/')+'/download','My books shows the owned purchase without storing a receipt secret in the URL');
  check((await call('GET',orderPath+'/download',undefined,cookie)).response.status===200,'account owner can re-download without email link');
  check((await (await call('GET','/me/standing',undefined,cookie)).data()).checks.ownsTheBook,'children book purchase counts as owning a book');
  r=await call('POST','/signup',{email:'other@example.test',password:'fixture-password-456',displayName:'Other fixture'});
  const other=r.response.headers.get('set-cookie').split(';')[0];
  check((await call('GET',orderPath,undefined,other)).response.status===404,'another account cannot view the receipt');
  check((await call('POST',orderPath+'/claim'+access,{},other)).response.status===409,'even a shared receipt cannot reassign an already claimed purchase');
  sqlite.prepare("UPDATE orders SET status='refunded' WHERE ref=?").run(ref);
  check((await call('GET',orderPath+'/download',undefined,cookie)).response.status===402,'refunded purchase loses download entitlement');
  sqlite.prepare("UPDATE orders SET status='paid' WHERE ref=?").run(ref);
  sqlite.prepare("UPDATE products SET status='preorder' WHERE slug=?").run(slug);
  check((await call('GET',orderPath+'/download'+access)).response.status===409,'an unreleased edition cannot be downloaded by bypassing the receipt UI');
  sqlite.prepare("UPDATE products SET status='live' WHERE slug=?").run(slug);
  // Create a separate guest order to exercise verified-email recovery.
  r=await call('POST','/checkout',{product:slug,email:'buyer@example.test'});
  const secondUrl=new URL((await r.data()).url,'https://fixture.test'),second=secondUrl.pathname.split('/').at(-1);
  await call('POST',`/orders/${second}/test-pay?key=${secondUrl.searchParams.get('key')}`,{});
  sqlite.prepare("UPDATE users SET email_verified_at=datetime('now') WHERE email='buyer@example.test'").run();
  r=await call('GET','/me/orders',undefined,cookie);
  check((await r.data()).orders.length===2,'verified-email recovery links earlier guest orders to My books');
  check(sqlite.prepare('SELECT COUNT(*) n FROM outbox WHERE dedupe_key IS NOT NULL').get().n===2,'one delivery per explicitly processed order; no bulk historical send');
  // Exercise the real webhook path, including duplicate Stripe notifications.
  sqlite.prepare("UPDATE orders SET status='pending',provider='stripe' WHERE ref=?").run(second);
  const raw=JSON.stringify({type:'checkout.session.completed',data:{object:{metadata:{ref:second},payment_status:'paid',customer_details:{email:'buyer@example.test'}}}});
  const timestamp=Math.floor(Date.now()/1000),signature=await hmacHex(env.STRIPE_WEBHOOK_SECRET,`${timestamp}.${raw}`);
  const header={'stripe-signature':`t=${timestamp},v1=${signature}`};
  check((await call('POST','/stripe/webhook',raw,'',header)).response.status===200,'verified Stripe webhook completes a real route payment');
  await call('POST','/stripe/webhook',raw,'',header);
  check(sqlite.prepare('SELECT COUNT(*) n FROM outbox WHERE dedupe_key IS NOT NULL').get().n===2,'duplicate Stripe webhook does not send another book email');
  check((await call('POST','/stripe/webhook',raw,'',{'stripe-signature':'invalid'})).response.status===400,'unverified webhook cannot confirm payment');
  console.log(`RESULT: ${checks} checks passed`);
} finally {
  sqlite.close();
  await rm(temp,{recursive:true,force:true});
}
