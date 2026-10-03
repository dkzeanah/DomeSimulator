// The Express app, built around a database handle so tests can hand it an
// in-memory one.

import fs from 'node:fs';
import path from 'node:path';
import cookieParser from 'cookie-parser';
import express from 'express';
import { rateLimit } from 'express-rate-limit';
import helmet from 'helmet';
import { config } from './config.js';
import { loadUser } from './lib/auth.js';
import { adminRoutes } from './routes/admin.js';
import { authRoutes } from './routes/auth.js';
import { contentRoutes } from './routes/content.js';
import { bookRoutes } from './routes/leads.js';
import { networkRoutes } from './routes/network.js';
import { storeRoutes, stripeWebhook } from './routes/store.js';

export function createApp(db, { rateLimits = true } = {}) {
  const app = express();
  app.set('trust proxy', 1); // behind Render/Railway/Fly's proxy, req.ip is the visitor's

  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          // The three platforms are embedded as iframes only; no third-party script runs.
          frameSrc: ['https://www.youtube-nocookie.com', 'https://www.youtube.com', 'https://www.tiktok.com', 'https://www.instagram.com'],
          imgSrc: ["'self'", 'data:', 'https://i.ytimg.com'],
          styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
          fontSrc: ["'self'", 'https://fonts.gstatic.com'],
          connectSrc: ["'self'"],
          scriptSrc: ["'self'"],
          objectSrc: ["'none'"],
          upgradeInsecureRequests: config.production ? [] : null,
        },
      },
      crossOriginEmbedderPolicy: false,
    }),
  );
  // Stripe signs the raw bytes, so its webhook reads them before any parser.
  app.post('/api/stripe/webhook', express.raw({ type: 'application/json', limit: '1mb' }), stripeWebhook(db));
  app.use(express.json({ limit: '64kb' }));
  app.use(cookieParser());

  // Every POST must be JSON. Browsers will not send application/json
  // cross-site without a CORS preflight this server never answers, which --
  // with the SameSite=Lax cookie -- is the CSRF defence. PATCH, PUT and
  // DELETE always need a preflight cross-site, so they may come bodiless.
  app.use('/api', (req, res, next) => {
    const hasBody = Number(req.headers['content-length'] || 0) > 0 || Boolean(req.headers['transfer-encoding']);
    if ((req.method === 'POST' || hasBody) && !req.is('application/json')) {
      return res.status(415).json({ error: 'Send JSON.' });
    }
    next();
  });

  if (rateLimits) {
    const limiter = (limit, minutes) =>
      rateLimit({ windowMs: minutes * 60 * 1000, limit, standardHeaders: 'draft-8', legacyHeaders: false, message: { error: 'Too many tries. Wait a few minutes and try again.' } });
    app.use('/api/auth/login', limiter(10, 15));
    app.use('/api/auth/signup', limiter(10, 60));
    app.use('/api/leads', limiter(20, 60));
    app.use('/api/waitlist', limiter(20, 60));
    app.use('/api/checkout', limiter(20, 60));
    app.use('/api', limiter(600, 15));
  }

  app.use(loadUser(db));

  app.get('/api/health', (_req, res) => res.json({ ok: true }));
  app.use('/api/auth', authRoutes(db));
  app.use('/api', bookRoutes(db));
  app.use('/api', storeRoutes(db));
  app.use('/api/network', networkRoutes(db));
  app.use('/api/admin', adminRoutes(db));
  app.use('/api', contentRoutes(db));
  app.use('/api', (_req, res) => res.status(404).json({ error: 'Not found.' }));

  // The built React app, with every non-API path falling through to it.
  if (fs.existsSync(config.clientDist)) {
    app.use(express.static(config.clientDist, { index: false, maxAge: '1h' }));
    app.get('/{*path}', (_req, res) => res.sendFile(path.join(config.clientDist, 'index.html')));
  }

  // eslint-disable-next-line no-unused-vars
  app.use((error, _req, res, _next) => {
    const status = error.status || error.statusCode || 500;
    if (status >= 500) console.error(error);
    res.status(status).json({ error: status >= 500 ? 'Something went wrong on our side.' : error.message });
  });

  return app;
}
