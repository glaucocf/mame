-- Controlled no-target trace. Keep the native shot allocator/cooldowns intact.
local M=manager.machine;local mem=M.devices[':maincpu'].spaces.program
local dest=assert(os.getenv('DEST'));local weapon=tonumber(os.getenv('WEAPON'))
local n,closed,own,sequence=0,false,false,0
local limits_only=os.getenv('LIMITS_ONLY')=='1'
local template=nil
if limits_only then local f=assert(io.open(dest..'/template.bin','rb'));template=f:read('*a');f:close();assert(#template==32)end
local csv=assert(io.open(dest..'/quadros.csv','w'))
csv:write('quadro,protocolo,botao,pin,player_x,player_y,arma,cooldown254,cooldown256,ativos\n')
local raw=assert(io.open(dest..'/dma.zlib','wb'));local zip=require('zlib').deflate(3)
local function button(mask,on)
 for _,f in pairs(M.ioport.ports[':P1'].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end
 error('botao ausente')
end
local function mode()
 if limits_only then
  if n>=31 and n<351 then return 'limite_'..((n-31)//20),(n-31)%20==5,true end
  return 'solto',false,false
 end
 if n>=1621 and n<=2420 then return 'saturacao',true,true end
 if n>=1471 and n<=1590 then return 'desvinculo',n<=1486,false end
 if n>=991 and n<=1350 then return 'pulso_2_2',(n-991)%4<2,false end
 if n>=511 and n<=870 then return 'cada_2_quadros',(n-511)%2==0,false end
 if n>=31 and n<=390 then return 'segurado',true,false end
 return 'solto',false,false
end
local function clear_shots()
 own=true
 for base=0xf300,0xf5a0,32 do for j=0,31 do mem:write_u8(base+j,0)end;mem:write_u8(base+1,0x10)end
 own=false
end
local function finish(reason)
 if closed then return end;closed=true
 local ok,err=pcall(function()local packed=zip('','finish');raw:write(packed);raw:close();csv:close()end)
 if not ok then reason='erro ao finalizar '..tostring(err)end
 local f=assert(io.open(dest..'/status.txt','w'));f:write('resultado='..reason..'\nquadros='..n..'\ndma='..sequence..'\n');f:close();M:exit()
end
taps={}
for base=0xf000,0xffe0,32 do
 if base<0xf200 or base>=0xf5c0 then
  taps[#taps+1]=mem:install_write_tap(base+8,base+8,'cadencia_inativo_'..base,function()if not own then return 0 end end)
  taps[#taps+1]=mem:install_write_tap(base+1,base+1,'cadencia_oculto_'..base,function(a,v)return v|0x10 end)
 end
end
bg=mem:install_write_tap(0xd806,0xd806,'cadencia_bg',function()return 0x40 end)
chars=mem:install_write_tap(0xc804,0xc804,'cadencia_chars',function(a,d)return d&0x7f end)
dma=mem:install_write_tap(0xc806,0xc806,'cadencia_dma',function()
 if closed then return end;sequence=sequence+1
 local packed=zip(string.pack('<I4I1',n,0)..mem:read_range(0xf000,0xffff,8),sequence%120==0 and 'sync'or'none');raw:write(packed)
end)
local function tick()
 n=n+1;local protocol,fire,pin=mode()
 if n==1 or n==31 or n==511 or n==991 or n==1471 or n==1621 then clear_shots()end
 if limits_only and n>=31 and n<351 and (n-31)%20==0 then
  clear_shots();own=true
  for slot=0,(n-31)//20-1 do
   for j=0,31 do mem:write_u8(0xf380+slot*32+j,template:byte(j+1))end
   mem:write_u8(0xf382+slot*32,104);mem:write_u8(0xf383+slot*32,128)
  end
  mem:write_u8(0xf253,(n-31)//20);mem:write_u8(0xf254,0xf8);mem:write_u8(0xf256,0);mem:write_u8(0xf250,weapon)
  own=false
 end
 for _,mask in ipairs({1,2,4,8,32})do button(mask,false)end;button(16,fire)
 own=true
 local player_x=(protocol=='desvinculo'and n>=1488)and 160 or 96
 mem:write_u8(0xf202,player_x);mem:write_u8(0xf203,32)
 mem:write_u8(0xf222,player_x+16);mem:write_u8(0xf223,32)
 mem:write_u8(0xf251,weapon);mem:write_u8(0xf257,99);mem:write_u8(0xf214,2)
 if mem:read_u8(0xf206)<12 then mem:write_u8(0xf206,64)end
 if n==1 then for base=0xf000,0xffe0,32 do
  if base<0xf200 or base>=0xf5c0 then mem:write_u8(base+8,0);mem:write_u8(base+1,mem:read_u8(base+1)|0x10);mem:write_u8(base+3,0)end
 end end
 if pin then for base=0xf380,0xf5a0,32 do if mem:read_u8(base+8)==2 then mem:write_u8(base+2,104);mem:write_u8(base+3,128)end end end
 own=false;local count=0
 for base=0xf380,0xf5a0,32 do if mem:read_u8(base+8)==2 then count=count+1 end end
 csv:write(string.format('%d,%s,%d,%d,%d,%d,%02X,%02X,%02X,%d\n',n,protocol,fire and 1 or 0,pin and 1 or 0,player_x,208,mem:read_u8(0xf251),mem:read_u8(0xf254),mem:read_u8(0xf256),count))
 if n==100 or n==600 or n==1100 or n==1490 or n==2300 then assert(not M.screens[':screen']:snapshot(dest..string.format('/f%04d.png',n)))end
 if n>=(limits_only and 380 or 2450)then finish('ok')end
end
sub=emu.add_machine_frame_notifier(function()if not closed then local ok,err=pcall(tick);if not ok then finish('erro '..tostring(err))end end end)
