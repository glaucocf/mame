local M=manager.machine
local cpu=M.devices[':maincpu']
local mem=cpu.spaces.program
local dest=os.getenv('DEST')
local limit=tonumber(os.getenv('FRAMES')) or 450000
local n,bank,layer,control,dma_seq=0,0,0,0,0
local closed=false
local stage,stage_start=0,0
local visited={}
local ending_frame=nil
local firing=false
local sweeping=false
local next_instance=0
local instances={}
local pending={}
local writers={}
local previous_graphics={}
local births=0
local events=assert(io.open(dest..'/eventos.csv','w'))
events:write('quadro,evento,fase,valor,pc,banco\n')
local objects=assert(io.open(dest..'/objetos.csv','w'))
objects:write('quadro,tipo,instancia,registro,endereco,anterior,novo,pc,banco,ix,iy,hl,de,bc,sp,bytes_no_evento,bytes_no_quadro_seguinte\n')
local graphics=assert(io.open(dest..'/graficos.csv','w'))
graphics:write('quadro,dma,registro,codigo,paleta,x,y,pc,banco,ix,iy,instancia\n')
local ram=assert(io.open(dest..'/ram.zlib','wb'))
local dma=assert(io.open(dest..'/dma.zlib','wb'))
local compress_ram=require('zlib').deflate(3)
local compress_dma=require('zlib').deflate(3)
local function emit(file,compress,data,flush) local packed=compress(data,flush or 'none');file:write(packed) end
local function hex(data) return (data:gsub('.',function(char) return string.format('%02X',char:byte()) end)) end
local function regs() return cpu.state.PC.value,cpu.state.IX.value,cpu.state.IY.value,cpu.state.HL.value,cpu.state.DE.value,cpu.state.BC.value,cpu.state.SP.value end
local function event(kind,value)
 events:write(string.format('%d,%s,%d,%s,%04X,%d\n',n,kind,mem:read_u8(0xe450),value or '',cpu.state.PC.value,bank))
end
local function shot() assert(not M.screens[':screen']:snapshot(dest..string.format('/f%07d.png',n))) end
local function pad(port,mask,on)
 for _,field in pairs(M.ioport.ports[port].fields) do if field.mask==mask then field:set_value(on and 1 or 0);return end end
 error('controle ausente '..port)
end
local function status(done)
 local file=assert(io.open(dest..'/status.txt','w'))
 file:write(string.format('quadro=%d\nfase_id=%d\nnascimentos_candidatos=%d\ndma=%d\ntiro=%s\nconcluido=%s\n',n,stage,births,dma_seq,tostring(firing),done or 'em_andamento'));file:close()
end
local function finish(reason)
 event(reason);closed=true
 M:save(dest..'/continuar.sta')
 emit(ram,compress_ram,'','finish');emit(dma,compress_dma,'','finish')
 ram:close();dma:close();events:close();objects:close();graphics:close();status(reason);M:exit()
end
banktap=mem:install_write_tap(0xc804,0xc804,'catalogo_banco',function(address,data) bank=(data&0x1c)>>2;control=data end)
layertap=mem:install_write_tap(0xd806,0xd806,'catalogo_camadas',function(address,data) if not closed and data~=layer then layer=data;event('camadas',string.format('%02X',data)) end end)
soundtap=mem:install_write_tap(0xc800,0xc800,'catalogo_som',function(address,data) if not closed and data~=0 and data~=0xff then event('som',string.format('%02X',data)) end end)
weapontap=mem:install_write_tap(0xf251,0xf251,'catalogo_arma',function(address,data)
 if not closed and data~=mem:read_u8(address) then
  event('arma',string.format('%02X',data))
  if data==0x10 or data==0x50 then event('candidato_laser',string.format('%02X',data)) end
 end
end)
local function group_tap(address,data)
 if not closed and data~=mem:read_u8(address) then event('grupo_'..string.format('%04X',address),string.format('%02X',data)) end
