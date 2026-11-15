local M=manager.machine
local mem=M.devices[':maincpu'].spaces.program
local dest=os.getenv('DEST')
local out=assert(io.open(dest..'/global_verificacao.txt','w'))
local n=0
local selected={}
local expected={}
local function find(suffix)
 for index,name in pairs(emu.plugin.cheat.list()) do
  if name=='Editor GLOBAL - '..suffix then return assert(emu.plugin.cheat.get(index)) end
 end
 error('cheat ausente '..suffix)
end
local function check(condition,message)
 assert(condition,message);out:write('OK '..message..'\n');out:flush()
end
local function each(fn)
 for slot=0,127 do fn(0xf000+slot*32,slot) end
end
local function tick()
 n=n+1
 if n==5 then
  selected.x=find('X interno');selected.y=find('Y interno');selected.gfx=find('grafico generico');selected.pal=find('paleta')
  selected.freeze=find('travar posicoes atuais');selected.hide=find('ocultar todas as pecas');selected.copy=find('copiar origem para TODOS (experimental)')
  for _,c in pairs(selected) do check(not c.get_enabled(),'inicia desligado '..c.desc) end
  selected.x.set_index(101);selected.y.set_index(121)
 end
 if n==8 then
  each(function(base) assert(mem:read_u8(base+3)==100 and mem:read_u8(base+2)==120) end)
  check(true,'X=100 e Y=120 nos 128 registros')
  selected.gfx.set_index(0x568);selected.pal.set_index(0xc)
 end
 if n==12 then
  each(function(base) assert(mem:read_u8(base)==0x67 and (mem:read_u8(base+1)&0xe0)==0xa0 and (mem:read_u8(base+1)&15)==11) end)
  check(true,'grafico 567 e paleta B nos 128 registros')
  for _,name in ipairs({'x','y','gfx','pal'}) do selected[name].set_enabled(false) end
  each(function(base,slot)
   local x=(slot*3)%256;local y=(slot*5)%256;local sign=slot%2==0 and 0 or 0x10
   mem:write_u8(base+3,x);mem:write_u8(base+2,y);mem:write_u8(base+1,(mem:read_u8(base+1)&0xef)|sign)
   expected[slot]={x=x,y=y,sign=sign}
  end)
  selected.freeze.set_index(3)
 end
 if n==16 then
  each(function(base,slot) local value=expected[slot];assert(mem:read_u8(base+3)==value.x and mem:read_u8(base+2)==value.y and (mem:read_u8(base+1)&0x10)==value.sign) end)
  check(true,'trava conserva posicao distinta e sinal de cada um dos 128 registros')
  selected.freeze.set_enabled(false)
  each(function(base,slot) expected[slot]={x=mem:read_u8(base+3),sign=mem:read_u8(base+1)&0x10} end)
  selected.hide.set_enabled(true)
 end
 if n==20 then
  each(function(base) assert(mem:read_u8(base+3)==0 and (mem:read_u8(base+1)&0x10)~=0) end)
  check(true,'oculta os 128 registros em X=-256')
  selected.hide.set_enabled(false)
  each(function(base,slot) local value=expected[slot];assert(mem:read_u8(base+3)==value.x and (mem:read_u8(base+1)&0x10)==value.sign) end)
  check(true,'desocultar restaura X e sinal individuais')
  local original=mem:read_range(0xf200,0xf21f,8)
  selected.copy.set_index(0x11);selected.copy.set_enabled(true)
  each(function(base) assert(mem:read_range(base,base+31,8)==original) end)
  check(true,'copia unica da origem 10 para todos os 128 registros')
  out:write('Concluido\n');out:close();M:exit()
 end
end
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick);if not ok then out:write('ERRO '..tostring(err)..'\n');out:flush();M:exit() end end)
