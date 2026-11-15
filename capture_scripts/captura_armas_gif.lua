local M=manager.machine
local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local dest=os.getenv('DEST');local weapon=tonumber(os.getenv('WEAPON'))
local n,control,sequence=0,0,0;local closed=false
local frames=420
local log=assert(io.open(dest..'/quadros.csv','w'))
local hits=assert(io.open(dest..'/reducoes_forca.csv','w'))
hits:write('quadro,endereco,forca_antes,forca_depois,pc,ix,iy,tipo_alvo_0A,codigo_tiro\n')
log:write('quadro,botao,arma_antes,arma_forcada,tempo,cooldown_F254,cooldown_F256\n')
local raw=assert(io.open(dest..'/dma.zlib','wb'));local compress=require('zlib').deflate(3)
local meta=assert(io.open(dest..'/video.txt','w'));meta:write(string.format('refresh=%.12f\nframe_period=%.12f\n',M.screens[':screen'].refresh,M.screens[':screen'].frame_period));meta:close()
local function button(mask,on)
 for _,field in pairs(M.ioport.ports[':P1'].fields) do if field.mask==mask then field:set_value(on and 1 or 0);return end end
 error('controle nao encontrado')
end
banktap=mem:install_write_tap(0xc804,0xc804,'gif_caracteres',function(address,data) control=data&0x7f;return control end)
layertap=mem:install_write_tap(0xd806,0xd806,'gif_fundo',function(address,data) return 0x40 end)
strengthtap=mem:install_write_tap(0xf380,0xf5bf,'gif_forca',function(address,data)
 if closed or address%32~=13 then return end
 local before=mem:read_u8(address);local base=address-13
 if data>0 and data<before and mem:read_u8(base+8)==2 then
  local ix=cpu.state.IX.value;local kind=ix>=0xf000 and ix<=0xffe0 and mem:read_u8(ix+10) or 0
  local code=mem:read_u8(base)+((mem:read_u8(base+1)&0xe0)<<3)
  hits:write(string.format('%d,%04X,%d,%d,%04X,%04X,%04X,%02X,%03X\n',n,address,before,data,cpu.state.PC.value,ix,cpu.state.IY.value,kind,code))
 end
end)
dmatap=mem:install_write_tap(0xc806,0xc806,'gif_dma',function()
 if closed then return end
 sequence=sequence+1
 local packed=compress(string.pack('<I4I1',n,control)..mem:read_range(0xf000,0xffff,8),sequence%60==0 and 'sync' or 'none');raw:write(packed)
end)
local function finish(reason)
 if closed then return end;closed=true
 local packed=compress('','finish');raw:write(packed);raw:close();log:close();hits:close()
 local status=assert(io.open(dest..'/status.txt','w'));status:write(string.format('quadros=%d\ndma=%d\nresultado=%s\n',n,sequence,reason));status:close();M:exit()
end
local function tick()
 if closed then return end
 n=n+1
 local fire=(n>=31 and n<=150) or (n>=181 and n<=300 and (n-181)%6<3)
 for _,mask in ipairs({1,2,4,8,32}) do button(mask,false) end
 button(16,fire)
 log:write(string.format('%d,%d,%02X,%02X,%d,%02X,%02X\n',n,fire and 1 or 0,mem:read_u8(0xf251),weapon,mem:read_u8(0xf257),mem:read_u8(0xf254),mem:read_u8(0xf256)))
 mem:write_u8(0xf251,weapon);mem:write_u8(0xf257,0x63)
 mem:write_u8(0xf214,2);mem:write_u8(0xd806,0x40)
 if mem:read_u8(0xf206)<12 then mem:write_u8(0xf206,32) end
 if n==60 or n==120 or n==200 or n==240 or n==330 then assert(not M.screens[':screen']:snapshot(dest..string.format('/mame_f%04d.png',n))) end
 if n>=frames then finish('ok') end
end
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick);if not ok then finish('erro: '..tostring(err)) end end)
