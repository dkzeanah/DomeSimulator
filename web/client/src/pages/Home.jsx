import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, money } from '../api.js';
import BookGate from '../components/BookGate.jsx';
import MediaCard from '../components/MediaCard.jsx';
import { TwoWays, Upsell } from '../components/Offers.jsx';
import { offered, useBooks, useFacts } from '../shop.js';

export default function Home() {
  const facts = useFacts();
  const { books } = useBooks();
  const [media, setMedia] = useState([]);

  useEffect(() => {
    api('/media').then((d) => setMedia(d.media.slice(0, 3))).catch(() => {});
  }, []);

  const sample = offered(books, 'free');
  const pages = facts?.books?.sample?.pages;
  const n = facts?.books?.paperback?.numbers;
  const dome = facts?.dome;
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Geodesic Dome Wedge Method</p>
          <h1>Frame a house from trees you split yourself.</h1>
          <p className="lead">
            A geodesic cabin whose frame is split from logs with a chainsaw -- no mill, no planer, no lumber yard. Every
            member is one of two lengths, every panel is built flat on one jig, and every number is computed, not
            guessed.
          </p>
          {n && (
            <ul className="stats">
              <li><b>{n.frameHours} h</b> of frame work</li>
              <li><b>{n.members}</b> split-log members</li>
              <li><b>{n.panels}</b> panels</li>
              <li><b>{n.floorSqft}</b> sq ft of floor</li>
              {facts.price && <li><b>{money(facts.price.stemCell)}</b> the stem cell</li>}
            </ul>
          )}
          <p className="row hero-links">
            <Link to="/buy" className="button ghost">The digital edition</Link>
            <Link to="/paperback" className="button ghost">The paperback</Link>
          </p>
        </div>
        <div className="hero-card">
          {sample ? (
            <>
              <p className="eyebrow">Free sample{pages ? ` · ${pages} pages` : ''}</p>
              {sample.cover && <img className="book-cover" src={sample.cover} alt={`Cover of ${sample.subtitle || sample.title}`} width="720" height="931" />}
              <h2>Read the opening chapters free</h2>
              <p className="muted">
                What has to be right, what you are allowed to get wrong, and the cut the whole method rests on -- exactly
                as the paperback prints them.
              </p>
              <BookGate book={sample} cta="Send me the free sample" after={<Upsell books={books} facts={facts} />} />
            </>
          ) : (
            <p className="muted">Loading the sample…</p>
          )}
        </div>
      </section>

      <TwoWays books={books} facts={facts} />

      <section className="tiles">
        <Link to="/dome" className="tile">
          <h3>How the dome works</h3>
          <p>
            {dome ? `${dome.acrossFt} ft across, ${dome.bays} bays. ` : ''}The price, what we keep, every fit-out and
            every reward tier -- straight from the model.
          </p>
        </Link>
        <Link to="/network" className="tile">
          <h3>Find the dome network</h3>
          <p>Pad hosts, dome owners, quilters, builders and people with trees, near you.</p>
        </Link>
        <Link to="/watch" className="tile">
          <h3>Watch the films</h3>
          <p>YouTube, TikTok and Instagram in one place.</p>
        </Link>
      </section>

      {media.length > 0 && (
        <section>
          <h2>Latest</h2>
          <div className="media-grid">
            {media.map((item) => <MediaCard key={item.id} item={item} />)}
          </div>
        </section>
      )}
    </>
  );
}
