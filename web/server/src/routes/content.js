// The public page content: the link-in-bio list, the media wall, the site
// profile and the dome's figures -- and the admin editing for the first two.

import fs from 'node:fs';
import { Router } from 'express';
import { z } from 'zod';
import { requireAdmin } from '../lib/auth.js';
import { httpError, httpUrl, optionalText, parse, route } from '../lib/http.js';
import { embedUrl, parseMediaUrl, thumbnailUrl } from '../lib/media.js';
import { latestUploads } from '../lib/youtube.js';
import { config, SERVER_ROOT } from '../config.js';
import { iso, nowIso } from '../db.js';
import path from 'node:path';

export const ICONS = ['link', 'youtube', 'tiktok', 'instagram', 'facebook', 'x', 'kickstarter', 'book', 'email', 'website', 'patreon', 'discord', 'github', 'threads', 'pinterest'];

const linkSchema = z.object({
  label: z.string().trim().min(1).max(80),
  url: httpUrl,
  icon: z.enum(ICONS).optional().default('link'),
  sort: z.number().int().optional(),
  visible: z.boolean().optional(),
});

const mediaSchema = z.object({
  url: z.string().trim().min(1).max(500),
  title: optionalText(200),
  featured: z.boolean().optional(),
  sort: z.number().int().optional(),
});

const toLink = (r) => ({ id: r.id, label: r.label, url: r.url, icon: r.icon, sort: r.sort, visible: Boolean(r.visible) });

const toMedia = (r) => ({
  id: r.id,
  platform: r.platform,
  kind: r.kind,
  url: r.url,
  embedId: r.embed_id,
  title: r.title || '',
  featured: Boolean(r.featured),
  sort: r.sort,
  embedUrl: embedUrl(r.platform, r.embed_id, r.kind),
  thumbnail: thumbnailUrl(r.platform, r.embed_id),
  createdAt: iso(r.created_at),
});

export function readSiteConfig() {
  if (!fs.existsSync(config.siteConfig)) return { name: 'Dome Network', tagline: '', links: [] };
  return JSON.parse(fs.readFileSync(config.siteConfig, 'utf8'));
}

/** First start only: copy the links from site.config.json into the database. */
export async function seedLinks(db) {
  const [{ n }] = await db('links').count({ n: 'id' });
  if (Number(n) > 0) return 0;
  const links = (readSiteConfig().links || []).filter((l) => l.label && l.url);
  if (links.length) {
    await db('links').insert(links.map((l, i) => ({
      label: l.label, url: l.url, icon: ICONS.includes(l.icon) ? l.icon : 'link', sort: i, visible: true, created_at: nowIso(),
    })));
  }
  return links.length;
}

export function contentRoutes(db) {
  const router = Router();

  router.get('/site', (_req, res) => {
    const site = readSiteConfig();
    res.json({
      name: site.name,
      tagline: site.tagline || '',
      avatar: site.avatar || '',
      kickstarterUrl: site.kickstarterUrl || '',
      youtubeChannelUrl: site.youtubeChannelUrl || '',
    });
  });

  // The stem cell's figures, exported from the Python model by export_facts.py.
  router.get('/facts', (_req, res) => {
    const file = path.join(SERVER_ROOT, 'src', 'generated', 'facts.json');
    if (!fs.existsSync(file)) return res.json({ facts: null });
    res.json({ facts: JSON.parse(fs.readFileSync(file, 'utf8')) });
  });

  // ---- links ---------------------------------------------------------

  router.get('/links', route(async (req, res) => {
    const all = req.user?.role === 'admin' && req.query.all === '1';
    let q = db('links').orderBy([{ column: 'sort' }, { column: 'id' }]);
    if (!all) q = q.where({ visible: true });
    res.json({ links: (await q).map(toLink) });
  }));

  router.post('/links', requireAdmin, route(async (req, res) => {
    const body = parse(linkSchema, req.body);
    const [{ max }] = await db('links').max({ max: 'sort' });
    const [row] = await db('links')
      .insert({ ...body, sort: body.sort ?? Number(max ?? -1) + 1, visible: body.visible ?? true, created_at: nowIso() })
      .returning('id');
    const id = typeof row === 'object' ? row.id : row;
    res.status(201).json({ link: toLink(await db('links').where({ id }).first()) });
  }));

  router.patch('/links/:id', requireAdmin, route(async (req, res) => {
    const id = Number(req.params.id);
    if (!(await db('links').where({ id }).first())) throw httpError(404, 'No such link.');
    await db('links').where({ id }).update(parse(linkSchema.partial(), req.body));
    res.json({ link: toLink(await db('links').where({ id }).first()) });
  }));

  router.delete('/links/:id', requireAdmin, route(async (req, res) => {
    await db('links').where({ id: Number(req.params.id) }).delete();
    res.json({ ok: true });
  }));

  // ---- media ---------------------------------------------------------

  router.get('/media', route(async (req, res) => {
    const platform = ['youtube', 'tiktok', 'instagram'].includes(req.query.platform) ? req.query.platform : null;
    let q = db('media_items').orderBy([{ column: 'featured', order: 'desc' }, { column: 'sort' }, { column: 'id', order: 'desc' }]);
    if (platform) q = q.where({ platform });
    res.json({ media: (await q.limit(200)).map(toMedia) });
  }));

  router.get('/media/youtube-latest', route(async (_req, res) => {
    const items = await latestUploads();
    res.json({
      channelConfigured: Boolean(config.youtubeChannelId),
      media: items.map((v) => ({
        platform: 'youtube',
        kind: v.short ? 'short' : 'video',
        embedId: v.embedId,
        title: v.title,
        publishedAt: v.publishedAt,
        embedUrl: embedUrl('youtube', v.embedId),
        thumbnail: thumbnailUrl('youtube', v.embedId),
        url: `https://www.youtube.com/watch?v=${v.embedId}`,
      })),
    });
  }));

  router.post('/media', requireAdmin, route(async (req, res) => {
    const body = parse(mediaSchema, req.body);
    const parsed = parseMediaUrl(body.url);
    if (!parsed) throw httpError(400, 'That does not look like a YouTube, TikTok or Instagram link. Paste the address of one video or post.');
    const exists = await db('media_items').where({ platform: parsed.platform, embed_id: parsed.embedId }).first('id');
    if (exists) throw httpError(409, 'That one is already on the wall.');
    const [row] = await db('media_items')
      .insert({
        platform: parsed.platform,
        embed_id: parsed.embedId,
        kind: parsed.kind,
        url: body.url,
        title: body.title,
        featured: body.featured ?? false,
        sort: body.sort ?? 0,
        created_at: nowIso(),
      })
      .returning('id');
    const id = typeof row === 'object' ? row.id : row;
    res.status(201).json({ media: toMedia(await db('media_items').where({ id }).first()) });
  }));

  router.patch('/media/:id', requireAdmin, route(async (req, res) => {
    const id = Number(req.params.id);
    if (!(await db('media_items').where({ id }).first())) throw httpError(404, 'No such item.');
    const body = parse(mediaSchema.omit({ url: true }).partial(), req.body);
    await db('media_items').where({ id }).update(body);
    res.json({ media: toMedia(await db('media_items').where({ id }).first()) });
  }));

  router.delete('/media/:id', requireAdmin, route(async (req, res) => {
    await db('media_items').where({ id: Number(req.params.id) }).delete();
    res.json({ ok: true });
  }));

  return router;
}
