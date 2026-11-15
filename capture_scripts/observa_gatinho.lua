local M=manager.machine
local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local dest=os.getenv('DEST');local template=tonumber(os.getenv('TEMPLATE_ADDR'))
local log=assert(io.open(dest..'/eventos.csv','w'));log:write('quadro,evento,endereco,valor,pc,ix,iy\n')
local n=0;local slot=nil
local function event(kind,address,value)
 log:write(string.format('%d,%s,%04X,%02X,%04X,%04X,%04X\n',n,kind,address,value,cpu.state.PC.value,cpu.state.IX.value,cpu.state.IY.value));log:flush()
end
tap=mem:install_write_tap(0xf251,0xf251,'gatinho_arma',function(address,data) if data~=mem:read_u8(address) then event('arma',address,data) end end)
sub=emu.add_machine_frame_notifier(function()
 n=n+1;mem:write_u8(0xf214,2)
 if n==1 then
  for base=0xf5c0,0xf7a0,32 do if mem:read_u8(base+8)==0 then slot=base;break end end
  assert(slot,'sem registro livre')
  local bytes=mem:read_range(template,template+31,8)
  for i=1,32 do mem:write_u8(slot+i-1,bytes:byte(i)) end
  mem:write_u8(slot+2,0x80);mem:write_u8(slot+3,0x80)
  event('criacao_teste',slot,mem:read_u8(slot+0xa))
 end
 if n>=80 and n<=85 then
  mem:write_u8(slot+2,(mem:read_u8(0xf222)-8)&255);mem:write_u8(slot+3,mem:read_u8(0xf203))
 end
 if n==2 or n==4 or n==20 or n==40 or n==60 or n==79 or n==84 or n==100 or n==120 then
  M.screens[':screen']:snapshot(dest..string.format('/f%04d.png',n))
  event('grafico',slot,mem:read_u8(slot));event('estado',slot+8,mem:read_u8(slot+8))
 end
 if n==120 then log:close();M:exit() end
end)
