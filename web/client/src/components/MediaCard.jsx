// A video or post that only loads the platform's player when it is clicked.
// Until then it is a picture and a button: faster, and nobody's tracker runs
// for a visitor who never pressed play.

import { useState } from 'react';
import Icon from './Icon.jsx';

const PLATFORM = { youtube: 'YouTube', tiktok: 'TikTok', instagram: 'Instagram' };

export default function MediaCard({ item }) {
  const [live, setLive] = useState(false);
  const tall = item.platform !== 'youtube' || item.kind === 'short';
  return (
    <figure className={`media ${tall ? 'tall' : 'wide'} ${item.platform}`}>
      <div className="frame">
        {live ? (
          <iframe
            src={`${item.embedUrl}${item.platform === 'youtube' ? '&autoplay=1' : ''}`}
            title={item.title || PLATFORM[item.platform]}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            loading="lazy"
          />
        ) : (
          <button className="poster" onClick={() => setLive(true)} aria-label={`Play ${item.title || PLATFORM[item.platform]}`}>
            {item.thumbnail ? <img src={item.thumbnail} alt="" loading="lazy" /> : <span className="poster-blank"><Icon name={item.platform} size={48} /></span>}
            <span className="play"><Icon name="play" size={28} /></span>
          </button>
        )}
      </div>
      <figcaption>
        <Icon name={item.platform} size={16} /> {item.title || PLATFORM[item.platform]}
        {' · '}
        <a href={item.url} target="_blank" rel="noreferrer">open on {PLATFORM[item.platform]}</a>
      </figcaption>
    </figure>
  );
}
