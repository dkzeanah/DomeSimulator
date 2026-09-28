// The dome network: find pad hosts, dome owners, quilters, builders and
// people with trees near you, and list yourself.
//
// Privacy by default: search results show a location rounded to about a
// kilometre, and a listing's contact details are shown only to people who are
// signed in -- so the map is useful to members and useless to scrapers.

import { Router } from 'express';
import { z } from 'zod';
import { requireUser } from '../lib/auth.js';
import { boundingBox, haversineKm } from '../lib/geo.js';
import { httpError, optionalText, parse, route } from '../lib/http.js';
import { iso, nowIso } from '../db.js';

/** The kinds of member the campaign needs, in the campaign's own words. */
export const KINDS = [
  { key: 'pad_host', label: 'Pad host', blurb: 'Land with a serviced pad a dome can stand on -- built or planned.' },
  { key: 'dome_owner', label: 'Dome owner', blurb: 'Has a dome, is building one, or wants one and needs somewhere to put it.' },
  { key: 'quilter', label: 'Quilter', blurb: 'Sews insulating layers from recycled clothing, for their own dome or for hire.' },
  { key: 'builder', label: 'Builder', blurb: 'Splits, cuts, assembles or installs -- frames, panels, pads, services.' },
  { key: 'timber', label: 'Standing timber', blurb: 'Has trees that could become a frame, or a mill that could split them.' },
];
const KIND_KEYS = KINDS.map((k) => k.key);

const listingSchema = z.object({
  kind: z.enum(KIND_KEYS),
  title: z.string().trim().min(3, 'needs at least 3 characters').max(120),
  body: optionalText(4000),
  city: optionalText(100),
  region: optionalText(100),
  country: optionalText(100),
  postalCode: optionalText(20),
  lat: z.number().min(-90).max(90).nullable().optional(),
  lng: z.number().min(-180).max(180).nullable().optional(),
  contact: optionalText(300),
  visible: z.boolean().optional(),
});

const searchSchema = z.object({
  q: z.string().trim().max(100).optional(),
  kind: z.enum(KIND_KEYS).optional(),
  lat: z.coerce.number().min(-90).max(90).optional(),
  lng: z.coerce.number().min(-180).max(180).optional(),
  radiusKm: z.coerce.number().min(1).max(5000).optional().default(250),
  limit: z.coerce.number().int().min(1).max(100).optional().default(50),
  offset: z.coerce.number().int().min(0).optional().default(0),
});

const round = (v, places = 2) => (v === null || v === undefined ? null : Number(Number(v).toFixed(places)));

function toListing(row, { viewer, distanceKm } = {}) {
  const own = viewer && viewer.id === row.user_id;
  return {
    id: row.id,
    kind: row.kind,
    title: row.title,
    body: row.body || '',
    city: row.city || '',
    region: row.region || '',
    country: row.country || '',
    postalCode: own ? row.postal_code || '' : undefined,
    // Two decimal places is about a kilometre: enough to find, not to doorstep.
    lat: own ? row.lat : round(row.lat),
    lng: own ? row.lng : round(row.lng),
    contact: viewer ? row.contact || '' : null,
    contactHidden: !viewer && Boolean(row.contact),
    visible: Boolean(row.visible),
    owner: { id: row.user_id, displayName: row.display_name },
    mine: Boolean(own),
    distanceKm: distanceKm === undefined ? undefined : Math.round(distanceKm * 10) / 10,
    createdAt: iso(row.created_at),
    updatedAt: iso(row.updated_at),
  };
}

function columns(body) {
  const out = {};
  const map = { kind: 'kind', title: 'title', body: 'body', city: 'city', region: 'region', country: 'country', postalCode: 'postal_code', lat: 'lat', lng: 'lng', contact: 'contact', visible: 'visible' };
  for (const [key, column] of Object.entries(map)) if (body[key] !== undefined) out[column] = body[key];
  return out;
}

