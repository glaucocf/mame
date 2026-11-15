local M=manager.machine;local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local sprite_share=assert(M.memory.shares[':spriteram'])
local function peek(address)return sprite_share:read_u8(address-0xf000)end
local dest=os.getenv('DEST');local jobs=dofile(os.getenv('JOBS'));local kai=os.getenv('ROM')=='1943h11000'
local destruction=os.getenv('DESTRUCTION')=='1';local knownpath=os.getenv('KNOWN');local known=knownpath and knownpath~=''and dofile(knownpath)or{}
local observation=tonumber(os.getenv('OBSERVE_FRAMES'))or 120
local births=nil;local newstates=nil
if destruction then
 births=assert(io.open(dest..'/nascimentos.csv','w'));births:write('caso,quadro,apos_morte,endereco,tipo_construtor,construtor,banco,pc,referencia,flags,tipo,resistencia,sp,pilha,bytes,chave\n')
 newstates=assert(io.open(dest..'/novos_estados.csv','w'));newstates:write('chave,caso,quadro,endereco,referencia,flags,tipo,resistencia,estado,arquivo,bytes\n')
end
local out=assert(io.open(dest..'/resultados.csv','w'))
out:write('caso,modelo,modo,arma,resultado,quadros,alvo,tiro,flags_iniciais,tipo,resistencia_inicial,resistencia_final,forca_inicial,forca_final,estado_tiro_final,energia_inicial,energia_apos_dano,invuln_final,flag_jogador_07,leituras_flags,aproximacoes,pc_primeiro_evento,rotina,referencia_inicial,referencia_esperada,energia_antes_dano,dano_por_contato\n')
local events=assert(io.open(dest..'/eventos.csv','w'))
events:write('caso,quadro,tipo,endereco,antes,depois,pc,ix,iy\n')
local index,n=0,0;local job=nil;local state='start';local closed=false;local first_hit=nil;local shot=nil;local flags_reads=0;local approaches=0;local shots_seen=0;local initial=nil;local min_hp=0;local shot_force=0;local energy_hit=64;local energy_before=64;local hit_pc=0;local hit_kind='';local last_target_flags=0;local read_pcs={}
local consumed_by_hit=false;local force_after_hit=0
local owner_lost=false
local killed_at=nil;local bank=0;local pending_births={};local save_queue={};local saved_new={};local last_save=-100
local function hex(data)return(data:gsub('.',function(c)return string.format('%02X',c:byte())end))end
local function button(mask,on)for _,f in pairs(M.ioport.ports[':P1'].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end end
local function pc_kind(pc)
 if pc>=(kai and 0x57c6 or 0x56ba) and pc<=(kai and 0x5810 or 0x5704)then return 'alvo'
 elseif pc>=(kai and 0x6264 or 0x612f) and pc<=(kai and 0x628d or 0x6158)then return 'projetil'
 elseif pc>=(kai and 0x5e3b or 0x5d2a) and pc<=(kai and 0x5e7c or 0x5d6b)then return 'alvo_multisprite'
 elseif pc>=(kai and 0x65ff or 0x64ca) and pc<=(kai and 0x664e or 0x6519)then return 'alvo_grande'
 else return ''end
end
local function in_collision(pc)return pc>=0x5500 and pc<0x6800 end
local function player_shot(base)return base>=0xf380 and base<=0xf5a0 and base%32==0 end
local gates={}
for _,pc in ipairs(kai and {0x575b,0x578c,0x582b,0x61cb,0x61fc,0x6290,0x5dc7,0x5dfd,0x5e97,0x658b,0x65c5,0x6657} or {0x564f,0x5680,0x571f,0x6096,0x60c7,0x615b,0x5cb6,0x5cec,0x5d86,0x6456,0x6490,0x6522})do gates[pc]=true end
local function aligned_position(pc,target,default_offset)
 local adjustment=0
 if mem:read_u8(pc)==0xc6 and mem:read_u8(pc+1)==8 then adjustment=8;pc=pc+2 end
 local offset=default_offset
 if mem:read_u8(pc)==0xdd and mem:read_u8(pc+1)==0x96 then offset=mem:read_u8(pc+2)end
 return (peek(target+offset)-adjustment)&255
end
local function event(kind,address,before,after)
 events:write(string.format('%s,%d,%s,%04X,%d,%d,%04X,%04X,%04X\n',job.id,n,kind,address,before,after,cpu.state.PC.value,cpu.state.IX.value,cpu.state.IY.value))
end
local function status(reason)
 local file=assert(io.open(dest..'/status.txt','w'));file:write(string.format('indice=%d\ntotal=%d\ncaso=%s\nquadro=%d\nestado=%s\n',index,#jobs,job and job.id or '',n,reason or state));file:close()
end
local function next_job()
 index=index+1;job=jobs[index];n=0;first_hit=nil;shot=nil;flags_reads=0;approaches=0;shots_seen=0;initial=nil;shot_force=0;energy_hit=64;energy_before=64;hit_pc=0;hit_kind='';read_pcs={}
 consumed_by_hit=false;force_after_hit=0
 owner_lost=false
 killed_at=nil;bank=0;pending_births={};save_queue={};last_save=-100
 if not job then closed=true;out:close();events:close();if births then births:close();newstates:close()end;status('concluido');M:exit();return end
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 state='loading';status();M:load(job.checkpoint)
end
local function finish(reason)
 local target=job.target;local shot_state=shot and mem:read_u8(shot+8) or 0;local force=shot and mem:read_u8(shot+13) or 0
 if first_hit and job.mode=='arma'then shot_state=consumed_by_hit and 4 or 2;force=force_after_hit end
 if job.mode=='contato' then
  if first_hit then reason=energy_hit<64 and 'causou_dano_ao_jogador' or 'resposta_de_contato'
  elseif flags_reads>0 then reason='sem_dano_no_ensaio' end
 elseif first_hit then reason=shot_state==2 and force>0 and 'atingiu_e_continuou' or 'atingiu_e_consumiu_tiro'
 elseif shots_seen==0 then reason='nenhum_tiro_ativo'
 elseif flags_reads>0 and approaches==0 then reason='sem_teste_espacial_para_esta_arma'
 elseif approaches>0 then reason='aproximacao_sem_acerto' end
 if destruction then reason=killed_at and 'destruido_observado' or 'nao_destruido_no_limite'end
 if owner_lost and not first_hit then reason='registro_reatribuido_antes_do_impacto'end
 out:write(string.format('%s,%s,%s,%02X,%s,%d,%04X,%04X,%02X,%02X,%d,%d,%d,%d,%02X,%d,%d,%d,%d,%d,%d,%04X,%s,%04X,%04X,%d,%d\n',job.id,job.model,job.mode,job.weapon,reason,n,target,shot or 0,initial.flags,initial.kind,initial.hp,min_hp,shot_force,force,shot_state,64,energy_hit,mem:read_u8(0xf214),mem:read_u8(0xf207),flags_reads,approaches,hit_pc,hit_kind,initial.reference,job.reference,energy_before,energy_before-energy_hit));out:flush();events:flush()
 if first_hit or (job.mode=='contato' and job.model=='M109')then M.screens[':screen']:snapshot(job.output..'.png')end
 next_job()
end
local function initialize()
 n=0
 local t=job.target;initial={flags=mem:read_u8(t+9),kind=mem:read_u8(t+10),hp=mem:read_u8(t+11),reference=mem:read_u16(t+28)};min_hp=initial.hp;last_target_flags=initial.flags
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 for p=0xf380,0xf5a0,32 do mem:write_u8(p+8,0);mem:write_u8(p,0);mem:write_u8(p+2,0);mem:write_u8(p+3,0)end
 mem:write_u8(0xf251,job.weapon);mem:write_u8(0xf257,0x63);mem:write_u8(0xf214,2);mem:write_u8(0xf206,64)
 state='running';event('inicio',t+9,initial.flags,initial.flags)
end
post=emu.add_machine_post_load_notifier(function()if state=='loading'then initialize()end end)
readtap=mem:install_read_tap(0xf000,0xffff,'matriz_espaco',function(address,data)
 if closed or state~='running' then return end
 local pc=cpu.state.PC.value;if not in_collision(pc)then return end
 local ix=cpu.state.IX.value;local iy=cpu.state.IY.value;local target=job.target
 if (n<3 or ix~=target or first_hit)and address==ix+9 and gates[pc]then return 0 end
 if n<3 or first_hit then return end
 if ix==target and address==target+9 then
  flags_reads=flags_reads+1;last_target_flags=data
  if not read_pcs[pc]then read_pcs[pc]=true;event('teste_flags',address,data,data)end
 end
 if job.mode=='arma' and ix==target and player_shot(iy) and peek(iy+8)==2 then
  local code=peek(iy)+((peek(iy+1)&0xe0)<<3)
  if (job.secondary and code~=0x09f)or(job.segment_base and iy~=job.segment_base)then
   if address==iy+3 then return (aligned_position(pc,target,3)+128)&255 elseif address==iy+2 then return (aligned_position(pc,target,2)+128)&255 end
   return
  end
  if not shot and (address==iy+2 or address==iy+3)then shot=iy;shot_force=peek(iy+13);force_after_hit=shot_force;event('tiro_selecionado',iy+13,shot_force,shot_force);event('grafico_tiro',iy,code,peek(iy+1))end
  if shot==iy then
   if address==iy+3 then approaches=approaches+1;return aligned_position(pc,target,3)
   elseif address==iy+2 then return aligned_position(pc,target,2)end
  end
 elseif job.mode=='contato' and (address==0xf203 or address==0xf222)and ix>=0xf000 and ix<=0xffe0 then
  if ix==target then
   approaches=approaches+1
   if address==0xf203 then return aligned_position(pc,target,3)else return (cpu.state.AF.value>>8)&255 end
  else
   if address==0xf203 then return (peek(ix+3)+128)&255 else return (peek(ix+2)+136)&255 end
  end
 end
end)
writetap=mem:install_write_tap(0xf000,0xffff,'matriz_efeitos',function(address,data)
 if closed or state~='running' or n<3 then return end
 local pc=cpu.state.PC.value;local ix=cpu.state.IX.value;local iy=cpu.state.IY.value
 if address==job.target+8 and data~=0 and peek(address)==0 and not first_hit and n>=1 then owner_lost=true;event('registro_reatribuido',address,0,data)end
 if job.model=='M011'and job.weapon==16 and address%32==13 and address>=0xf380 and address<0xf5c0 then local old=mem:read_u8(address);if old~=data then event('debug_forca',address,old,data)end end
 if ix~=job.target or not in_collision(pc)then return end
 local before=peek(address);if before==data then return end
 local kind=pc_kind(pc)
 if job.mode=='arma' and kind~='' and player_shot(iy) and iy==shot then
  if address==job.target+11 or address==iy+8 or address==iy+13 then
   if not first_hit then first_hit=n;hit_pc=pc;hit_kind=kind end
   if address==job.target+11 then min_hp=math.min(min_hp,data)end
   if destruction and address==job.target+11 and data==0 and not killed_at then killed_at=n;event('alvo_destruido',address,before,data)end
   if address==iy+8 and data~=2 then consumed_by_hit=true end
   if address==iy+13 then force_after_hit=data end
   event('efeito_colisao',address,before,data)
  end
 elseif job.mode=='contato' and approaches>0 and (address==0xf206 or address==0xf204 or address==0xf208 or address==0xf20e)then
  if not first_hit then first_hit=n;hit_pc=pc;hit_kind='contato_jogador'end
  if address==0xf206 then energy_before=before;energy_hit=math.min(energy_hit,data)end
  event('efeito_contato',address,before,data)
 end
end)
banktap=mem:install_write_tap(0xc804,0xc804,'matriz_banco',function(address,data)bank=(data&0x1c)>>2 end)
birthtap=mem:install_write_tap(0xf000,0xffff,'matriz_filhos',function(address,data)
 if not destruction or closed or state~='running' or not killed_at or n-killed_at>observation or address%32~=8 or data==0 or mem:read_u8(address)~=0 then return end
 local base=address-8;if base>=0xf200 and base<0xf5c0 then return end
 local pc=cpu.state.PC.value;local template=pc;local style='P';local b=bank
 if pc>=2 and mem:read_u8(pc-2)==0xed and mem:read_u8(pc-1)==0xb0 then style='L';template=(cpu.state.HL.value-8)&0xffff;if template<0x8000 then b=-1 end end
 local sp=cpu.state.SP.value
 pending_births[#pending_births+1]={base=base,frame=n,style=style,template=template,bank=b,pc=pc,sp=sp,stack=hex(mem:read_range(sp,math.min(0xffff,sp+15),8))}
end)
local function process_births()
 if not destruction then return end
 for _,r in ipairs(pending_births)do
  local bytes=mem:read_range(r.base,r.base+31,8);local ref=mem:read_u16(r.base+28)
  local key=string.format('%s_%d_%04X_%04X',r.style,r.bank,r.template,ref)
  births:write(string.format('%s,%d,%d,%04X,%s,%04X,%d,%04X,%04X,%02X,%02X,%d,%04X,%s,%s,%s\n',job.id,r.frame,r.frame-killed_at,r.base,r.style,r.template,r.bank,r.pc,ref,bytes:byte(10),bytes:byte(11),bytes:byte(12),r.sp,r.stack,hex(bytes),key))
  if not known[key]and not saved_new[key]then saved_new[key]='queued';save_queue[#save_queue+1]={key=key,base=r.base}end
 end
 pending_births={}
 if #save_queue>0 then
  local r=table.remove(save_queue,1)
  if mem:read_u8(r.base+8)~=0 then
   local bytes=mem:read_range(r.base,r.base+31,8);local path=dest..'/novos/'..r.key
   M:save(path..'.sta');M.screens[':screen']:snapshot(path..'.png');last_save=n
   newstates:write(string.format('%s,%s,%d,%04X,%04X,%02X,%02X,%d,%02X,%s,%s\n',r.key,job.id,n,r.base,mem:read_u16(r.base+28),bytes:byte(10),bytes:byte(11),bytes:byte(12),bytes:byte(9),path..'.sta',hex(bytes)));newstates:flush();saved_new[r.key]=true
  else saved_new[r.key]=nil end
 end
 births:flush()
end
local function tick()
 if closed then return end
 if state=='start'then next_job();return end
 if state=='loading'then return end
 n=n+1
 if owner_lost and not destruction then finish('registro_reatribuido_antes_do_impacto');return end
 process_births()
 if destruction and first_hit and not killed_at and n-first_hit>=1 then first_hit=nil;shot=nil;shot_force=0;force_after_hit=0;consumed_by_hit=false end
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 mem:write_u8(0xf251,job.weapon);mem:write_u8(0xf257,0x63)
 mem:write_u8(0xf214,job.mode=='contato' and n>=3 and 0 or 2)
 if job.mode=='contato' and n==3 then mem:write_u8(0xf206,64)end
 if not first_hit and mem:read_u8(job.target+8)~=0 then
  mem:write_u8(job.target+2,128);mem:write_u8(job.target+3,128);mem:write_u8(job.target+1,mem:read_u8(job.target+1)&0xef)
 end
 if job.mode=='arma' and not first_hit then button(16,n>=3 and n%6<3)end
 for p=0xf380,0xf5a0,32 do if mem:read_u8(p+8)==2 then shots_seen=shots_seen+1 end end
 if destruction then
  if killed_at and n-killed_at>=observation and #save_queue==0 and n-last_save>=4 then finish('morte_observada');return end
  if not killed_at and(mem:read_u8(job.target+8)==0 or n>=600)and n>=10 then finish('nao_destruido_no_limite');return end
 else
  if first_hit and n-first_hit>=1 then finish('com_interacao');return end
  if mem:read_u8(job.target+8)==0 and n>=3 then finish('alvo_expirou');return end
  if n>=90 then finish('sem_teste_de_colisao');return end
 end
 if n%30==0 then status()end
end
frame=emu.add_machine_frame_notifier(function()local ok,err=pcall(tick);if not ok and not closed then local f=io.open(dest..'/erro.txt','w');f:write(tostring(err));f:close();closed=true;out:close();events:close();status('erro');M:exit()end end)
