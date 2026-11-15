from pathlib import Path
import struct
import sys
import zlib

path=Path(sys.argv[1])
decoder=zlib.decompressobj()
record_size=4+(0xd806-0xd000+1)+(0xffff-0xe000+1)
pending=b''
frames=0
with path.open('rb') as stream:
    while chunk:=stream.read(65536):
        pending+=decoder.decompress(chunk)
        size=len(pending)//record_size*record_size
        for offset in range(0,size,record_size):
            frame=struct.unpack_from('<I',pending,offset)[0]
            assert frame==frames+1,(frames,frame)
            frames=frame
        pending=pending[size:]
print(f'{path}: {frames} quadros consecutivos; stream_finalizado={decoder.eof}; bytes_pendentes={len(pending)}')