export function networkRoutes(db) {
  const router = Router();

  router.get('/kinds', (_req, res) => res.json({ kinds: KINDS }));

  router.get('/', route(async (req, res) => {
    const s = parse(searchSchema, req.query);
    const near = s.lat !== undefined && s.lng !== undefined;
    let query = db('listings')
      .join('users', 'users.id', 'listings.user_id')
      .where('listings.visible', true)
      .select('listings.*', 'users.display_name');
    if (s.kind) query = query.andWhere('listings.kind', s.kind);
    if (s.q) {
      const like = `%${s.q.toLowerCase().replace(/[%_\\]/g, (c) => `\\${c}`)}%`;
      query = query.andWhere((w) => {
        for (const column of ['listings.title', 'listings.body', 'listings.city', 'listings.region', 'listings.country', 'listings.postal_code']) {
          w.orWhereRaw(`LOWER(${column}) LIKE ? ESCAPE '\\'`, [like]);
        }
      });
    }
    if (near) {
      const box = boundingBox(s.lat, s.lng, s.radiusKm);
      query = query.whereBetween('listings.lat', [box.minLat, box.maxLat]);
      // A box that crosses the date line is two ranges.
      if (box.minLng < -180 || box.maxLng > 180) {
        query = query.andWhere((w) =>
          w.where('listings.lng', '>=', box.minLng < -180 ? box.minLng + 360 : box.minLng)
            .orWhere('listings.lng', '<=', box.maxLng > 180 ? box.maxLng - 360 : box.maxLng));
      } else {
        query = query.whereBetween('listings.lng', [box.minLng, box.maxLng]);
      }
      const rows = await query.limit(2000);
      const hits = rows
        .map((row) => ({ row, d: haversineKm(s.lat, s.lng, row.lat, row.lng) }))
        .filter((h) => h.d <= s.radiusKm)
        .sort((a, b) => a.d - b.d);
      return res.json({
        total: hits.length,
        results: hits.slice(s.offset, s.offset + s.limit).map((h) => toListing(h.row, { viewer: req.user, distanceKm: h.d })),
      });
    }
    const [{ count }] = await query.clone().clearSelect().count({ count: 'listings.id' });
    const rows = await query.orderBy('listings.updated_at', 'desc').limit(s.limit).offset(s.offset);
    res.json({ total: Number(count), results: rows.map((row) => toListing(row, { viewer: req.user })) });
  }));

  router.get('/mine', requireUser, route(async (req, res) => {
    const rows = await db('listings')
      .join('users', 'users.id', 'listings.user_id')
      .where('listings.user_id', req.user.id)
      .orderBy('listings.updated_at', 'desc')
      .select('listings.*', 'users.display_name');
    res.json({ results: rows.map((row) => toListing(row, { viewer: req.user })) });
  }));

  router.get('/:id', route(async (req, res) => {
    const row = await db('listings')
      .join('users', 'users.id', 'listings.user_id')
      .where('listings.id', Number(req.params.id))
      .first('listings.*', 'users.display_name');
    if (!row || (!row.visible && row.user_id !== req.user?.id)) throw httpError(404, 'No such listing.');
    res.json({ listing: toListing(row, { viewer: req.user }) });
  }));

  router.post('/', requireUser, route(async (req, res) => {
    const body = parse(listingSchema, req.body);
    const mine = await db('listings').where({ user_id: req.user.id }).count({ n: 'id' }).first();
    if (Number(mine.n) >= 20) throw httpError(400, 'Twenty listings is the limit per account.');
    const [row] = await db('listings')
      .insert({ ...columns(body), user_id: req.user.id, visible: body.visible ?? true, created_at: nowIso(), updated_at: nowIso() })
      .returning('id');
    const id = typeof row === 'object' ? row.id : row;
    const saved = await db('listings').join('users', 'users.id', 'listings.user_id').where('listings.id', id).first('listings.*', 'users.display_name');
    res.status(201).json({ listing: toListing(saved, { viewer: req.user }) });
  }));

  router.patch('/:id', requireUser, route(async (req, res) => {
    const id = Number(req.params.id);
    const row = await db('listings').where({ id }).first();
    if (!row) throw httpError(404, 'No such listing.');
    if (row.user_id !== req.user.id && req.user.role !== 'admin') throw httpError(403, 'That listing is not yours.');
    const body = parse(listingSchema.partial(), req.body);
    await db('listings').where({ id }).update({ ...columns(body), updated_at: nowIso() });
    const saved = await db('listings').join('users', 'users.id', 'listings.user_id').where('listings.id', id).first('listings.*', 'users.display_name');
    res.json({ listing: toListing(saved, { viewer: req.user }) });
  }));

  router.delete('/:id', requireUser, route(async (req, res) => {
    const id = Number(req.params.id);
    const row = await db('listings').where({ id }).first();
    if (!row) throw httpError(404, 'No such listing.');
    if (row.user_id !== req.user.id && req.user.role !== 'admin') throw httpError(403, 'That listing is not yours.');
    await db('listings').where({ id }).delete();
    res.json({ ok: true });
  }));

  return router;
}

