-- Entra no SCROLL TEST (E835 = 7) a partir do save do menu, tira as bordas e
-- fotografa a tela a cada +0x1000 de rolagem, anotando os registradores.
local SAIDA = os.getenv("SCROLL_LOG")
local quadro = 0
local mem = manager.machine.devices[":maincpu"].spaces["program"]
local log = io.open(SAIDA, "w")
local passo = 0

local function botao(porta, nome, v)
    local p = manager.machine.ioport.ports[porta]
    if p and p.fields[nome] then p.fields[nome]:set_value(v) end
end

local function regs()
    local sx = mem:read_u8(0xD800) + 256 * mem:read_u8(0xD801)
    local sy = mem:read_u8(0xD802)
    local bx = mem:read_u8(0xD803) + 256 * mem:read_u8(0xD804)
    return sx, sy, bx
end

local function cada_quadro()
    quadro = quadro + 1
    botao(":P1", "P1 Button 1", 0)
    botao(":P1", "P1 Button 2", 0)
    botao(":P2", "P2 Button 2", 0)
    if quadro <= 40 then mem:write_u8(0xE835, 7) end
    if quadro >= 20 and quadro < 26 then botao(":P1", "P1 Button 1", 1) end
    if quadro == 110 then
        local sx, sy, bx = regs()
        log:write(string.format("com_bordas %d %04X %02X %04X\n", quadro, sx, sy, bx))
        manager.machine.video:snapshot()
    end
    if quadro >= 120 and quadro < 126 then botao(":P2", "P2 Button 2", 1) end
    if quadro >= 160 then
        local f = (quadro - 160) % 30
        if f == 0 then
            local sx, sy, bx = regs()
            log:write(string.format("passo%02d %d %04X %02X %04X\n", passo, quadro, sx, sy, bx))
            manager.machine.video:snapshot()
            passo = passo + 1
            if passo > 16 then
                log:close()
                manager.machine:exit()
            end
        end
        if f >= 5 and f < 10 then botao(":P1", "P1 Button 2", 1) end
    end
end

if emu.add_machine_frame_notifier then
    assinatura_quadro = emu.add_machine_frame_notifier(cada_quadro)
else
    emu.register_frame_done(cada_quadro)
end
