local M=manager.machine
local mem=M.devices[":maincpu"].spaces["program"]
local dest=os.getenv("DEST")
local mode=os.getenv("MODE")
local out=assert(io.open(dest.."/quadros.txt","w"))
local n=0
local function set(p,mask,v)
 for _,field in pairs(M.ioport.ports[":P"..p].fields) do
  if field.mask==mask then field:set_value(v and 1 or 0); return end
 end
 error("controle ausente")
end
local function snap(name)
 local screen=M.screens[":screen"]
 local err=screen:snapshot(dest.."/"..name..".png")
 assert(not err,tostring(err))
end
local function calibrate()
 n=n+1
 if n<40 then mem:write_u8(0xe835,7) end
 set(1,16,n>=20 and n<23)
 set(2,32,n>=100 and n<103)
 set(1,8,n>=140 and n<160)
 set(2,8,n>=140 and n<160)
 if n%10==0 then
 out:write(string.format("%d %02X %04X %02X %04X\n",n,mem:read_u8(0xe835),mem:read_u16(0xd800),mem:read_u8(0xd802),mem:read_u16(0xd803)));out:flush()
 end
 if n==10 or n==90 or n==130 or n==170 then snap("f"..n) end
 if n==180 then M:exit() end
end
local function scroll()
 n=n+1
 if n<40 then mem:write_u8(0xe835,7) end
 set(1,16,n>=20 and n<23)
 set(2,32,n>=100 and n<103)
 set(2,16,(mode~="upper_lower" and n>=70 and n<73) or (mode=="upper_only" and n>=83 and n<86))
 if n<140 then return end
 local idx=(n-140)//136
 local phase=(n-140)%136
 local count=idx==511 and 127 or 128
 set(1,4,phase<count)
 set(2,4,phase<count)
 if phase==0 then
  local pos=math.min(idx*128,65535)
  local a,b=mem:read_u16(0xd800),mem:read_u16(0xd803)
  assert(a==(mode=="lower_only" and 0 or pos) and b==(mode=="upper_only" and 0 or pos),string.format("posicao %04X: UPPER %04X LOWER %04X",pos,a,b))
  local name=string.format("%04X",pos)
  snap(name)
  out:write(string.format("%s.png,%d,%04X,%04X\n",name,n,a,b));out:flush()
  if idx==512 then M:exit() end
 end
end
local function inspect()
 n=n+1
 local code=({obj=6,chr=4,service=8})[mode]
 if n<40 then mem:write_u8(0xe835,code) end
 set(1,16,n>=20 and n<23)
 if mode=="service" then
  if n>=18 then snap(string.format("f%04d",n)) end
  if n==600 then M:exit() end
 else
  set(1,4,n>=100 and n<103)
  set(1,1,n>=120 and n<123)
  if n==90 or n==115 or n==135 then
   snap("f"..n)
   local v=assert(io.open(dest.."/v"..n..".bin","wb"))
   for i=0xd000,0xd3ff do v:write(string.char(mem:read_u8(i))) end
   v:close()
   for i=0xe800,0xe86f do out:write(string.format("%02X ",mem:read_u8(i))) end
   out:write("\n");out:flush()
  end
  if n==140 then M:exit() end
 end
end
local target=0
local stable=0
local tries=0
local function pages()
 n=n+1
 local obj=mode=="object_test"
 if n<40 then mem:write_u8(0xe835,obj and 6 or 4) end
 set(1,16,n>=20 and n<23)
 if n<90 then return end
 local per=obj and 32 or 8
 local pal,page=target//per,target%per
 local actualpage=obj and (mem:read_u8(0xd0b8)*4+mem:read_u8(0xd0f8)//4) or mem:read_u8(0xd1d9)
 local actualpal=obj and mem:read_u8(0xd0fb) or (mem:read_u8(0xd1ba)*16+mem:read_u8(0xd1da))
 local right=actualpal~=pal
 local up=not right and actualpage~=page
 if right or up then
  stable=0
  tries=tries+1
  assert(tries<800,string.format("alvo %d/%d tela %d/%d",pal,page,actualpal,actualpage))
 else stable=stable+1 end
 set(1,8,up and n%16<5)
 set(1,1,right and n%16<5)
 if stable==10 then
  local name=string.format("pal_%02X/%s_%03X",pal,obj and "sprite" or "banco",obj and page*64 or page)
  snap(name);out:write(string.format("%s.png,%d\n",name,n));out:flush()
  target=target+1;stable=0;tries=0
  if target==(obj and 512 or 256) then M:exit() end
 end
end
local action=mode:find("upper") or mode=="lower_only"
local catalog=mode=="object_test" or mode=="vram_character_code"
local tick=action and scroll or catalog and pages or (mode=="calibracao" and calibrate or inspect)
sub=emu.add_machine_frame_notifier(function() local ok,err=pcall(tick); if not ok then out:write(tostring(err));out:flush();M:exit() end end)
