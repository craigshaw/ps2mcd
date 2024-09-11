import calendar
import time
from pathlib import Path

DF_READ = 0x0001
DF_WRITE = 0x0002
DF_EXECUTE = 0x0004
DF_PROTECTED = 0x0008
DF_FILE = 0x0010
DF_DIRECTORY = 0x0020
O_CREATE = 0x0200
DF_CREATED = 0x0400
DF_PSTATION = 0x0800
DF_PSX = 0x1000
DF_HIDDEN = 0x2000
DF_EXISTS = 0x8000

class DirectoryEntry():
    def __init__(self, dir_tuple, path):
        self.mode = dir_tuple[0]
        self.length = dir_tuple[1]
        self.created = self._to_local_time(dir_tuple[2])
        self.cluster = dir_tuple[3]
        self.dir_entry = dir_tuple[4]
        self.modified = self._to_local_time(dir_tuple[5])
        self.attr = dir_tuple[6]
        self.name = dir_tuple[7].decode('UTF-8').rstrip('\x00')
        self.path = path

    def __str__(self) -> str:
        return f'{self.length:<10} {time.strftime("%b %d %Y %H:%M:%S", self.created):<23}' \
            f' {time.strftime("%b %d %Y %H:%M:%S", self.modified):<23} {self.to_path()}'
    
    def _to_local_time(self, t) -> time.struct_time:
        # Time of Day (8 bytes)
        # Offset	Name	Type	Description
        # 0x01	    sec	    byte	seconds
        # 0x02	    min	    byte	minutes
        # 0x03	    hour	byte	hours
        # 0x04	    day	    byte	day of the month
        # 0x05	    month	byte	month (1-12)
        # 0x06	    year	word	year
        # Timestamps are in +9 UTC
        year = int.from_bytes(t[6:8], "little")
        unix_time = calendar.timegm((year, t[5], t[4], t[3], t[2], t[1])) - (9*60*60)
        return time.localtime(unix_time)

    def is_file(self) -> int:
        return self.mode & DF_FILE
    
    def is_dir(self) -> int:
        return self.mode & DF_DIRECTORY
    
    def in_use(self):
        return self.mode & DF_EXISTS
    
    def to_path(self) -> Path:
        return Path(self.path) / Path(self.name)