local M=manager.machine;local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local dest=os.getenv('DEST');local jobs=dofile(os.getenv('JOBS'))
local log=assert(io.open(dest..'/preparacao.csv','w'))
log:write('modelo,resultado,quadro_local,quadro_estimado,endereco,estado,flags,tipo,resistencia,raio_y,raio_x,codigo,x,y,referencia_1C,bytes\n')
local index,n,bank=0,0,0;local job=nil;local state='start';local target=nil;local candidates={};local found_at=0;local save_wait=0;local closed=false;local saved_fallback=false
local function hex(data)return (data:gsub('.',function(c)return string.format('%02X',c:byte())end))end
local function button(mask,on)for _,f in pairs(M.ioport.ports[':P1'].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end end
local function status(reason)
 local f=assert(io.open(dest..'/status.txt','w'));f:write(string.format('indice=%d\ntotal=%d\nmodelo=%s\nquadro_local=%d\nestado=%s\n',index,#jobs,job and job.id or '',n,reason or state));f:close()
end
local function next_job()
 index=index+1;job=jobs[index];target=nil;candidates={};n=0;bank=0;saved_fallback=false
 if not job then closed=true;log:close();status('concluido');M:exit();return end
 state='loading';status();M:load(job.checkpoint)
end
local function record(reason)
 local b=target and mem:read_range(target,target+31,8) or string.rep('\0',32)
 local code=b:byte(1)+((b:byte(2)&0xe0)<<3)
 log:write(string.format('%s,%s,%d,%d,%04X,%02X,%02X,%02X,%d,%d,%d,%03X,%d,%d,%04X,%s\n',job.id,reason,n,job.baseframe+n,target or 0,b:byte(9),b:byte(10),b:byte(11),b:byte(12),b:byte(13),b:byte(14),code,b:byte(4)-((b:byte(2)&16)<<4),b:byte(3),string.unpack('<I2',b,29),hex(b)));log:flush()
end
local function save(reason)
 record(reason);M:save(job.output..'.sta');M.screens[':screen']:snapshot(job.output..'.png');state='saving';save_wait=0;status(reason)
end
post=emu.add_machine_post_load_notifier(function()if state=='loading' then n=0;state='finding';status()end end)
banktap=mem:install_write_tap(0xc804,0xc804,'prepara_banco',function(a,data)bank=(data&0x1c)>>2 end)
birthtap=mem:install_write_tap(0xf000,0xffff,'prepara_nascimento',function(address,data)
 if closed or state~='finding' or address%32~=8 or data==0 then return end
 local pc=cpu.state.PC.value
 if pc<2 or mem:read_u8(pc-2)~=0xed or mem:read_u8(pc-1)~=0xb0 then return end
 local template=(cpu.state.HL.value-8)&0xffff
 if template==job.template and (job.bank==-1 or bank==job.bank) then candidates[#candidates+1]=address-8 end
end)
local function tick()
 if closed then return end
 if state=='start' then next_job();return end
 if state=='loading' then return end
 if state=='saving' then save_wait=save_wait+1;if save_wait>=3 then local f=io.open(job.output..'.sta','rb');assert(f,'save ausente '..job.id);f:close();next_job()end;return end
 n=n+1
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 if state=='finding' and job.originalfire then button(16,(job.baseframe+n)%6<3);mem:write_u8(0xf257,0x63);mem:write_u8(0xf254,0xf8);mem:write_u8(0xf256,0)end
 mem:write_u8(0xf214,2)
 if mem:read_u8(0xf206)>0 and mem:read_u8(0xf206)<12 then mem:write_u8(0xf206,32)end
 if state=='finding' then
  for _,base in ipairs(candidates)do
   if mem:read_u16(base+28)==job.reference then target=base;found_at=n;state='observing';break end
  end
  candidates={}
 end
 if target then
  local active=mem:read_u8(target+8)~=0;local attr=mem:read_u8(target+1);local y=mem:read_u8(target+2);local x=mem:read_u8(target+3)
  local visible=(attr&16)==0 and y>=16 and y<240 and x<248
  if active and visible and (mem:read_u8(target+9)&3)~=0 and mem:read_u8(0xf208)==2 then save('colisao_ativa');return end
  if active and visible and not saved_fallback then M:save(job.output..'.sta');M.screens[':screen']:snapshot(job.output..'.png');saved_fallback=true end
  if not active or n-found_at>=360 then
   if saved_fallback then record('fallback_visual');state='saving';save_wait=0;status('fallback_visual')
   elseif active then save('fora_da_area')
   else record('perdido_sem_save');next_job()end
   return
  end
 end
 if n>=1000 then record('nao_localizado');next_job();return end
 if n%120==0 then status()end
end
frame=emu.add_machine_frame_notifier(function()local ok,err=pcall(tick);if not ok and not closed then local f=io.open(dest..'/erro.txt','w');f:write(tostring(err));f:close();closed=true;log:close();status('erro');M:exit()end end)
