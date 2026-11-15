local mem = manager.machine.devices[":maincpu"].spaces["program"]
local n=0
local log=io.open("C:/Users/glauc/OneDrive/Documentos/claude/arcade/battle-of-midway/mame-src/captures/probe/log2.txt","w")
emu.register_frame_done(function()
 n=n+1
 if n<=40 then mem:write_u8(0xE835,7) end
 if n%20==0 then
  local s=mem:read_u8(0xD800)+256*mem:read_u8(0xD801)
  local sy=mem:read_u8(0xD802)
  local b=mem:read_u8(0xD803)+256*mem:read_u8(0xD804)
  log:write(string.format("%d %04X %02X %04X\n",n,s,sy,b))
  manager.machine.video:snapshot()
 end
end)
