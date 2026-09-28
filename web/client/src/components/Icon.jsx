// Small line icons, drawn here rather than loaded from a third party.
// They are generic glyphs, not the platforms' trademarked logos.

const PATHS = {
  link: 'M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1',
  youtube: 'M3 7.5C3 6 4 5 5.5 5h13C20 5 21 6 21 7.5v9c0 1.5-1 2.5-2.5 2.5h-13C4 19 3 18 3 16.5zM10 9v6l5-3z',
  tiktok: 'M14 4v10.5a3.5 3.5 0 1 1-3.5-3.5M14 4c.5 2.5 2.5 4 5 4',
  instagram: 'M7 3h10a4 4 0 0 1 4 4v10a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4zM12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zM17.5 6.5h0',
  facebook: 'M14 21v-8h3l.5-3.5H14V7.5c0-1 .5-1.5 1.5-1.5H18V3h-3c-2.5 0-4 1.5-4 4v2.5H8V13h3v8',
  x: 'M4 4l16 16M20 4L4 20',
  kickstarter: 'M8 4v16M8 13l8-9M11 10l6 10',
  book: 'M4 5c3-1 6-1 8 1 2-2 5-2 8-1v14c-3-1-6-1-8 1-2-2-5-2-8-1zM12 6v14',
  email: 'M3 6h18v12H3zM3 6l9 7 9-7',
  website: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18',
  patreon: 'M15 4a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM4 4v16',
  discord: 'M6 7c4-2 8-2 12 0l2 9c-2 2-4 3-6 3l-1-2M6 7L4 16c2 2 4 3 6 3l1-2M9 12h0M15 12h0',
  github: 'M9 19c-4 1-4-2-6-2M15 21v-3.5c0-1 .1-1.5-.5-2 3-.3 5.5-1.5 5.5-6a4.5 4.5 0 0 0-1.3-3.2 4 4 0 0 0-.1-3.2s-1-.3-3.4 1.3a11.5 11.5 0 0 0-6 0C6.8 2.8 5.8 3.1 5.8 3.1a4 4 0 0 0-.1 3.2A4.5 4.5 0 0 0 4.4 9.5c0 4.5 2.5 5.7 5.5 6-.6.5-.6 1.1-.6 2V21',
  threads: 'M16 9c-1-2-2.5-3-4.5-3C8 6 6 8.5 6 12s2 6 5.5 6c3 0 5-2 5-4.5S14 10 11.5 10 9 11.5 9.5 13s3 1.5 4-.5',
  pinterest: 'M12 3a9 9 0 0 0-3 17.5M10 21l2.5-10M12 8a3 3 0 0 1 3 3c0 3-2 5-3.5 4',
  pin: 'M12 21s-7-6.5-7-11a7 7 0 0 1 14 0c0 4.5-7 11-7 11zM12 7.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z',
  play: 'M8 5v14l11-7z',
};

export default function Icon({ name, size = 20, className = '' }) {
  return (
    <svg
      className={`icon ${className}`}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name] || PATHS.link} />
    </svg>
  );
}
