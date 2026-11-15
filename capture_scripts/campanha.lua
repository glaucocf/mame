local M=manager.machine
local mem=M.devices[':maincpu'].spaces.program
local dest=os.getenv('DEST')
local maxframe=tonumber(os.getenv('FRAMES'))
local fire=os.getenv('FIRE')~='0'
local sweep=os.getenv('FIRE')=='2'
local resume=os.getenv('RESUME')
local n=0
local oldstage=-1
local visited={}
local final_at=nil
local log=assert(io.open(dest..'/eventos.csv','w'))
log:write('quadro,evento,fase_E450,indice_E451,energia_F206,tanque_E12F,upper,lower,valor\n')
local raw=assert(io.open(dest..'/ram.zlib','wb'))
local compress=require('zlib').deflate(3)
local closed=false
local function event(kind,value)
 log:write(string.format('%d,%s,%d,%d,%d,%d,%d,%d,%s\n',n,kind,mem:read_u8(0xe450),mem:read_u8(0xe451),mem:read_u8(0xf206),mem:read_u8(0xe12f),mem:read_u16(0xd800),mem:read_u16(0xd803),value or ''))
 log:flush()
end
local function set(port,mask,on)
 for _,field in pairs(M.ioport.ports[port].fields) do
  if field.mask==mask then field:set_value(on and 1 or 0);return end
 end
 error('controle ausente '..port)
end
local function shot()
 local err=M.screens[':screen']:snapshot(dest..string.format('/f%07d.png',n))
 assert(not err,tostring(err))
end
local function finish(reason)
 if closed then return end
 event(reason)
 M:save(dest..'/continuar.sta')
 closed=true
 local packed=compress('','finish')
 raw:write(packed);raw:close();log:close()
 M:exit()
end
soundtap=mem:install_write_tap(0xc800,0xc800,'campanha_som',function(offset,data,mask) if not closed and data~=0xff and data~=0 then event('som',string.format('%02X',data)) end end)
layertap=mem:install_write_tap(0xd806,0xd806,'campanha_camadas',function(offset,data,mask) if not closed then event('camadas',string.format('%02X',data)) end end)
local function tick()
 if closed then return end
 n=n+1
 if n==1 and resume~='' then M:load(resume) end
 local packed=compress(string.pack('<I4',n)..mem:read_range(0xd000,0xd806,8)..mem:read_range(0xe000,0xffff,8),n%60==0 and 'sync' or 'none')
 raw:write(packed)
 mem:write_u8(0xf214,2)
 local energy=mem:read_u8(0xf206)
 if energy>0 and energy<12 then event('protecao_energia',32);mem:write_u8(0xf206,32) end
 set(':SYSTEM',64,resume=='' and n>=300 and n<305)
 set(':SYSTEM',1,resume=='' and n>=360 and n<365)
 set(':P1',16,fire and n%6<3)
 if sweep then
  set(':P1',1,n>120 and (n//120)%2==0)
  set(':P1',2,n>120 and (n//120)%2==1)
 end
 if fire then mem:write_u8(0xf251,4);mem:write_u8(0xf257,0x63);mem:write_u8(0xf254,0xf8);mem:write_u8(0xf256,0) end
 local stage=mem:read_u8(0xe450)
 if n>400 and stage<16 then visited[stage]=true end
 if stage~=oldstage then
  if oldstage==15 and stage==0 then
   local total=0;for _ in pairs(visited) do total=total+1 end
   if total==16 then final_at=n;event('possivel_final') end
  end
  event('fase');oldstage=stage;M:save(dest..string.format('/fase_%02d_f%07d.sta',stage,n));shot()
 end
 if n%60==0 then event('amostra') end
 if n%4==0 then shot() end
 if final_at and n-final_at==3600 then finish('apos_retorno_da_fase_16') end
 if n==maxframe then finish('limite_do_trecho') end
end
sub=emu.add_machine_frame_notifier(function()
 local ok,err=pcall(tick)
 if not ok then event('erro',tostring(err));finish('erro_fatal') end
end)
