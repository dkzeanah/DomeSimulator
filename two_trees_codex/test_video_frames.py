import tempfile
from pathlib import Path
import unittest

from .video_frames import nearby_subtitles, seconds, subtitles


class ExistingVideoFrameTests(unittest.TestCase):
    def test_srt_times_and_multiline_caption(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'film.srt'
            path.write_text('1\n00:01:02,250 --> 00:01:05,500\nA wedge\nbecomes a strut.\n\n2\n00:02:00,000 --> 00:02:02,000\nThe dome.\n', encoding='utf-8')
            cues = subtitles(path)
            self.assertEqual(cues[0], {'start': 62.25, 'end': 65.5, 'text': 'A wedge becomes a strut.'})
            self.assertEqual(nearby_subtitles(cues, 64, window=3), cues[:1])

    def test_invalid_timestamp_is_not_accepted(self):
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                seconds(value)
        self.assertEqual(seconds('00:02:03.5'), 123.5)


if __name__ == '__main__':
    unittest.main()
