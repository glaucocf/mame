local mem=manager.machine.devices[":maincpu"].spaces["program"]
local n=0
emu.register_frame_done(function()
 n=n+1
 mem:write_u8(0xE835,7)
 if n==140 then manager.machine.video:snapshot() end
end)
