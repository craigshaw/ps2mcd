import array
import struct

ExpectedFileHeader = "Sony PS2 Memory Card Format "

class UnsupportedFileTypeError(Exception):
    pass

class PS2MC():
    def __init__(self, path):
        with open(path, mode='rb') as file:
            self.img = file.read()

        # Read the superblock
        sb = struct.unpack('<28s12sHHHHIIIIII8x128s128sBBH', self.img[:340])

        if sb[0].decode('UTF-8').rstrip('\x00') != ExpectedFileHeader:
            raise UnsupportedFileTypeError("File is not a valid PS2 memory card image")
        
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

        # Extract the FAT
        self.fat = self._flatten_fat()

    def __str__(self) -> str:
        return f'Size: {len(self.img)} bytes\npage len: {self.page_len}\ncluster size: {self.cs}\n' \
            f'ifc_table: {self.ifc_table}\nfat entries: {len(self.fat)}'
    
    def _flatten_fat(self) -> list:
        fat = []

        # For each ifc table entry currently in use
        for ifc_cluster_num in [x for x in self.ifc_table if x != 0]:
            # Get the (absolute) indirect FAT cluster referenced
            ifc = self._read_absolute_cluster(ifc_cluster_num)

            # For each cluster reference in the cluster that isn't 0xFFFFFF
            for fcn_bytes in range(0, len(ifc), 4):
                fat_cluster_num = struct.unpack_from('<I', ifc, fcn_bytes)[0]

                if fat_cluster_num != 0xFFFFFFFF:
                    # Get the (absolute) FAT cluster referenced
                    fc = self._read_absolute_cluster(fat_cluster_num)

                    # Put each FAT entry in the cluster into the flattened FAT
                    for fat_entry in range(0, len(fc), 4):
                        fat.append(struct.unpack_from('<I', fc, fat_entry)[0])

        return fat
    
    def _read_absolute_cluster(self, cluster_num) -> bytes:
        o1 = (cluster_num * self.cs)
        o2 = o1 + self.cs
        return self.img[o1:o2]