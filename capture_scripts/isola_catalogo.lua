local M=manager.machine;local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local ram=assert(M.memory.shares[':spriteram']);local dest=assert(os.getenv('DEST'))
local jobs=dofile(assert(os.getenv('JOBS')));local kai=os.getenv('ROM')=='1943h11000'
local index,n=0,0;local job=nil;local state='start';local closed=false
local pinned=true;local retired=false;local parts={};local bullets={}
local hold_x,hold_y=176,105;local blocked,hits,shots=0,0,0;local hp_min=0
local moved=false;local minx,maxx,miny,maxy=0,0,0,0;local snapshot_pending=false
local own=false;local frame_log=nil;local event_log=nil;local visible_parts={}
local out=assert(io.open(dest..'/resultados.csv','w'))
out:write('modelo,rotina,alvo,hp_original,hp_minimo,impactos_naturais,resultado,movimento_observado,x_min,x_max,y_min,y_max,projeteis_emitidos,ativacoes_bloqueadas,pecas_graficas,quadros,camadas\n')
local function peek(a)return ram:read_u8(a-0xf000)end
local function poke(a,v)ram:write_u8(a-0xf000,v&255)end
local function word(a)return peek(a)+256*peek(a+1)end
local function gfx(a)return peek(a)+((peek(a+1)&0xe0)<<3)end
local function event(kind,a,b,c)
 if not event_log then return end
 event_log:write(string.format('%d,%s,%04X,%d,%d,%04X,%04X,%04X\n',n,kind,a or 0,b or 0,c or 0,cpu.state.PC.value,cpu.state.IX.value,cpu.state.IY.value))
