local n=0
emu.register_frame_done(function()
 n=n+1
 if n==30 then manager.machine.video:snapshot() end
end)
