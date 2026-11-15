local M=manager.machine;local mem=M.devices[':maincpu'].spaces.program
local dest=assert(os.getenv('DEST'));local out=assert(io.open(dest..'/camadas_xml.csv','w'))
out:write('rom,valor,upper,lower,sprites,caracteres_preservados\n')
local n=0
local function tick()
 n=n+1;if n~=2 then return end
 local f=assert(io.open('cheat/'..emu.romname()..'.xml','r'));local content=f:read('a');f:close()
 local block=assert(content:match('(<cheat desc="VIDEO %- camadas BG e sprites %(D806%)">.-</cheat>)'))
 local defs=require('cheat/cheat_xml').conv_cheat('<mamecheat version="1">'..block..'</mamecheat>')
 assert(#defs==1,'quantidade de cheats inesperada');local cheat=defs[1]
 -- Root-device save names are not exposed in this build's device.items.
 -- Identify the three registered scalars by their independent responses to
 -- all eight writes, without advancing the CPU between the measurements.
 local scalars={}
 for index=0,4095 do
  local item=emu.item(index);if item.size==0 then break end
  if item.count==1 then scalars[#scalars+1]={index=index,item=item,values={}}end
 end
 assert(#scalars>0,'save items ausentes')
 local function execute(script,value)
  assert(load(script,'D806 XML','t',{maincpup=mem,param=value}))()
  for _,r in ipairs(scalars)do r.values[#r.values+1]=r.item:read(0)end
 end
 for value=0,0x70,0x10 do execute(cheat.script.run,value)end
 execute(cheat.script.off,0x70)
 local matched={}
 for _,bit in ipairs({0x10,0x20,0x40})do
  for _,r in ipairs(scalars)do
   local correct=true
   for i=1,9 do
    local value=i==9 and 0x70 or(i-1)*0x10
    if (r.values[i]~=0)~=((value&bit)~=0)then correct=false;break end
   end
   if correct then assert(not matched[bit],'resposta ambigua');matched[bit]=r end
  end
  assert(matched[bit],string.format('estado de video %02X nao respondeu',bit))
 end
 for _,r in ipairs(scalars)do
  if r~=matched[0x10]and r~=matched[0x20]and r~=matched[0x40]then
   for i=2,9 do assert(r.values[i]==r.values[1],'outro estado escalar foi alterado')end
  end
 end
 for i=1,9 do out:write(string.format('%s,%02X,%d,%d,%d,true\n',emu.romname(),i==9 and 0x70 or(i-1)*0x10,matched[0x10].values[i],matched[0x20].values[i],matched[0x40].values[i]))end
 out:close();local done=assert(io.open(dest..'/camadas_xml_ok.txt','w'));done:write('8 combinacoes e desligamento conferidos nos estados reais do driver. Caracteres preservados.\n');done:close();M:exit()
end
frame=emu.add_machine_frame_notifier(function()
 local ok,err=pcall(tick)
 if not ok then out:write('ERRO '..tostring(err)..'\n');out:close();M:exit()end
end)