end
local function status(reason)
 local f=assert(io.open(dest..'/status.txt','w'));f:write(string.format('indice=%d\ntotal=%d\nmodelo=%s\nquadro=%d\nestado=%s\n',index,#jobs,job and job.id or '',n,reason or state));f:close()
end
local function button(mask,on)
 for _,f in pairs(M.ioport.ports[':P1'].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end
end
local function clear(base)
 for o=0,31 do poke(base+o,0)end;poke(base+1,0x10)
end
local function screenshot(name)
 assert(not M.screens[':screen']:snapshot(job.output..'/'..name..'.png'))
 local file=assert(io.open(job.output..'/'..name..'_sprites.bin','wb'));file:write(mem:read_range(0xf000,0xffff,8));file:close()
end
local function load_job()
 state='loading';status();M:load(job.checkpoint)
end
local function next_job()
 if frame_log then frame_log:close();event_log:close()end
 index=index+1;job=jobs[index]
 if not job then closed=true;out:close();state='concluido';status('concluido');M:exit();return end
 n=0;blocked=0;hits=0;shots=0;hp_min=job.hp;moved=false;visible_parts={}
 frame_log=assert(io.open(job.output..'/quadros.csv','w'))
 frame_log:write('quadro,estado,hp,flags,x,y,posicao_fixa,outros_inimigos,projeteis_proprios\n')
 event_log=assert(io.open(job.output..'/eventos.csv','w'))
 event_log:write('quadro,evento,endereco,antes,depois,pc,ix,iy\n')
 load_job()
end
local function finish_job()
 local count=0;for _ in pairs(visible_parts)do count=count+1 end
 local result=hp_min==0 and hits>0 and 'destruido_por_disparo_natural'or hits>0 and 'dano_por_disparo_natural'or'sem_impacto_natural_no_limite'
 out:write(string.format('%s,%s,%04X,%d,%d,%d,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,40\n',job.id,job.routine,job.target,job.hp,hp_min,hits,result,tostring(moved),minx,maxx,miny,maxy,shots,blocked,count,n));out:flush();event_log:flush()
 next_job()
end
local function initialize()
 local t=job.target
 assert(word(t+28)==job.reference,'referencia diferente: '..job.id)
 assert(peek(t+11)==job.hp,'HP original diferente: '..job.id)
 retired=false;bullets={};parts={[t]=true};pinned=true
 if job.routine=='alvo_multisprite'then for a=t,t+0x60,32 do parts[a]=true end
 elseif job.routine=='alvo_grande'then for a=t-0x80,t+0x160,32 do parts[a]=true end end
 for a in pairs(parts)do assert(a>=0xf000 and a<=0xffe0,'peca fora da RAM')end
 own=true
 for base=0xf000,0xffe0,32 do
  if not(base>=0xf200 and base<0xf300)and base~=t then
   if parts[base]then for o=8,31 do poke(base+o,0)end else clear(base)end
  end
 end
 local aim=peek(0xf222);if aim<48 or aim>192 then aim=112 end
 hold_y=aim+(job.routine=='alvo_multisprite'and -8 or job.routine=='alvo_grande'and 8 or 0)
 hold_x=176;poke(t+2,hold_y);poke(t+3,hold_x);poke(t+1,peek(t+1)&0xef);poke(t+5,0);poke(t+6,0)
 poke(0xf214,2);poke(0xf206,64);poke(0xf250,0);poke(0xf251,kai and 0x50 or 0x10);poke(0xf257,0x63)
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 mem:write_u8(0xd806,0x40);own=false;state='running'
 event('alvo_pronto',t,peek(t+8),peek(t+11));status()
end
post=emu.add_machine_post_load_notifier(function()
 if state=='loading'then
  local ok,err=pcall(initialize)
  if not ok then local f=assert(io.open(dest..'/erro.txt','w'));f:write(tostring(err));f:close();closed=true;status('erro');M:exit()end
 end
end)
layers=mem:install_write_tap(0xd806,0xd806,'isolado_BG',function(a,d)return 0x40 end)
chars=mem:install_write_tap(0xc804,0xc804,'isolado_CHAR',function(a,d)return d&0x7f end)
filter=mem:install_write_tap(0xf000,0xffff,'isolado_objetos',function(a,d)
 if own or state~='running'or closed then return end
 local base=a&0xffe0;local offset=a&31;local before=peek(a);local t=job.target
 if base>=0xf200 and base<0xf5c0 then return end
 if base==t then
  if retired then return before end
  if offset==11 and d<before then
   local iy=cpu.state.IY.value;local pc=cpu.state.PC.value
   if iy>=0xf380 and iy<0xf5c0 and pc>=0x5500 and pc<0x6800 then
    hits=hits+1;hp_min=math.min(hp_min,d);event('impacto_natural',a,before,d);snapshot_pending=true
   else event('valor_0B_alterado_por_outra_rotina',a,before,d)end
  end
  if offset==8 and d==0 then retired=true;event('alvo_retirado',a,before,d)end
  if pinned and peek(t+11)>0 then
   if offset==2 then return hold_y elseif offset==3 then return hold_x
   elseif offset==5 or offset==6 then return 0 elseif offset==1 then return d&0xef end
  end
  return
 end
 if parts[base]and offset<8 and cpu.state.IX.value==t then return end
 if base<0xf200 then
  local pc=cpu.state.PC.value
  if not bullets[base]and not retired and cpu.state.IX.value==t and cpu.state.IY.value==base and pc>=2 and mem:read_u8(pc-2)==0xed and mem:read_u8(pc-1)==0xb0 then
   bullets[base]=true;shots=shots+1;event('projetil_emitido_pelo_alvo',base,0,1)
  end
  if bullets[base]then return end
 end
 if offset==8 and d~=0 and before==0 then
  blocked=blocked+1
  if cpu.state.IX.value==t then event('criacao_propria_fora_do_pool_de_tiros_bloqueada',a,before,d)end
 end
 return before
end)
local function tick()
 if closed then return end
 if state=='start'then next_job();return end
 if state~='running'then return end
 n=n+1
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 poke(0xf214,2);if peek(0xf206)>0 and peek(0xf206)<12 then poke(0xf206,32)end
 poke(0xf251,kai and 0x50 or 0x10);poke(0xf257,0x63)
 if n==121 then
  pinned=false;minx=peek(job.target+3);maxx=minx;miny=peek(job.target+2);maxy=miny;event('movimento_livre',job.target,minx,miny)
 end
 if n>121 and n<=180 then
  local x,y=peek(job.target+3),peek(job.target+2)
  if x~=minx or y~=miny then moved=true end
  minx=math.min(minx,x);maxx=math.max(maxx,x);miny=math.min(miny,y);maxy=math.max(maxy,y)
 end
 if n==181 then load_job();return end
 if n>=184 and hp_min>0 then button(16,n%6<3)end
 for base in pairs(bullets)do if peek(base+8)==0 then clear(base);bullets[base]=nil end end
 if retired then for base in pairs(parts)do poke(base+1,peek(base+1)|0x10);poke(base+3,0)end end
 local others,own_shots=0,0
 for base=0xf000,0xffe0,32 do
  if not(base>=0xf200 and base<0xf5c0)and base~=job.target and peek(base+8)~=0 then
   if bullets[base]then own_shots=own_shots+1 else others=others+1 end
  end
  if parts[base]and gfx(base)~=0 and(peek(base+1)&0x10)==0 then visible_parts[base]=true end
 end
 assert(others==0,'outro inimigo ativo: '..job.id)
 frame_log:write(string.format('%d,%02X,%d,%02X,%d,%d,%s,%d,%d\n',n,peek(job.target+8),peek(job.target+11),peek(job.target+9),peek(job.target+3),peek(job.target+2),tostring(pinned),others,own_shots))
 if n==30 then screenshot('parado')elseif n==150 then screenshot('movimento')elseif n==210 then screenshot('antes_do_tiro')end
 if snapshot_pending then screenshot('impacto');snapshot_pending=false end
 if n%120==0 then frame_log:flush();event_log:flush();status()end
 if n>=360 and hp_min==0 and hits>0 then finish_job()
 elseif n>=1200 then screenshot('limite_sem_destruicao');finish_job()end
end
frame=emu.add_machine_frame_notifier(function()
 local ok,err=pcall(tick)
 if not ok then
  local f=assert(io.open(dest..'/erro.txt','w'));f:write(tostring(err));f:close();closed=true;status('erro');out:flush();if event_log then event_log:flush()end;M:exit()
 end
end)
