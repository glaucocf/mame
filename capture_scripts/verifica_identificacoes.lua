local M=manager.machine
local mem=M.devices[':maincpu'].spaces.program
local dest=os.getenv('DEST')
local out=assert(io.open(dest..'/identificacoes_verificacao.txt','w'))
local n=0
local function check(condition,message) assert(condition,message);out:write('OK '..message..'\n');out:flush() end
local function tick()
 n=n+1
 if n~=5 then return end
 local file=assert(io.open('cheat/'..emu.romname()..'.xml','r'));local content=file:read('a');file:close()
 local definitions=require('cheat/cheat_xml').conv_cheat(content)
 local byname={};for _,definition in ipairs(definitions) do byname[definition.desc]=definition end
 local consult=assert(byname['Editor - consultar registro'])
 check(consult.parameter.item[0x2e+1].text:find('pool pequenos',1,true)~=nil,'consulta identifica o pool 2E-3D')
 check(consult.parameter.item[0x4e+1].text:find('abertura/grande',1,true)~=nil,'consulta identifica slot reutilizado')
 mem:write_u8(0xf748,0x10);mem:write_u8(0xf747,7);mem:write_u8(0xf755,0xf7);mem:write_u8(0xe207,4)
 mem:write_u16(0xf75c,0x5a59);mem:write_u16(0xf75e,0x8a70)
 local before=mem:read_range(0xe000,0xffff,8)
 local outputs={}
 local function execute(name,param)
  local definition=assert(byname[name]);check(not definition.script.on and not definition.script.change and not definition.script.off,'consulta sem acoes de alteracao: '..name)
  local env={maincpup=mem,screen=M.screens[':screen'],ui={},param=param,draw_text=function(ui,align,line,color,format,...) outputs[#outputs+1]=string.format(format,...) end}
  assert(load(definition.script.run,name,'t',env))()
 end
 execute('Editor - investigar pequenos (ref.1943h10111)',0x3a)
 execute('Editor - consultar contador de grupo',7)
 execute('Editor - referencias graficas identificadas',0x640)
 check(mem:read_range(0xe000,0xffff,8)==before,'consultas deixam a memoria intacta')
 local lines=table.concat(outputs,'\n');out:write(lines..'\n')
 check(lines:find('Contador E200+grupo: 4',1,true)~=nil,'leitura encadeada do contador correta')
 check(lines:find('Marca especial +15: F7',1,true)~=nil,'marca especial correta')
 check(lines:find('Referencia grafica: 640',1,true)~=nil or lines:find('Grafico de referencia: 640',1,true)~=nil,'referencia grafica correta')
 for index,name in pairs(emu.plugin.cheat.list()) do
  if name=='Editor - investigar pequenos (ref.1943h10111)' then local cheat=emu.plugin.cheat.get(index);check(not cheat.get_enabled(),'nova consulta inicia desligada');cheat.set_index(13) end
 end
 out:write('Concluido\n');out:close();M:exit()
end
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick);if not ok then out:write('ERRO '..tostring(err)..'\n');out:flush();M:exit() end end)
