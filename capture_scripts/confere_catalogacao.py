from pathlib import Path
import csv,json,struct,sys,zlib
base=Path(__file__).resolve().parents[1]
rom=sys.argv[1];folder=base/'captures'/rom/'catalogacao_01'
status=dict(line.split('=',1) for line in (folder/'status.txt').read_text().splitlines())
assert status['concluido']=='campanha_concluida',status
events=list(csv.DictReader((folder/'eventos.csv').open()))
phases={int(row['valor']) for row in events if row['evento']=='fase'}|{0}
assert all(i in phases for i in range(16)),phases
assert any(row['evento']=='retorno_apos_final' for row in events)
assert not any(row['evento'] in ('erro','erro_fatal') for row in events)
pngs={int(path.stem[1:]) for path in folder.glob('f*.png')}
frames=int(status['quadro']);missing=[f for f in range(4,frames+1,4) if f not in pngs]
assert not missing,missing[:10]
decoder=zlib.decompressobj();pending=b'';seq=0;last_frame=-1;cat=[]
with (folder/'dma.zlib').open('rb') as stream:
    while chunk:=stream.read(65536):
        pending+=decoder.decompress(chunk)
        size=len(pending)//4107*4107
        for off in range(0,size,4107):
            frame,number,bank,layers,control=struct.unpack_from('<IIBBB',pending,off)
            assert number==seq+1 and frame>=last_frame,(seq,number,last_frame,frame)
            seq=number;last_frame=frame
            if layers&0x40:
                for slot in range(128):
                    p=off+11+slot*32
                    code,attr,y,x=pending[p:p+4]
                    if code in (0xc4,0xc5,0xcc,0xcd) and attr==0xa9 and x<256 and 0<=y<240:
                        if not cat or cat[-1][1]!=slot or frame-cat[-1][0]>1:cat.append((frame,slot,code,attr,x,y))
        pending=pending[size:]
assert decoder.eof and not pending
assert seq==int(status['dma'])
summary={'rom':rom,'quadros':frames,'imagens':len(pngs),'dma':seq,'dma_ultimo_quadro':last_frame,'fases_1_a_16':True,'retorno_apos_final':True,'lacunas_imagens':len(missing),'dma_stream_finalizado':decoder.eof,'gatinho_candidatos_dma':cat,'intervencoes':[row for row in events if row['evento'].startswith('intervencao_')],'coletas_laser':[row for row in events if row['evento']=='candidato_laser']}
(folder/'analise'/'validacao.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2),flush=True)
