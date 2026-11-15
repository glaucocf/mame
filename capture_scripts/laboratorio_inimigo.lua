-- First isolated enemy: real campaign checkpoint, native HP and collision paths.
local M=manager.machine
local cpu=M.devices[':maincpu'];local mem=cpu.spaces.program
local ram=assert(M.memory.shares[':spriteram'])
local cfg=dofile(assert(os.getenv('LAB_CONFIG')))
local target=cfg.target;local dest=cfg.dest;local kai=cfg.engine==1
local parts={[target]=true}
if cfg.routine=='alvo_multisprite'then for a=target,target+0x60,32 do parts[a]=true end
elseif cfg.routine=='alvo_grande'then for a=target-0x80,target+0x160,32 do parts[a]=true end end
local n=0;local state='start';local closed=false;local own=false
local pinned=true;local protected=true;local hostile_enabled=true;local retired=false
local hold_x,hold_y=176,112;local original=nil;local own_bullets={}
local blocked=0;local deaths=0;local shots=0;local reloads=0;local hits=0
local moving=false;local replaced=false;local origin_x,origin_y=nil,nil
local last_layers=0x40;local effective_layers=0x40
local weapons=kai and {0,1,2,3,4,8,0x10,0x30,0x50}or{0,1,2,3,4,8,0x10}
local weapon_index=1;local snapshot_hit=nil;local last_status=0
local frames=cfg.frames or 0;local automatic=cfg.automatic or false
local log=assert(io.open(dest..'/quadros.csv','w'))
log:write('quadro,estado_alvo,hp,codigo,x,y,posicao_fixa,outros_inimigos,tiros_inimigo,camadas,energia,invulneravel\n')
local events=assert(io.open(dest..'/eventos.csv','w'))
events:write('quadro,evento,endereco,antes,depois,pc,ix,iy\n')
local function peek(a)return ram:read_u8(a-0xf000)end
local function poke(a,v)ram:write_u8(a-0xf000,v&255)end
local function word(a)return peek(a)+256*peek(a+1)end
local function code(a)return peek(a)+((peek(a+1)&0xe0)<<3)end
local function event(kind,a,b,c)
 events:write(string.format('%d,%s,%04X,%d,%d,%04X,%04X,%04X\n',n,kind,a or 0,b or 0,c or 0,cpu.state.PC.value,cpu.state.IX.value,cpu.state.IY.value));events:flush()
end
local function status(result)
 local f=assert(io.open(dest..'/status.txt','w'))
 f:write(string.format('rom=%s\nquadro=%d\nestado=%s\nalvo=%04X\nhp=%d\ncamadas=%02X\ncriacao_bloqueada=%d\nimpactos=%d\n',cfg.rom,n,result or state,target,peek(target+11),effective_layers,blocked,hits));f:close()
end
local function button(mask,on)
 for _,f in pairs(M.ioport.ports[':P1'].fields)do if f.mask==mask then f:set_value(on and 1 or 0);return end end
end
local function clear_record(base)
 for o=0,31 do poke(base+o,0)end
 poke(base+1,0x10) -- offscreen X=-256; inactive even if graphic zero is opaque.
end
local function summary(result)
 local f=assert(io.open(dest..'/validacao.json','w'))
 f:write(string.format('{"resultado":%q,"rom":%q,"quadros":%d,"hp_inicial":%d,"criacao_bloqueada":%d,"impactos":%d,"colisao_confirmada":%s,"movimento_confirmado":%s,"reposicao_confirmada":%s,"projeteis_do_alvo":%d,"recargas":%d}\n',result,cfg.rom,n,original and original:byte(12)or 0,blocked,hits,tostring(hits>0),tostring(moving),tostring(replaced),shots,reloads));f:close()
end
local function finish(result)
 if closed then return end
 closed=true;status(result);summary(result);log:close();events:close()
 if automatic then M:exit()end
end
local function load_initial(reason)
 if state=='loading'then return end
 reloads=reloads+1;event(reason or 'recriar',target,0,reloads);state='loading';M:load(cfg.checkpoint)
