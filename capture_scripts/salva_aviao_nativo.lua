local M=manager.machine;local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local dest=assert(os.getenv('DEST'));local template=tonumber(os.getenv('TEMPLATE'))
local reference=tonumber(os.getenv('REFERENCE'));local n=0;local target=nil;local candidates={};local saved_at=nil
local function pad(port,mask,on)
 for _,f in pairs(M.ioport.ports[port].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end
end
birth=mem:install_write_tap(0xf000,0xffff,'primeiro_aviao_nativo',function(a,d)
 if a%32~=8 or d==0 then return end
 local pc=cpu.state.PC.value
 if pc>=2 and mem:read_u8(pc-2)==0xed and mem:read_u8(pc-1)==0xb0 and((cpu.state.HL.value-8)&0xffff)==template then candidates[#candidates+1]=a-8 end
end)
local function tick()
 n=n+1
 if saved_at then if n-saved_at>=4 then M:exit()end;return end
 pad(':SYSTEM',64,n>=300 and n<305);pad(':SYSTEM',1,n>=360 and n<365)
 for _,mask in ipairs({1,2,4,8,16,32})do pad(':P1',mask,false)end
 mem:write_u8(0xf214,2)
 if mem:read_u8(0xf206)>0 and mem:read_u8(0xf206)<12 then mem:write_u8(0xf206,32)end
 for _,base in ipairs(candidates)do if mem:read_u16(base+28)==reference then target=base;break end end
 candidates={}
 if target and mem:read_u8(target+8)~=0 and(mem:read_u8(target+9)&3)~=0 and mem:read_u8(0xf208)==2 and mem:read_u8(target+2)>=16 and mem:read_u8(target+2)<240 and(mem:read_u8(target+1)&0x10)==0 then
  assert(mem:read_u8(target+11)==1)
  M:save(dest..'/aviao_inicial.sta');M.screens[':screen']:snapshot(dest..'/aviao_inicial.png')
  local f=assert(io.open(dest..'/alvo.json','w'));f:write(string.format('{"target":%d,"reference":%d,"frame":%d,"hp":1}\n',target,reference,n));f:close();saved_at=n
 end
 if n>=18000 then local f=assert(io.open(dest..'/erro.txt','w'));f:write('Aviao inicial nao localizado');f:close();M:exit()end
end
frame=emu.add_machine_frame_notifier(tick)