end
grouptap=mem:install_write_tap(0xe200,0xe20f,'catalogo_grupos',group_tap)
flagtap=mem:install_write_tap(0xe133,0xe133,'catalogo_marca',group_tap)
objecttap=mem:install_write_tap(0xf000,0xffff,'catalogo_objetos',function(address,data)
 if closed or n<360 then return end
 local slot=(address-0xf000)//32
 local field=address%32
 if field==0 or field==1 then
  local pc,ix,iy=regs();writers[slot]={pc=pc,bank=bank,ix=ix,iy=iy}
 end
 if field~=8 and field~=0x1c and field~=0x1d then return end
 local before=mem:read_u8(address)
 if before==data then return end
 local kind='referencia_1C'
 if field==8 then
  kind='estado_08'
  if before==0 and data~=0 then next_instance=next_instance+1;instances[slot]=next_instance;kind='nascimento_candidato';births=births+1
  elseif before~=0 and data==0 then kind='liberacao_candidata' end
 end
 local pc,ix,iy,hl,de,bc,sp=regs()
 local base=0xf000+slot*32
 local bytes=mem:read_range(base,base+31,8)
 bytes=bytes:sub(1,field)..string.char(data)..bytes:sub(field+2)
 pending[#pending+1]={frame=n,kind=kind,id=instances[slot] or 0,slot=slot,address=address,before=before,new=data,pc=pc,bank=bank,ix=ix,iy=iy,hl=hl,de=de,bc=bc,sp=sp,bytes=hex(bytes)}
end)
dmatap=mem:install_write_tap(0xc806,0xc806,'catalogo_dma',function()
 if closed then return end
 dma_seq=dma_seq+1
 local bytes=mem:read_range(0xf000,0xffff,8)
 emit(dma,compress_dma,string.pack('<I4I4I1I1I1',n,dma_seq,bank,layer,control)..bytes,dma_seq%60==0 and 'sync' or 'none')
 if n<360 then return end
 for slot=0,127 do
  local offset=slot*32
  local code_low,attr,y,x=bytes:byte(offset+1,offset+4)
  local code=code_low+((attr&0xe0)<<3)
  local writer=writers[slot] or {pc=0,bank=0,ix=0,iy=0}
  local signature=string.pack('<I2I1I2I2',code,attr&15,writer.ix,writer.iy)
  if signature~=previous_graphics[slot] then
   graphics:write(string.format('%d,%d,%02X,%03X,%X,%d,%d,%04X,%d,%04X,%04X,%d\n',n,dma_seq,slot,code,attr&15,x-((attr&16)<<4),y,writer.pc,writer.bank,writer.ix,writer.iy,instances[slot] or 0))
   previous_graphics[slot]=signature
  end
 end
end)
local function tick()
 if closed then return end
 n=n+1
 for _,item in ipairs(pending) do
  local base=0xf000+item.slot*32
  objects:write(string.format('%d,%s,%d,%02X,%04X,%02X,%02X,%04X,%d,%04X,%04X,%04X,%04X,%04X,%04X,%s,%s\n',item.frame,item.kind,item.id,item.slot,item.address,item.before,item.new,item.pc,item.bank,item.ix,item.iy,item.hl,item.de,item.bc,item.sp,item.bytes,hex(mem:read_range(base,base+31,8))))
 end
 pending={}
 emit(ram,compress_ram,string.pack('<I4',n)..mem:read_range(0xd000,0xd806,8)..mem:read_range(0xe000,0xffff,8),n%60==0 and 'sync' or 'none')
 pad(':SYSTEM',64,n>=300 and n<305);pad(':SYSTEM',1,n>=360 and n<365)
 mem:write_u8(0xf214,2)
 local energy=mem:read_u8(0xf206)
 if energy>0 and energy<12 then event('protecao_energia',energy);mem:write_u8(0xf206,32) end
 local current=mem:read_u8(0xe450)
 if current~=stage then
  event('fase',current)
  if (stage==15 or stage==16) and current==0 and visited[15] then
   local count=0;for _ in pairs(visited) do count=count+1 end
   if count==16 then ending_frame=n;event('retorno_apos_final') end
  end
  stage=current;stage_start=n
  M:save(dest..string.format('/fase_%02d_f%07d.sta',stage,n));shot()
 end
 if n>400 and stage<16 then visited[stage]=true end
 if stage==15 and n-stage_start>=17000 and not firing then firing=true;event('intervencao_tiro_final');mem:write_u8(0xf251,4) end
 pad(':P1',16,firing and n%6<3)
 if firing then mem:write_u8(0xf257,0x63);mem:write_u8(0xf254,0xf8);mem:write_u8(0xf256,0) end
 local sweep=firing and stage==15 and n-stage_start>=28000
 if sweep and not sweeping then sweeping=true;event('intervencao_varredura_final') end
 pad(':P1',1,sweep and (n//120)%2==0);pad(':P1',2,sweep and (n//120)%2==1)
 if n%4==0 then shot() end
 if n%600==0 then M:save(dest..string.format('/checkpoint_f%07d.sta',n)) end
 if n%60==0 then event('amostra',energy);events:flush();objects:flush();graphics:flush();status() end
 if ending_frame and n-ending_frame>=120 then finish('campanha_concluida') elseif n>=limit then finish('limite_do_trecho') end
end
sub=emu.add_machine_frame_notifier(function()
 local ok,err=pcall(tick)
 if not ok and not closed then event('erro',tostring(err):gsub(',',';'));finish('erro_fatal') end
end)
