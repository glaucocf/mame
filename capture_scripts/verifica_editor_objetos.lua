local M=manager.machine
local mem=M.devices[':maincpu'].spaces.program
local dest=os.getenv('DEST')
local out=assert(io.open(dest..'/editor_verificacao.txt','w'))
local n=0
local selected={}
local function find(suffix)
 for index,name in pairs(emu.plugin.cheat.list()) do
  if name=='Editor 10 [F200] Objeto 10 - '..suffix then return assert(emu.plugin.cheat.get(index)) end
 end
 error('cheat ausente '..suffix)
end
local function check(condition,message)
 assert(condition,message);out:write('OK '..message..'\n');out:flush()
end
local function tick()
 n=n+1
 if n==5 then
  local total=0;for _,_ in pairs(emu.plugin.cheat.list()) do total=total+1 end
  out:write('Cheats carregados: '..total..'\n');out:flush()
  selected.x=find('X interno');selected.y=find('Y interno');selected.gfx=find('grafico generico');selected.pal=find('paleta')
  selected.freeze=find('travar posicao grafica');selected.hide=find('ocultar peca');selected.copy=find('copiar registro para (experimental)')
  for _,c in pairs(selected) do check(not c.get_enabled(),'inicia desligado '..c.desc) end
  selected.x.set_index(101);selected.y.set_index(121)
 end
 if n==8 then
  check(mem:read_u8(0xf203)==100,'X interno=100');check(mem:read_u8(0xf202)==120,'Y interno=120')
  selected.gfx.set_index(0x568);selected.pal.set_index(0xc)
 end
 if n==12 then
  check(mem:read_u8(0xf200)==0x67,'codigo baixo=67')
  check((mem:read_u8(0xf201)&0xe0)==0xa0,'codigo alto preservado')
  check((mem:read_u8(0xf201)&0xf)==0xb,'paleta=B')
  M.screens[':screen']:snapshot(dest..'/posicao_grafico_paleta.png')
  selected.x.set_enabled(false);selected.y.set_enabled(false);selected.gfx.set_enabled(false);selected.pal.set_enabled(false)
  mem:write_u8(0xf203,100);mem:write_u8(0xf202,120)
  selected.freeze.set_index(1)
 end
 if n==16 then
  check(mem:read_u8(0xf203)==100,'trava X atual')
  selected.freeze.set_enabled(false)
  selected.hide.set_enabled(true)
 end
 if n==20 then
  check(mem:read_u8(0xf203)==0 and (mem:read_u8(0xf201)&0x10)~=0,'ocultar usa X=-256')
  selected.hide.set_enabled(false)
  selected.copy.set_index(0x80);selected.copy.set_enabled(true)
  check(mem:read_range(0xf200,0xf21f,8)==mem:read_range(0xffe0,0xffff,8),'copia unica dos 32 bytes')
  out:write('Concluido\n');out:close();M:exit()
 end
end
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick);if not ok then out:write('ERRO '..tostring(err)..'\n');out:flush();M:exit() end end)
