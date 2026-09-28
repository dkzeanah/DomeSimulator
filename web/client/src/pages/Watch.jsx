import { useEffect, useState } from 'react';
import { api } from '../api.js';
import MediaCard from '../components/MediaCard.jsx';

const TABS = [
  ['all', 'Everything'],
  ['youtube', 'YouTube'],
  ['tiktok', 'TikTok'],
  ['instagram', 'Instagram'],
];

export default function Watch() {
  const [tab, setTab] = useState('all');
  const [items, setItems] = useState(null);
  const [latest, setLatest] = useState([]);

  useEffect(() => {
    api('/media/youtube-latest').then((d) => setLatest(d.media)).catch(() => {});
  }, []);

  useEffect(() => {
    setItems(null);
    api('/media', { query: { platform: tab === 'all' ? '' : tab } })
      .then((d) => setItems(d.media))
      .catch(() => setItems([]));
  }, [tab]);

  // Channel uploads not already pinned on the wall.
  const pinned = new Set((items || []).filter((i) => i.platform === 'youtube').map((i) => i.embedId));
  const fromChannel = tab === 'all' || tab === 'youtube' ? latest.filter((v) => !pinned.has(v.embedId)) : [];

  return (
    <section>
      <h1>Watch</h1>
      <p className="lead">The films, the shorts and the build posts, in one place. Nothing loads from a platform until you press play.</p>
      <div className="tabs" role="tablist">
        {TABS.map(([key, label]) => (
          <button key={key} role="tab" aria-selected={tab === key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>
      {items === null && <p className="muted">Loading…</p>}
      {items && items.length === 0 && fromChannel.length === 0 && (
        <p className="muted">Nothing here yet. An admin adds videos and posts by pasting their links on the Admin page.</p>
      )}
      <div className="media-grid">
        {items?.map((item) => <MediaCard key={`m${item.id}`} item={item} />)}
        {fromChannel.map((item) => <MediaCard key={`y${item.embedId}`} item={item} />)}
      </div>
    </section>
  );
}
