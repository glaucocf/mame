"""Measure native births including a slot retired/reused inside one frame."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,struct,zlib
BASE=Path(__file__).resolve().parents[1];ROOT=BASE/'captures/cadencia_armas_02'
def protocol(n):
    for name,lo,hi in [('segurado',31,390),('cada_2_quadros',511,870),('pulso_2_2',991,1350),('desvinculo',1471,1590),('saturacao',1621,2420)]:
        if lo<=n<=hi:return name
    return 'solto'
def analyze(folder):
    metadata=json.loads((folder/'metadata.json').read_text());raw=zlib.decompress((folder/'dma.zlib').read_bytes())
    assert len(raw)%4101==0
    births=defaultdict(list);peak=Counter();visible=Counter();previous={};first_tracks={};lives=[];tracking={};allrows=[]
    for at in range(0,len(raw),4101):
        n=struct.unpack_from('<I',raw,at)[0];a=raw[at+5:at+4101];kind=protocol(n);now={};shown=0
        for off in range(0x380,0x5c0,32):
            r=a[off:off+32]
            if r[8]!=2:
                if off in tracking:lives.append(tracking.pop(off))
                continue
            now[off]=r;before=previous.get(off)
            born=before is None or r[10]>before[10]+8
            if born:
                if off in tracking:lives.append(tracking.pop(off))
                shot=dict(frame=n,slot=f'{0xf000+off:04X}',code=r[0]+((r[1]&224)<<3),palette=r[1]&15,power=r[13],dx=r[2]-a[0x202],dy=(240-r[3])-(240-a[0x203]))
                births[kind].append(shot);tracking[off]=dict(protocol=kind,birth=n,slot=shot['slot'],points=[])
            if off in tracking:
                tracking[off]['points'].append([n,int(r[2]),240-(int(r[3])-((r[1]&16)<<4)),r[0]+((r[1]&224)<<3),r[1]&15,r[13],r[10]])
            sx=int(r[3])-((r[1]&16)<<4)
            if -16<sx<256 and 0<=r[2]<256:shown+=1
        peak[kind]=max(peak[kind],len(now));visible[kind]=max(visible[kind],shown);previous=now
    lives.extend(tracking.values());result=dict(rom=metadata['rom'],weapon=metadata['weapon'],protocols={})
    for name,events in births.items():
        groups=Counter(e['frame']for e in events);times=sorted(groups)
        result['protocols'][name]=dict(peak_active=peak[name],peak_visible=visible[name],salvos=len(times),components=len(events),
            components_per_salvo=dict(Counter(groups.values())),intervals=dict(Counter(b-a for a,b in zip(times,times[1:]))),first_salvos=list(groups.items())[:12])
    held=births['segurado'];first=min(e['frame']for e in held)
    result['first_volley']=[e for e in held if e['frame']==first]
    tracks=[]
    for shot in result['first_volley']:
        life=next(t for t in lives if t['birth']==first and t['slot']==shot['slot']);points=life['points']
        delta=Counter((b[1]-a[1],b[2]-a[2])for a,b in zip(points,points[1:])if b[0]==a[0]+1)
        tracks.append(dict(slot=shot['slot'],frames=len(points),velocity_counts={f'{dx},{dy}':count for(dx,dy),count in delta.items()},points=points))
    result['first_tracks']=tracks
    (folder/'analysis.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
    rows=[]
    for folder in sorted(ROOT.glob('1943h*/[0-9A-F][0-9A-F]')):
        if not(folder/'status.txt').exists()or'resultado=ok'not in(folder/'status.txt').read_text():continue
        r=analyze(folder);rows.append(r)
        print(r['rom'],f"{r['weapon']:02X}",[(k,v['peak_active'],v['components_per_salvo'],v['intervals'])for k,v in r['protocols'].items()if k!='solto'])
    (ROOT/'analysis.json').write_text(json.dumps(rows,indent=2))