end
local function initialize()
 assert(word(target+28)==cfg.reference,'referencia do alvo diferente do catalogo')
 assert(peek(target+11)==(cfg.hp or 1)and peek(target+8)~=0,'save sem o alvo e HP esperados')
 original=original or mem:read_range(target,target+31,8)
 own=true;own_bullets={};retired=false
 for base=0xf000,0xffe0,32 do
  if not(base>=0xf200 and base<0xf300)and base~=target then
   if parts[base]then for o=8,31 do poke(base+o,0)end else clear_record(base)end
  end
 end
 -- Aim along the player's real firing line, without altering collision reads.
 hold_y=peek(0xf222);if hold_y<16 or hold_y>220 then hold_y=112 end
 hold_y=hold_y+(cfg.routine=='alvo_multisprite'and -8 or cfg.routine=='alvo_grande'and 8 or 0)
 if pinned then poke(target+2,hold_y);poke(target+3,hold_x);poke(target+1,peek(target+1)&0xef);poke(target+5,0);poke(target+6,0)end
 poke(0xf214,protected and 2 or 0);poke(0xf206,64)
 poke(0xf250,0);poke(0xf251,weapons[weapon_index]);poke(0xf257,0x63)
 for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
 mem:write_u8(0xd806,0x40)
 -- The CHAR layer is separate. Hide it for a clear inspection screen.
 -- Bank is selected by game code; the C804 tap preserves every bit except 80.
 own=false;state='running'
 if reloads>1 then replaced=true end
 event('alvo_pronto',target,peek(target+8),peek(target+11));status()
end
local keys={}
for _,k in ipairs({'R','M','I','T','N'})do keys[k]=M.input:code_from_token('KEYCODE_'..k)end
post=emu.add_machine_post_load_notifier(function()if state=='loading'then initialize()end end)
layer_tap=mem:install_write_tap(0xd806,0xd806,'laboratorio_camadas',function(a,d)
 last_layers=d;effective_layers=0x40;return 0x40
end)
control_tap=mem:install_write_tap(0xc804,0xc804,'laboratorio_caracteres',function(a,d)return d&0x7f end)
write_tap=mem:install_write_tap(0xf000,0xffff,'laboratorio_isolamento',function(a,d)
 if state~='running'or own or closed then return end
 local base=a&0xffe0;local offset=a&31;local before=peek(a)
 if base>=0xf200 and base<0xf5c0 then return end -- player, player 2 and shot pools.
 if base==target then
  if retired then return before end
  if offset==11 and d<before then
   hits=hits+1;event('hp_reduzido',a,before,d);snapshot_hit=n+1
   if d==0 then deaths=deaths+1 end
  end
  if offset==8 and d==0 then retired=true;event('alvo_retirado',a,before,d)end
  if pinned and peek(target+11)>0 then
   if offset==2 then return hold_y elseif offset==3 then return hold_x
   elseif offset==5 or offset==6 then return 0
   elseif offset==1 then return d&0xef end
  end
  return
 end
 if parts[base]and offset<8 and cpu.state.IX.value==target then return end
 if base<0xf200 then
  local pc=cpu.state.PC.value
  if hostile_enabled and not retired and cpu.state.IX.value==target and cpu.state.IY.value==base and pc>=2 and mem:read_u8(pc-2)==0xed and mem:read_u8(pc-1)==0xb0 and not own_bullets[base]then
   own_bullets[base]=true;shots=shots+1;event('projetil_do_alvo',base,0,1)
  end
  if own_bullets[base]then return end
 end
 if offset==8 and d~=0 and before==0 then blocked=blocked+1 end
 return before
end)
local function count_others()
 local enemies,bullets=0,0
 for base=0xf000,0xffe0,32 do
  if not(base>=0xf200 and base<0xf5c0)and base~=target and peek(base+8)~=0 then
   if own_bullets[base]then bullets=bullets+1 else enemies=enemies+1 end
  end
 end
 return enemies,bullets
