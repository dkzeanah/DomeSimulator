from pathlib import Path
import struct,json
def boxes(data,start=0,end=None):
    end=len(data) if end is None else end
    while start+8<=end:
        size,kind=struct.unpack('>I4s',data[start:start+8]);head=8
        if size==1:size=struct.unpack('>Q',data[start+8:start+16])[0];head=16
        if not size:size=end-start
        yield kind,start+head,start+size
        start+=size
def tracks(file):
    data=Path(file).read_bytes();res=[]
    for kind,a,b in boxes(data):
        if kind!=b'moov':continue
        for kind,a,b in boxes(data,a,b):
            if kind!=b'trak':continue
            d={}
            for kind,a,b in boxes(data,a,b):
                if kind!=b'mdia':continue
                for kind,a,b in boxes(data,a,b):
                    if kind==b'mdhd':
                        if data[a]==1:scale,dur=struct.unpack('>IQ',data[a+20:a+32])
                        else:scale,dur=struct.unpack('>II',data[a+12:a+20])
                        d['duration']=dur/scale
                    if kind==b'hdlr':d['type']=data[a+8:a+12].decode()
            res.append(d)
    return res
if __name__=='__main__':
    r=Path(__file__).parent;t=json.loads((r/'timeline.json').read_text())
    for x in t:
        actual=next(x for x in tracks(r/'clips'/f'{x["index"]:02}.mp4') if x['type']=='vide')['duration']
        print(x['index'],x['duration'],actual,round(actual-x['duration'],6))
    print(tracks(r.parent/'output'/'The-many-values-of-one-tree.mp4'))
