// Sign up, sign in, sign out, and the signed-in person's own profile.

import { Router } from 'express';
import bcrypt from 'bcryptjs';
import { z } from 'zod';
import {
  checkPassword,
  endSession,
  hashPassword,
  normaliseEmail,
  publicUser,
  requireUser,
  roleFor,
  startSession,
} from '../lib/auth.js';
import { httpError, optionalText, parse, route } from '../lib/http.js';
import { nowIso } from '../db.js';
import { upsertSubscriber } from './leads.js';

// Compared against when the email is unknown, so a wrong email takes as long
// as a wrong password and the response time does not reveal who has an account.
const DUMMY_HASH = bcrypt.hashSync('no-such-account', 12);

const password = z.string().min(10, 'must be at least 10 characters').max(200);

const signupSchema = z.object({
  email: z.email().max(320),
  password,
  displayName: z.string().trim().min(1, 'is required').max(80),
  marketingConsent: z.boolean().optional().default(false),
});

const loginSchema = z.object({ email: z.email(), password: z.string().min(1).max(200) });

const profileSchema = z.object({
  displayName: z.string().trim().min(1).max(80).optional(),
  bio: optionalText(2000),
  city: optionalText(100),
  region: optionalText(100),
  country: optionalText(100),
  website: optionalText(300),
  currentPassword: z.string().max(200).optional(),
  newPassword: password.optional(),
});

export function authRoutes(db) {
  const router = Router();

  router.post('/signup', route(async (req, res) => {
    const body = parse(signupSchema, req.body);
    const email = normaliseEmail(body.email);
    if (await db('users').where({ email }).first('id')) {
      throw httpError(409, 'That email already has an account. Sign in instead.');
    }
    const [row] = await db('users')
      .insert({
        email,
        password_hash: await hashPassword(body.password),
        display_name: body.displayName,
        role: roleFor(email),
        created_at: nowIso(),
        updated_at: nowIso(),
      })
      .returning('id');
    const id = typeof row === 'object' ? row.id : row;
    // Everyone with an account is on the list; consent decides whether they
    // hear from us about anything other than their account.
    await upsertSubscriber(db, { email, name: body.displayName, consent: body.marketingConsent, source: 'signup' });
    await startSession(db, res, id);
    res.status(201).json({ user: publicUser(await db('users').where({ id }).first()) });
  }));

  router.post('/login', route(async (req, res) => {
    const body = parse(loginSchema, req.body);
    const user = await db('users').where({ email: normaliseEmail(body.email) }).first();
    // Same message and roughly the same time whether the email exists or not.
    const ok = await checkPassword(body.password, user?.password_hash || DUMMY_HASH);
    if (!user || !ok) throw httpError(401, 'Email or password is not right.');
    await startSession(db, res, user.id);
    res.json({ user: publicUser(user) });
  }));

  router.post('/logout', route(async (req, res) => {
    await endSession(db, req, res);
    res.json({ ok: true });
  }));

  router.get('/me', (req, res) => res.json({ user: publicUser(req.user) }));

  router.patch('/me', requireUser, route(async (req, res) => {
    const body = parse(profileSchema, req.body);
    const update = { updated_at: nowIso() };
    if (body.displayName !== undefined) update.display_name = body.displayName;
    for (const key of ['bio', 'city', 'region', 'country', 'website']) {
      if (key in req.body) update[key] = body[key];
    }
    if (body.newPassword) {
      if (!body.currentPassword || !(await checkPassword(body.currentPassword, req.user.password_hash))) {
        throw httpError(400, 'Your current password is needed to set a new one.');
      }
      update.password_hash = await hashPassword(body.newPassword);
      // Changing the password signs every other device out.
      await db('sessions').where({ user_id: req.user.id }).delete();
      await startSession(db, res, req.user.id);
    }
    await db('users').where({ id: req.user.id }).update(update);
    res.json({ user: publicUser(await db('users').where({ id: req.user.id }).first()) });
  }));

  router.delete('/me', requireUser, route(async (req, res) => {
    const body = parse(z.object({ password: z.string().min(1) }), req.body);
    if (!(await checkPassword(body.password, req.user.password_hash))) {
      throw httpError(400, 'Password is not right.');
    }
    // Listings and sessions go with the account (ON DELETE CASCADE); the
    // email is also taken off the mailing list.
    await db('subscribers').where({ email: req.user.email }).update({ unsubscribed_at: nowIso(), marketing_consent: false });
    await db('users').where({ id: req.user.id }).delete();
    await endSession(db, req, res);
    res.json({ ok: true });
  }));

  return router;
}
