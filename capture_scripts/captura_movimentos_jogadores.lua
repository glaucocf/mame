-- Native player graphics/movement reference for the separate SEGA graphics ROMs.
local M=manager.machine;local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local dest=assert(os.getenv('DEST'));local checkpoint=assert(os.getenv('CHECKPOINT'))
local cold=os.getenv('COLD')=='1'
local ram=assert(M.memory.shares[':spriteram'])
local function peek(a)return ram:read_u8(a-0xf000)end
local function poke(a,v)ram:write_u8(a-0xf000,v&255)end
local n=0;local stage='start';local ready=0;local active=false;local done=false
local controls={0,2,1,8,4,10,9,6,5}
local names={'NEUTRO','ESQUERDA','DIREITA','CIMA','BAIXO','CIMA_ESQUERDA','CIMA_DIREITA','BAIXO_ESQUERDA','BAIXO_DIREITA'}
local control=0
local raw=assert(io.open(dest..'/dma.bin','wb'))
local frames=assert(io.open(dest..'/quadros.csv','w'))
frames:write('quadro,fase,passo,direcao,tempo,p1_estado,p2_estado,p1_x,p1_y,p2_x,p2_y,p1_pal,p2_pal\n')
local function pad(port,mask,on)
 for _,f in pairs(M.ioport.ports[port].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end
end
local function clear_inputs()
 for _,port in ipairs({':P1',':P2'})do for _,mask in ipairs({1,2,4,8,16,32})do pad(port,mask,false)end end
 for _,mask in ipairs({1,2,64,128})do pad(':SYSTEM',mask,false)end
end
local function finish(reason)
 if done then return end;done=true;raw:close();frames:close()
 local f=assert(io.open(dest..'/status.txt','w'));f:write(string.format('resultado=%s\nquadros=%d\np1=%02X\np2=%02X\n',reason,n,peek(0xf208),peek(0xf288)));f:close();M:exit()
end
post=emu.add_machine_post_load_notifier(function()if stage=='loading'then stage='join';n=0 end end)
chars=mem:install_write_tap(0xc804,0xc804,'jogadores_chars',function(a,d)control=d&0x7f;return control end)
layers=mem:install_write_tap(0xd806,0xd806,'jogadores_bg',function(a,d)return 0x40 end)
dma=mem:install_write_tap(0xc806,0xc806,'jogadores_dma',function()
 if not done then raw:write(string.pack('<I4I1',n,control)..mem:read_range(0xf000,0xffff,8))end
end)
local function tick()
 if done then return end
 if stage=='start'then if cold then stage='join';n=0 else stage='loading';M:load(checkpoint)end;return end
 if stage=='loading'then return end
 n=n+1;clear_inputs()
 poke(0xf214,2);poke(0xf294,2)
 if peek(0xf206)>0 then poke(0xf206,64)end
 if peek(0xf286)>0 then poke(0xf286,64)end
 mem:write_u8(0xd806,0x40)
 if stage=='join'then
  mem:write_u8(0xe312,9);pad(':SYSTEM',2,cold and n>=360 and n<=365 or not cold and n>=10 and n<=15)
  if peek(0xf208)==2 and peek(0xf288)==2 then
   ready=ready+1
   if ready==30 then stage='capture';n=0;M:save(dest..'/dois_jogadores.sta')end
  else ready=0 end
  if n>=1800 then finish('nao_ativou_dois_jogadores')end
  return
 end
 local step=(n-1)//96+1;local t=(n-1)%96
 local mask=controls[step]or 0;local name=names[step]or'EXTRA'
 if step<=9 then
  if t==0 then
   for _,base in ipairs({0xf200,0xf280})do
    poke(base+2,base==0xf200 and 80 or 144);poke(base+3,96);poke(base+5,0);poke(base+6,0)
   end
  end
  local applied=t<48 and mask or 0
  for _,port in ipairs({':P1',':P2'})do for _,bit in ipairs({1,2,4,8})do pad(port,bit,(applied&bit)~=0)end end
 else
  -- Capture the special button and native reversal transitions as well.
  local extra=n-9*96
  if extra<=120 then pad(':P1',32,extra>=10 and extra<16);pad(':P2',32,extra>=60 and extra<66);name='ESPECIAL'
  elseif extra<=360 then
   local dir=(extra%80)<40 and 2 or 1
   for _,port in ipairs({':P1',':P2'})do pad(port,dir,true)end;name='REVERSAO'
  else finish('ok');return end
 end
 frames:write(string.format('%d,%s,%d,%s,%d,%02X,%02X,%d,%d,%d,%d,%X,%X\n',n,stage,step,name,t,peek(0xf208),peek(0xf288),peek(0xf203),peek(0xf202),peek(0xf283),peek(0xf282),peek(0xf201)&15,peek(0xf281)&15))
 if n%96==32 or n==900 then M.screens[':screen']:snapshot(dest..string.format('/mame_%04d.png',n))end
end
frame=emu.add_machine_frame_notifier(function()local ok,err=pcall(tick);if not ok then local f=assert(io.open(dest..'/erro.txt','w'));f:write(tostring(err));f:close();finish('erro')end end)
