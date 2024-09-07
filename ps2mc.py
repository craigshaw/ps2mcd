import array
import struct

ExpectedFileHeader = "Sony PS2 Memory Card Format "

class UnsupportedFileType(Exception):
    pass

class PS2MC():
    def __init__(self, path):
        with open(path, mode='rb') as file:
            self.img = file.read()

        # Read the superblock
        sb = struct.unpack('<28s12sHHHHIIIIII8x128s128sBBH', self.img[:340])

        if sb[0].decode('UTF-8').rstrip('\x00') != ExpectedFileHeader:
            raise UnsupportedFileType("File is not a valid PS2 memory card image")
        
        self.page_len = sb[2]
        self.pages_per_cluster = sb[3]
        self.pages_per_block = sb[4]
        self.clusters_per_card = sb[6]
        self.alloc_offset = sb[7]
        self.alloc_end = sb[8]
        self.dir_root = sb[9]
        self.ifc_table = array.array('I', sb[12])

        # Calculate the cluster size
        self.cs = self.page_len * self.pages_per_cluster

    def __str__(self) -> str:
        return f'Size: {len(self.img)} bytes\npage len: {self.page_len}\ncluster size: {self.cs}\n' \
            f'ifc_table: {self.ifc_table}'