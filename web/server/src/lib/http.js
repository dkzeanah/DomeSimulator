// Small helpers shared by the routes.

import { z } from 'zod';

/** Wrap an async handler so a thrown error reaches the error middleware. */
export const route = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

/** Parse with a zod schema; a bad request becomes a 400 with a readable message. */
export function parse(schema, data) {
  const result = schema.safeParse(data);
  if (!result.success) {
    const issue = result.error.issues[0];
    const field = issue.path.join('.') || 'input';
    const error = new Error(`${field}: ${issue.message}`);
    error.status = 400;
    throw error;
  }
  return result.data;
}

export function httpError(status, message) {
  const error = new Error(message);
  error.status = status;
  return error;
}

// Optional text fields arrive as '' from forms; store them as null.
export const optionalText = (max) =>
  z
    .string()
    .trim()
    .max(max)
    .optional()
    .nullable()
    .transform((v) => (v ? v : null));

export const httpUrl = z
  .string()
  .trim()
  .max(500)
  .refine((v) => {
    try {
      return ['http:', 'https:', 'mailto:'].includes(new URL(v).protocol);
    } catch {
      return false;
    }
  }, 'must be a full web address starting with https://');

export const bool = (v) => v === true || v === 1 || v === '1' || v === 'true';
