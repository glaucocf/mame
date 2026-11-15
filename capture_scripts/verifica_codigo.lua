local M=manager.machine
local mem=M.devices[':maincpu'].spaces.program
local dest=os.getenv('DEST')
local enabled=os.getenv('CODIGO')=='1'
local log=assert(io.open(dest..'/arma.csv','w'))
log:write('quadro,arma_F251,tempo_F257,energia_F206\n')
local n=0
local function set(player,mask,on)
 for _,field in pairs(M.ioport.ports[':P'..player].fields) do
  if field.mask==mask then field:set_value(on and 1 or 0) end
 end
end
sub=emu.add_machine_frame_notifier(function()
 n=n+1
 for _,mask in ipairs({1,8,16,32}) do set(1,mask,enabled and n<650) end
 for _,mask in ipairs({4,32}) do set(2,mask,enabled and os.getenv('P2')=='1' and n<650) end
 log:write(string.format('%d,%02X,%d,%d\n',n,mem:read_u8(0xf251),mem:read_u8(0xf257),mem:read_u8(0xf206)))
 if n%120==0 then M.screens[':screen']:snapshot(dest..string.format('/f%04d.png',n)) end
 if n==800 then log:close();M:exit() end
end)
