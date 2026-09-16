from pathlib import Path
import sys,json,wave,math,re,subprocess,concurrent.futures,textwrap
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'output'
sys.path.insert(0,str(ROOT/'vendor'))
import imageio_ffmpeg
from mp4info import tracks
FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
SCENES=json.loads((ROOT/'scenes.json').read_text(encoding='utf-8'))
FPS=24
DELAY=.6
TAIL=.9
RATE=16000
def run(args):
    result=subprocess.run([FFMPEG,'-hide_banner','-loglevel','error','-y',*args],capture_output=True,text=True)
    if result.returncode: raise RuntimeError(result.stderr[-5000:])
    return result
def stamp(t,sep=','):
    ms=round(t*1000); h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02}{sep}{ms:03}'
timeline=[]
start=0
for i,s in enumerate(SCENES):
    a=ROOT/'audio-local'/f'{i+1:02}.wav'
    with wave.open(str(a)) as w:
        speech=w.getnframes()/w.getframerate()
    duration=math.ceil((speech+DELAY+TAIL)*FPS)/FPS
    existing=ROOT/'clips'/f'{i+1:02}.mp4'
    if existing.exists():
        prior=next(x['duration'] for x in tracks(existing) if x['type']=='vide')
        if prior>=speech+DELAY+.5:duration=prior
    timeline.append(dict(index=i+1,start=start,duration=duration,speech=speech,title=s['title'].replace('\n',' ')))
    start+=duration
(ROOT/'timeline.json').write_text(json.dumps(timeline,indent=2),encoding='utf-8')

# Write exact word-event captions, grouped into readable phrases.
subs=[]
for s,t in zip(SCENES,timeline):
    words=json.loads((ROOT/'audio-local'/f'{t["index"]:02}.json').read_text(encoding='utf-8-sig'))
    assert words[-1]['start'] < t['speech'], (t,words[-1])
    j=0
    while j<len(words):
        k=j+1
        while k<len(words):
            phrase=s['narration'][words[j]['position']:words[k]['position']].strip()
            if len(phrase)>=75 or words[k]['start']-words[j]['start']>=5 or re.search(r'[.!?]$',phrase):break
            k+=1
        endpos=words[k]['position'] if k<len(words) else len(s['narration'])
        phrase=s['narration'][words[j]['position']:endpos].strip()
        a=t['start']+DELAY+words[j]['start']
        b=t['start']+DELAY+(words[k]['start'] if k<len(words) else t['speech'])
        subs.append((a,b,textwrap.fill(phrase,width=46)))
        assert b>a,(a,b,phrase)
        j=k
srt='\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n{txt}' for i,(a,b,txt) in enumerate(subs))+'\n'
(OUT/'The-many-values-of-one-tree.srt').write_text(srt,encoding='utf-8')
vtt='WEBVTT\n\n'+'\n\n'.join(f'{stamp(a,".")} --> {stamp(b,".")}\n{txt}' for a,b,txt in subs)+'\n'
(OUT/'The-many-values-of-one-tree.vtt').write_text(vtt,encoding='utf-8')

# Preserve the complete spoken script, visual cues, and source notes.
md=['# The many values of one tree','',f'Complete narration script. General audience. Runtime {stamp(start,".").split(".")[0]}.','',
    'Narration: Microsoft Zira Desktop, generated locally. The visuals use the supplied economic model and existing DomeSim illustrations. The opening woodland is a generated conceptual image.','',
    'The $4,800 shell framing value and the tree yield are project assumptions, not established quotes or measured construction results. Nominal financed payments and present-day replacement costs are separate measures.','']
for s,t in zip(SCENES,timeline):
    md.extend([f'## {t["index"]:02}. {t["title"]}',f'**{stamp(t["start"],".").split(".")[0]}**','',s['narration'],'','**On screen**',''])
    if isinstance(s['body'][0],list):
        md.extend(['- '+' — '.join(row) for row in s['body']])
    else:md.extend(['- '+v.replace('\n',' ') for v in s['body']])
    if s['note']:md.extend(['',s['note']])
    md.extend([''])
