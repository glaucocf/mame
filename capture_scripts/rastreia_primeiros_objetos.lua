local M=manager.machine
local cpu=M.devices[':maincpu']
local mem=cpu.spaces.program
local dest=os.getenv('DEST')
local log=assert(io.open(dest..'/escritas.csv','w'))
local groups=assert(io.open(dest..'/grupos.csv','w'))
groups:write('quadro,endereco,anterior,novo,pc,banco\n')
log:write('quadro,endereco,registro,campo,anterior,novo,pc,banco\n')
local n=0
local fire=os.getenv('FIRE')=='1'
local bank=0
local closed=false
local function button(port,mask,on)
 for _,field in pairs(M.ioport.ports[port].fields) do if field.mask==mask then field:set_value(on and 1 or 0) end end
end
banktap=mem:install_write_tap(0xc804,0xc804,'primeiros_banco',function(offset,data) bank=(data&0x1c)>>2 end)
objecttap=mem:install_write_tap(0xf5c0,0xfa3f,'primeiros_objetos',function(address,data)
 if closed or n<360 then return end
 local field=address%32
 if field>7 and field<0x1b and field~=0x15 then return end
 local previous=mem:read_u8(address)
 if previous==data then return end
 log:write(string.format('%d,%04X,%02X,%02X,%02X,%02X,%04X,%d\n',n,address,(address-0xf000)//32,field,previous,data,cpu.state['PC'].value,bank))
end)
local function group_write(address,data)
 if closed or n<360 then return end
 local previous=mem:read_u8(address)
 if previous~=data then groups:write(string.format('%d,%04X,%02X,%02X,%04X,%d\n',n,address,previous,data,cpu.state['PC'].value,bank)) end
end
flag_tap=mem:install_write_tap(0xe133,0xe133,'primeiros_flag',group_write)
group_tap=mem:install_write_tap(0xe200,0xe20f,'primeiros_contador',group_write)
local function tick()
 if closed then return end
 n=n+1
 button(':SYSTEM',64,n>=300 and n<305)
 button(':SYSTEM',1,n>=360 and n<365)
 mem:write_u8(0xf214,2)
 button(':P1',16,fire and n>1100 and n%6<3)
 if fire then mem:write_u8(0xf251,4);mem:write_u8(0xf257,0x63);mem:write_u8(0xf254,0xf8);mem:write_u8(0xf256,0) end
 if n==480 or n==1100 or n==1320 or n==1440 or n==1800 or n==2640 or n==2880 then
  M.screens[':screen']:snapshot(dest..string.format('/f%04d.png',n))
  M:save(dest..string.format('/f%04d.sta',n))
 end
 if fire and n>=1320 and n<=2160 and n%60==0 then M.screens[':screen']:snapshot(dest..string.format('/f%04d.png',n)) end
 if n%60==0 then log:flush();groups:flush() end
 if n==3000 then closed=true;log:close();groups:close();M:exit() end
end
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick);if not ok then log:write('ERRO '..tostring(err));log:flush();closed=true;M:exit() end end)
