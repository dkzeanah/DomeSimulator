// The link-in-bio page: open it from Instagram or TikTok. It stands alone,
// with no site header, because that is what people expect from one.

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useSession } from '../App.jsx';
import Icon from '../components/Icon.jsx';

export default function Links() {
  const { site } = useSession();
  const [links, setLinks] = useState(null);
  useEffect(() => {
    api('/links').then((d) => setLinks(d.links)).catch(() => setLinks([]));
  }, []);

  return (
    <div className="links-page">
      <img className="avatar" src={site?.avatar || '/mark.svg'} alt="" width="96" height="96" />
      <h1>{site?.name}</h1>
      {site?.tagline && <p className="tagline">{site.tagline}</p>}
      <ul className="link-list">
        {site?.kickstarterUrl && (
          <li>
            <a className="link-button highlight" href={site.kickstarterUrl} target="_blank" rel="noreferrer">
              <Icon name="kickstarter" /> Back the stem-cell dome on Kickstarter
            </a>
          </li>
        )}
        <li>
          <Link className="link-button highlight" to="/book">
            <Icon name="book" /> Get the free book
          </Link>
        </li>
        <li>
          <Link className="link-button" to="/network">
            <Icon name="pin" /> Find the dome network
          </Link>
        </li>
        <li>
          <Link className="link-button" to="/watch">
            <Icon name="play" /> Watch the films
          </Link>
        </li>
        {links?.map((l) => (
          <li key={l.id}>
            <a className="link-button" href={l.url} target="_blank" rel="noreferrer">
              <Icon name={l.icon} /> {l.label}
            </a>
          </li>
        ))}
      </ul>
      <Link to="/" className="links-home">
        <img src="/mark.svg" alt="" width="20" height="20" /> {site?.name} home
      </Link>
    </div>
  );
}
