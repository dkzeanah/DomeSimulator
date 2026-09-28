// Distance search that runs the same on SQLite and Postgres.
//
// The database narrows to a latitude/longitude box (an ordinary indexed range
// query); the exact great-circle distance is then computed here. For a network
// of thousands of listings this is plenty; PostGIS is the upgrade if it ever
// becomes millions.

const EARTH_KM = 6371.0088;
const rad = (deg) => (deg * Math.PI) / 180;

export function haversineKm(lat1, lng1, lat2, lng2) {
  const dLat = rad(lat2 - lat1);
  const dLng = rad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_KM * Math.asin(Math.min(1, Math.sqrt(a)));
}

/** A box that contains every point within radiusKm of (lat, lng). */
export function boundingBox(lat, lng, radiusKm) {
  const dLat = (radiusKm / EARTH_KM) * (180 / Math.PI);
  const cos = Math.cos(rad(lat));
  // Near the poles a longitude band stops meaning anything; take all of it.
  const dLng = cos < 1e-6 ? 180 : Math.min(180, dLat / cos);
  return {
    minLat: Math.max(-90, lat - dLat),
    maxLat: Math.min(90, lat + dLat),
    minLng: lng - dLng,
    maxLng: lng + dLng,
  };
}
