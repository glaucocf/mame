from pathlib import Path
for rom in ('10111','11000'):
 for mode in ('upper_lower','upper_only','lower_only','object_test','vram_character_code'):
    p=Path('captures/1943h'+rom)/mode
    log=(p/'quadros.txt').read_text().splitlines()
    print(rom,mode,len(log),log[-1:] )
