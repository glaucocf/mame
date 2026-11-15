local mem = manager.machine.devices[":maincpu"].spaces["program"]
local p1=manager.machine.ioport.ports[":P1"]
local p2=manager.machine.ioport.ports[":P2"]
local out=io.open("C:/Users/glauc/OneDrive/Documentos/claude/arcade/battle-of-midway/mame-src/captures/probe_state/nav.txt","w")
local n=0
local function button(port,name,v) if port.fields[name] then port.fields[name]:set_value(v) end end
emu.register_frame_done(function()
 n=n+1
 mem:write_u8(0xE835,7)
 button(p1,"P1 Button 1",n>=20 and n<26 and 1 or 0)
 button(p2,"P2 Button 2",n>=100 and n<106 and 1 or 0)
 if n==140 then
  local a=mem:read_u8(0xD800)+256*mem:read_u8(0xD801)
  local b=mem:read_u8(0xD803)+256*mem:read_u8(0xD804)
  out:write(string.format("%d E835=%02X A=%04X B=%04X\n",n,mem:read_u8(0xE835),a,b));out:close()
  manager.machine.video:snapshot()
 end
end)