end
local function snapshot(name)assert(not M.screens[':screen']:snapshot(dest..'/'..name..'.png'))end
local function tick()
 if closed then return end
 if state=='start'then load_initial('carregar');return end
 if state~='running'then return end
 n=n+1
 if automatic then
  for _,mask in ipairs({1,2,4,8,16,32})do button(mask,false)end
  if n==121 then pinned=false;origin_x=peek(target+3);origin_y=peek(target+2);event('movimento_livre',target,origin_x,origin_y)end
  if n>121 and n<181 and(peek(target+3)~=origin_x or peek(target+2)~=origin_y)then moving=true end
  if n==181 or n==360 then pinned=true;load_initial('recriar_automatico');return end
  if n>=200 and n<=300 then button(16,true)end
 else
  if M.input:code_pressed_once(keys.R)then load_initial('recriar_tecla_R');return end
  if M.input:code_pressed_once(keys.M)then
   pinned=not pinned
   if pinned then hold_x=peek(target+3);hold_y=peek(target+2)end
   event('posicao_fixa',target,0,pinned and 1 or 0)
  end
  if M.input:code_pressed_once(keys.I)then protected=not protected end
  if M.input:code_pressed_once(keys.T)then
   hostile_enabled=not hostile_enabled
   if not hostile_enabled then for base in pairs(own_bullets)do clear_record(base)end;own_bullets={}end
  end
  if M.input:code_pressed_once(keys.N)then weapon_index=weapon_index%#weapons+1 end
 end
 poke(0xf251,weapons[weapon_index]);poke(0xf257,0x63)
 poke(0xf214,protected and 2 or 0)
 if peek(0xf206)>0 and peek(0xf206)<12 then poke(0xf206,32)end
 for base in pairs(own_bullets)do
  if peek(base+8)==0 then clear_record(base);own_bullets[base]=nil end
 end
 if retired then for base in pairs(parts)do poke(base+1,peek(base+1)|0x10);poke(base+3,0)end end
 mem:write_u8(0xd806,0x40)
 local others,bullets=count_others()
 assert(others==0,'objeto nao selecionado ativo')
 log:write(string.format('%d,%02X,%d,%03X,%d,%d,%d,%d,%d,%02X,%d,%d\n',n,peek(target+8),peek(target+11),code(target),peek(target+3),peek(target+2),pinned and 1 or 0,others,bullets,effective_layers,peek(0xf206),peek(0xf214)))
 if n==30 or n==150 or n==390 then snapshot(string.format('quadro_%04d',n))end
 if snapshot_hit and n==snapshot_hit then snapshot('impacto_natural');snapshot_hit=nil end
 if n-last_status>=60 then last_status=n;log:flush();status()end
 if frames>0 and n>=frames then finish('ok')end
end
frame=emu.add_machine_frame_notifier(function()
 local ok,err=pcall(tick)
 if not ok then
  local f=assert(io.open(dest..'/erro.txt','w'));f:write(tostring(err));f:close();finish('erro');M:exit()
 end
end)
stop=emu.add_machine_stop_notifier(function()finish('encerrado')end)
emu.register_frame_done(function()
 if state~='running'or closed then return end
 local ui=M.render.ui_container;local hp=peek(target+11)
 local title=cfg.routine and('ALVO '..cfg.model)or'AVIAO PEQUENO'
 ui:draw_text('left',0.01,string.format('%s | HP %d | ARMA %02X',title,hp,weapons[weapon_index]),0xffffffff,0xc0000000)
 ui:draw_text('left',0.055,string.format('BG OFF | POSICAO %s | PROTECAO %s',pinned and 'FIXA'or'LIVRE',protected and 'ON'or'OFF'),0xffffff00,0xc0000000)
 ui:draw_text('left',0.88,'R recriar | M movimento | I protecao',0xffffffff,0xc0000000)
 ui:draw_text('left',0.93,'N arma | T tiros inimigos | ESC sair',0xffffffff,0xc0000000)
end)
