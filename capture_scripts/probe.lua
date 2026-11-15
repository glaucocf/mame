local mem = manager.machine.devices[":maincpu"].spaces["program"]
local p1 = manager.machine.ioport.ports[":P1"]
local function set(n,v) if p1.fields[n] then p1.fields[n]:set_value(v) end end
local log=io.open("C:/Users/glauc/OneDrive/Documentos/claude/arcade/battle-of-midway/mame-src/captures/probe/log.txt","w")
local n=0
emu.add_machine_frame_notifier(function()
 n=n+1
 if n<=40 then mem:write_u8(0xE835,7) end
 set("P1 Button 1", n>=20 and n<26 and 1 or 0)
 set("P1 Up", n>=50 and n<80 and 1 or 0)
 if n%20==0 then
  local s=mem:read_u8(0xD800)+256*mem:read_u8(0xD801)
  local sy=mem:read_u8(0xD802)
  local b=mem:read_u8(0xD803)+256*mem:read_u8(0xD804)
  log:write(string.format("%d %04X %02X %04X\n",n,s,sy,b)); log:flush()
 end
 if n==200 then log:close(); manager.machine:exit() end
end)
