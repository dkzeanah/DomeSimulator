from pathlib import Path
import sys,json,subprocess,re,wave,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
import imageio_ffmpeg
ff=imageio_ffmpeg.get_ffmpeg_exe()
out=ROOT.parent/'output'
video=out/'The-many-values-of-one-tree.mp4'
timeline=json.loads((ROOT/'timeline.json').read_text())
expected=timeline[-1]['start']+timeline[-1]['duration']
meta=subprocess.run([ff,'-hide_banner','-i',str(video)],capture_output=True,text=True).stderr
assert '1920x1080' in meta and 'Video: h264' in meta and 'Audio: aac' in meta and 'Subtitle: mov_text' in meta,meta
assert meta.count('Chapter #')==26,meta
reader=imageio_ffmpeg.read_frames(str(video));props=next(reader);reader.close()
assert abs(props['duration']-expected)<.15,props
r=subprocess.run([ff,'-hide_banner','-loglevel','error','-i',str(video),'-map','0:v','-map','0:a','-f','null','-'],capture_output=True,text=True)
assert r.returncode==0 and not r.stderr.strip(),r.stderr
levels=[]
for t in timeline:
    with wave.open(str(ROOT/'audio-local'/f'{t["index"]:02}.wav')) as w:
        pcm=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
    peak=float(np.max(np.abs(pcm)));rms=float(np.sqrt(np.mean(pcm**2)))
    assert rms>.01 and peak<1,(t,peak,rms)
    marks=json.loads((ROOT/'audio-local'/f'{t["index"]:02}.json').read_text(encoding='utf-8-sig'))
    assert len(marks)>60 and all(a['start']<=b['start'] for a,b in zip(marks,marks[1:]))
    levels.append(dict(scene=t['index'],peak=peak,rms=rms))
for ix in [1,9,16,26]:
    t=timeline[ix-1]
    subprocess.run([ff,'-hide_banner','-loglevel','error','-y','-ss',str(t['start']+2),'-i',str(video),'-frames:v','1',str(ROOT/f'video-check-{ix:02}.png')],check=True)
report=dict(duration=props['duration'],expected_duration=expected,video_codec='h264',audio_codec='aac',resolution=[1920,1080],chapters=26,subtitle_codec='mov_text',decode_pass=True,bytes=video.stat().st_size,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),audio_levels=levels)
(ROOT/'video-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['audio_levels','sha256']}),flush=True)
