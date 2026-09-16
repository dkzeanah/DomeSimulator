"""Extract reproducible, full-frame book figures from existing project films.

The source movie is the rendering authority: no movie, subtitle, or shared
renderer is rewritten. Each run has its own directory and source fingerprints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import uuid

from .publication import _ffmpeg
from .storage import stamp


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def seconds(value):
    """Accept nonnegative seconds or an SRT/HH:MM:SS clock."""
    if isinstance(value, str) and ':' in value:
        clock = value.strip().replace(',', '.').split(':')
        if len(clock) != 3:
            raise ValueError('A clock must have hours, minutes, and seconds.')
        value = float(clock[0]) * 3600 + float(clock[1]) * 60 + float(clock[2])
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Frame timestamp must be finite and nonnegative.')
    return result


def subtitles(path):
    path = Path(path)
    if not path.is_file():
        return []
    text = path.read_text(encoding='utf-8-sig')
    cues = []
    for block in re.split(r'\r?\n\s*\r?\n', text.strip()):
        lines = block.splitlines()
        timing = next((i for i, line in enumerate(lines) if '-->' in line), None)
        if timing is None:
            continue
        left, right = lines[timing].split('-->', 1)
        start, end = seconds(left.strip()), seconds(right.strip().split()[0])
        cues.append({'start': start, 'end': end, 'text': ' '.join(lines[timing + 1:])})
    return cues


def nearby_subtitles(cues, timestamp, window=8):
    return [cue for cue in cues if cue['start'] <= timestamp + window and cue['end'] >= timestamp - window]


def contact_sheet(results, path, columns=3, thumb_size=(640, 360)):
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    import textwrap
    label_height = 78
    width, height = thumb_size
    rows = math.ceil(len(results) / columns)
    sheet = Image.new('RGB', (columns * width, rows * (height + label_height)), '#fffdf5')
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    except OSError:
        font = ImageFont.load_default()
    for i, result in enumerate(results):
        x, y = (i % columns) * width, (i // columns) * (height + label_height)
        with Image.open(result['path']) as frame:
            thumb = ImageOps.contain(frame.convert('RGB'), thumb_size)
            sheet.paste(thumb, (x + (width - thumb.width) // 2, y + (height - thumb.height) // 2))
        label = f"{i + 1:02d}. {result['caption']}"
        for j, line in enumerate(textwrap.wrap(label, width=60)[:3]):
            draw.text((x + 12, y + height + 4 + 23*j), line, font=font, fill='#243f34')
    sheet.save(path)
    return str(path)


def extract_frames(plan, source_root, output_root, progress_callback=None):
    """Extract the plan's selections, recording portable, attachable recipes.

    ``plan`` is a list of source (relative MP4), timestamp, caption, purpose,
    and optional suggested_chapters records. Missing frames fail explicitly.
    """
    from PIL import Image
    source_root = Path(source_root).resolve()
    destination = Path(output_root).resolve() / ('video-' + stamp() + '-' + uuid.uuid4().hex[:8])
    destination.mkdir(parents=True, exist_ok=False)
    ffmpeg = str(_ffmpeg())
    fingerprints, cue_cache, results = {}, {}, []
    for index, selection in enumerate(plan, 1):
        source = (source_root / selection['source']).resolve()
        if source_root not in source.parents or source.suffix.lower() != '.mp4':
            raise ValueError('Source movie must be an MP4 within the selected project root.')
        if not source.is_file():
            raise FileNotFoundError(source)
        timestamp = seconds(selection['timestamp'])
        if progress_callback:
            progress_callback(f"Frame {index}/{len(plan)}: {source.name} at {timestamp:.3f}s")
        key = str(source)
        if key not in fingerprints:
            fingerprints[key] = sha256(source)
            cue_cache[key] = subtitles(source.with_suffix('.srt'))
        filename = f"{index:02d}-{source.stem}-{timestamp:010.3f}s.png"
        output = destination / filename
        command = [ffmpeg, '-nostdin', '-hide_banner', '-loglevel', 'error', '-n',
                   '-ss', f'{timestamp:.6f}', '-i', str(source), '-frames:v', '1',
                   '-update', '1', str(output)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        if result.returncode or not output.is_file():
            raise RuntimeError(f'Frame extraction failed for {source.name}: {result.stderr[-3000:]}')
        with Image.open(output) as frame:
            dimensions = list(frame.size)
            frame.verify()
        nearby = nearby_subtitles(cue_cache[key], timestamp)
        recipe = {'schema': 'two-trees-existing-video-frame/v1',
                  'source_video': source.relative_to(source_root).as_posix(),
                  'source_sha256': fingerprints[key], 'timestamp_seconds': timestamp,
                  'frame_selection': 'FFmpeg input seek with accurate decoding; first decoded frame at requested time',
                  'framing': 'Entire original frame; original presentation overlays retained',
                  'dimensions': dimensions, 'purpose': selection.get('purpose', '')}
        item = {'path': str(output), 'caption': selection['caption'],
                'provenance': f"Existing video-engine presentation: {source.stem.replace('-', ' ')} at {timestamp:.1f} s. Source-model example.",
                'recipe': recipe,
                'render_metadata': {'source_video': recipe['source_video'],
                                    'source_sha256': fingerprints[key],
                                    'nearby_subtitles': nearby,
                                    'subtitle_path': source.with_suffix('.srt').relative_to(source_root).as_posix() if source.with_suffix('.srt').is_file() else None,
                                    'subtitle_sha256': sha256(source.with_suffix('.srt')) if source.with_suffix('.srt').is_file() else None,
                                    'image_sha256': sha256(output),
                                    'source_values': 'Numbers and claims belong to the original presentation configuration; they are not new field measurements.'},
                'suggested_chapters': selection.get('suggested_chapters', []),
                'purpose': selection.get('purpose', '')}
        results.append(item)
        (destination / 'partial-manifest.json').write_text(json.dumps({'results': results}, indent=2), encoding='utf-8')
    sheets = []
    for start in range(0, len(results), 9):
        sheets.append(contact_sheet(results[start:start+9], destination / f'contact-sheet-{start//9+1:02d}.jpg'))
    manifest = {'schema': 'two-trees-existing-video-illustrations/v1', 'created': stamp(),
                'source_root': str(source_root), 'source_read_only': True,
                'results': results, 'contact_sheets': sheets,
                'count': len(results), 'manifest': str(destination / 'manifest.json')}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-root', type=Path, default=Path(__file__).parent / 'workspace/expanded-art')
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    result = extract_frames(plan, args.source_root, args.output_root, print)
    print(result['manifest'])


if __name__ == '__main__':
    main()