(OUT/'Full-presentation-script.md').write_text('\n'.join(md),encoding='utf-8')
sources=['# Sources and model assumptions','',
 'The supplied essay is the primary source for the dome economic model. External references below corroborate selected market and forestry concepts. Prices are dated comparisons and vary by locality, species and service.','',
 '## External references','',
 '- [TimberMart-South, Q2 2026 bulletin](https://timbermart-south.com/wp-content/uploads/2026/07/2Q2026_bulletin.pdf): $23.34/ton South-wide pine sawtimber and $5.40/ton pine pulpwood. Published July 7, 2026.',
 '- [Alabama Q4 2025 price discussion](https://thetimberlandinvestor.com/alabama-stumpage-timber-prices/): secondary corroboration of the essay’s approximate $17–$21/ton Alabama range.',
 '- [North River Firewood price list](https://north-river-firewood.ueniweb.com/price-list): $275 full-cord pickup and $300 delivered listing, with delivery and stacking terms. This listing does not establish an equivalent pine-species price.',
 '- [Penn State Extension, Valuing Standing Timber](https://extension.psu.edu/valuing-standing-timber): cord measurement and variability in solid volume, with 65–90 cubic feet described.',
 '- [Oklahoma State Extension, Measuring Woodland Timber](https://extension.okstate.edu/fact-sheets/measuring-woodland-timber): example use of a 90-cubic-foot cord conversion.',
 '- [USDA Forest Products Laboratory, Research Paper 285](https://www.fpl.fs.usda.gov/documnts/fplrp/fplrp285.pdf): historical recovery discussion supporting an average near 7.5 BF/ft³. It does not independently establish the essay’s full 7.5–8.4 southern-pine range.',
 '- [Fireside Sawmill lumber prices](https://potato-pepper-ggcl.squarespace.com/lumberprices): example common 1x pine listing at $1.50/BF. Grade, geography and drying differ.','',
 '## Inputs preserved from the supplied essay','',
 'The representative 15-inch tree, 60 useful feet, 37 ft³ solid volume, 0.35–0.45 cord, 0.35 and 0.47 cord yield-table examples, $1.20/BF lower price, broader Southeast firewood range, wedge replacement value, 120-member requirement, $4,800 gross framing substitution, upper $3,200 per-tree case, labor hours and direct costs remain supplied scenario inputs. No measured yield record, engineering validation, bill of materials, or equivalent contractor quote was provided with this request.',
 '', 'The essay attributes the 90 ft³ cord conversion to Alabama Extension. That exact attribution and its tree-yield table were not independently located, so the video presents them as working conversions and source inputs.',
 '', '## Calculations and interpretations','',
 '- 37 × 7.5 = 277.5 BF, coarsely rounded to 275 to preserve the source example. At $1.20–$1.50/BF, 275 BF gives $330–$412.50. The broader ladder rounds that to $330–$415.',
 '- 8 × 60 ÷ 6 = 80 theoretical blanks per tree. Two trees give 160, before actual losses and acceptance. 160 − 120 = 40 potential pieces.',
 '- A $4,800 principal, 6.5% fixed annual rate, monthly payments and 360 months give $30.339265/month and $10,922.135446 total nominal principal and interest. The total already contains the $4,800 principal. No loan fees, taxes or insurance are included.',
 '- $4,800 ÷ $250 = 19.2. $4,800 ÷ $50 = 96. $4,800 ÷ 80 hours = $60/hour gross, before costs.',
 '- $2,400 − $300 − 40 × $25 = $1,100 net use value before the forgone raw-tree sale. Compared with a $25 sale alternative, the advantage is $1,075.',
 '', '## Visual and narration credits','',
 'Dome, jig and shell imagery comes from existing DomeSim project illustrations. The radial wedge illustration is a crop of the existing Why Wedges video still, preserving the member itself. These are concept renders, not photographs of completed construction.',
 '', 'Forest background: generated with the built-in ImageGen tool and saved in build/forest.png. The full generation prompt is in build/forest-prompt.txt. Microsoft Zira Desktop provided local synthetic narration. Subtitle timing comes from local speech-engine word events.','']
(OUT/'Sources-and-assumptions.md').write_text('\n'.join(sources),encoding='utf-8')

# Each scene is encoded with a short dissolve through black. Narration begins after the fade.
clips=ROOT/'clips';clips.mkdir(exist_ok=True)
def encode(t):
    n=t['index'];d=t['duration'];dest=clips/f'{n:02}.mp4'
    if dest.exists() and dest.stat().st_size>1000 and dest.stat().st_mtime>(ROOT/'slides'/f'{n:02}.png').stat().st_mtime:return
    run(['-loop','1','-framerate',str(FPS),'-i',str(ROOT/'slides'/f'{n:02}.png'),'-t',f'{d:.6f}',
         '-vf',f'fade=t=in:st=0:d=0.35,fade=t=out:st={d-.35:.6f}:d=0.35,format=yuv420p',
         '-c:v','libx264','-preset','veryfast','-tune','stillimage','-crf','21','-threads','2','-an',str(dest)])
    print(f'Encoded scene {n:02}/26',flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(encode,timeline))

# Assemble a continuous PCM track on the same scene timeline, avoiding AAC padding at joins.
combined=ROOT/'narration.wav'
with wave.open(str(combined),'wb') as out:
    out.setnchannels(1);out.setsampwidth(2);out.setframerate(RATE)
    written=0
    for t in timeline:
        goal=round((t['start']+DELAY)*RATE)
        out.writeframes(b'\0\0'*(goal-written));written=goal
        with wave.open(str(ROOT/'audio-local'/f'{t["index"]:02}.wav'),'rb') as w:
            pcm=w.readframes(w.getnframes());out.writeframes(pcm);written+=len(pcm)//2
    out.writeframes(b'\0\0'*(round(start*RATE)-written))
concat=ROOT/'clips.txt'
concat.write_text('\n'.join(f"file 'clips/{t['index']:02}.mp4'" for t in timeline),encoding='utf-8')
meta=[';FFMETADATA1','title=The many values of one tree','comment=General-audience presentation. Local synthetic narration. Source-model assumptions explained in script.']
for t in timeline:
    meta.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(t["start"]*1000)}',f'END={round((t["start"]+t["duration"])*1000)}','title='+t['title']])
(ROOT/'chapters.ffmeta').write_text('\n'.join(meta)+'\n',encoding='utf-8')
run(['-f','concat','-safe','0','-i',str(concat),'-i',str(combined),'-i',str(OUT/'The-many-values-of-one-tree.srt'),'-i',str(ROOT/'chapters.ffmeta'),
     '-map','0:v','-map','1:a','-map','2:s','-map_metadata','3','-map_chapters','3','-c:v','copy','-c:a','aac','-b:a','128k','-ar','44100',
     '-af','loudnorm=I=-18:TP=-1.5:LRA=9','-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata:s:a:0','language=eng',
     '-movflags','+faststart','-t',str(start),str(OUT/'The-many-values-of-one-tree.mp4')])
print(f'Finished {start:.2f} seconds, {len(subs)} subtitle cues',flush=True)
