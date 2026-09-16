import sys, json, asyncio
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'vendor'))
import edge_tts

async def main():
    scenes=json.loads((ROOT/'scenes.json').read_text(encoding='utf-8'))
    directory=ROOT/'audio'
    directory.mkdir(exist_ok=True)
    sem=asyncio.Semaphore(2)
    async def one(i,s):
        async with sem:
            audio=directory/f'{i+1:02d}.mp3'
            bounds=audio.with_suffix('.json')
            if audio.exists() and bounds.exists():
                return
            for attempt in range(3):
                try:
                    timing=[]
                    c=edge_tts.Communicate(s['narration'],'en-US-AndrewMultilingualNeural',rate='-3%',pitch='-2Hz',boundary='WordBoundary')
                    with audio.open('wb') as out:
                        async for chunk in c.stream():
                            if chunk['type']=='audio': out.write(chunk['data'])
                            elif chunk['type']=='WordBoundary': timing.append(chunk)
                    if not timing or audio.stat().st_size<1000: raise RuntimeError('Empty narration')
                    bounds.write_text(json.dumps(timing),encoding='utf-8')
                    print(f'Voiced {i+1:02d}/{len(scenes)}: {len(timing)} words',flush=True)
                    return
                except Exception as e:
                    if attempt==2: raise
                    await asyncio.sleep(1)
    await asyncio.gather(*(one(i,s) for i,s in enumerate(scenes)))

asyncio.run(main())
