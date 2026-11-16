"""Native hold/tap/capacity tests; all emulation frames retained in DMA."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,json,os,subprocess,zlib,struct
BASE=Path(__file__).resolve().parents[1]
WEAPONS=(0,1,2,3,4,8,0x10,0x30,0x50)
LIMITS=False
def run(job):
    rom,weapon=job;dest=BASE/('captures/cadencia_limites_05'if LIMITS else'captures/cadencia_armas_02')/rom/f'{weapon:02X}';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'status.txt').exists()and'resultado=ok'in(dest/'status.txt').read_text():return str(dest)+' existing'
    state=BASE/'captures'/rom/'catalogacao_01/checkpoint_f0001800.sta';assert state.exists()
    meta=dict(rom=rom,weapon=weapon,state=str(state),frames=2450,protocols={'hold':[31,390],'tap_every_2_frames':[511,870],'two_on_two_off':[991,1350],'detachment':[1471,1590],'pinned_capacity':[1621,2420]},frameskip=0,targets_blocked=True)
    (dest/'metadata.json').write_text(json.dumps(meta,indent=2))
    if LIMITS:
        raw=zlib.decompress((BASE/'captures/cadencia_armas_02'/rom/f'{weapon:02X}'/'dma.zlib').read_bytes())
        for at in range(0,len(raw),4101):
            n=struct.unpack_from('<I',raw,at)[0];a=raw[at+5:at+4101]
            if 31<=n<=100 and a[0x388]==2:
                (dest/'template.bin').write_bytes(a[0x380:0x3A0]);break
        else:raise AssertionError('native shot template missing')
        meta.update(frames=380,protocols={'preoccupied_slots':list(range(16))},method='native shot records occupy actual allocator slots; positions pinned')
        (dest/'metadata.json').write_text(json.dumps(meta,indent=2))
    args=[str(BASE/'1943h.exe'),rom,'-noreadconfig','-rompath','roms','-state',str(state),'-nothrottle','-frameskip','0','-noautoframeskip','-video','none','-sound','none','-noplugins','-nocheat','-skip_gameinfo','-cfg_directory',str(dest/'cfg'),'-autoboot_delay','0','-autoboot_script','capture_scripts/cadencia_armas.lua']
    with (dest/'mame.log').open('w')as f:
        subprocess.run(args,cwd=BASE,env={**os.environ,'DEST':dest.as_posix(),'WEAPON':str(weapon),'LIMITS_ONLY':'1'if LIMITS else'0'},stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
    assert 'resultado=ok'in(dest/'status.txt').read_text(),dest
    return f'{rom} {weapon:02X}: capture complete'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--limits',action='store_true');a=p.parse_args();LIMITS=a.limits
    jobs=[('1943h10111',0),('1943h11000',1)]if a.pilot else[(r,w)for r,ws in [('1943h10111',WEAPONS[:7]),('1943h11000',WEAPONS)]for w in ws]
    with ThreadPoolExecutor(max_workers=2)as pool:
        for result in pool.map(run,jobs):print(result,flush=True)
