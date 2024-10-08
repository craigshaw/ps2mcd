import array
import struct

from directory import DirectoryEntry

EXPECTED_FILE_IDENTIFIER = "Sony PS2 Memory Card Format "
SUPERBLOCK_SIZE = 340
DIRECTORY_SIZE = 512
VALID_PAGE_SIZES = [512,1024]
ECC_SIZE = 16

class UnsupportedFileTypeError(Exception):
    pass

class PS2MC():
    def __init__(self, path):
        self.path = path

        with open(path, mode='rb') as file:
            self.img = file.read()

        # Unpack the superblock
        self._unpack_superblock()
        
        # Validate the card
        self._validate()

        # Extract the FAT
        self.fat = self._flatten_fat()

        # Enumerate all files on the card
        self.files = self._enumerate_all_files()

    def __str__(self):
        return f'Card: {self.path}\nSize: {len(self.img)} bytes\nPage size: {self.page_size} bytes\nCluster size: {self.cs} bytes\n' \
            f'Total files: {len(self.files)}\n' + ''.join([f'{f}\n' for f in self.files])
    
    def _unpack_superblock(self):
        sb = struct.unpack('<28s12sHHHHIIIIII8x128s128sBBH', self.img[:SUPERBLOCK_SIZE])

        self.identifier = sb[0].decode('UTF-8').rstrip('\x00')
        self.page_size = sb[2]
        self.pages_per_cluster = sb[3]
        self.pages_per_block = sb[4]
        self.clusters_per_card = sb[6]
        self.alloc_offset = sb[7]
        self.alloc_end = sb[8]
        self.dir_root = sb[9]
        self.ifc_table = array.array('I', sb[12])

        # Calculate the cluster size
        self.cs = self.page_size * self.pages_per_cluster

        # Work out whether we've got a card with ECCs
        self.ecc_len = 0 if len(self.img) / self.cs == self.clusters_per_card else ECC_SIZE

    def _validate(self):
        # Validate what we've got
        if self.identifier != EXPECTED_FILE_IDENTIFIER:
            raise UnsupportedFileTypeError("File is not a valid PS2 memory card image")

        if self.page_size not in VALID_PAGE_SIZES or \
           self.page_size == 512 and not (self.pages_per_cluster == 1 or self.pages_per_cluster == 2) or \
           self.page_size == 1024 and self.pages_per_cluster != 1:
               raise UnsupportedFileTypeError("Unsupported memory card geometry")

    def _flatten_fat(self):
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
    
    def _enumerate_all_files(self):
        files=[]
        self._read_files_recursive(files, self.dir_root, '')
        return files
    
    def _read_files_recursive(self, files, cluster_num, path, length=0):
        dirs = self._read_directory_entries(cluster_num, path, length)
        for d in dirs:
            if d.is_file() and d.in_use():
                files.append(d)
            elif d.is_dir() and d.name != '.' and d.name != '..' and d.in_use():
                self._read_files_recursive(files, d.cluster, f'{path}{d.name}/', d.length)

    def _read_directory_entries(self, first_cluster_num, path, length):
        rd = self._read_file_starting_at_cluster(first_cluster_num)
        return self._unpack_directory_entries(rd, path, length)
    
    def _read_file_starting_at_cluster(self, cluster_num):
        fat_idx = cluster_num

        # Read first cluster
        d = self._read_allocatable_cluster(cluster_num)

        # Now go through the FAT pulling each cluster until we hit an FF entry
        while self.fat[fat_idx] != 0xFFFFFFFF:
            next_cluster_num = (self.fat[fat_idx] & 0x7FFFFFFF)
            d += self._read_allocatable_cluster(next_cluster_num)
            fat_idx = next_cluster_num

        return d
    
    def _unpack_directory_entries(self, dbuffer, path, length):
        dirs = []

        if length == 0:
            length = struct.unpack_from('<I', dbuffer, 4)[0]

        for i in range(length):
            dir = self._unpack_directory_entry(dbuffer[(i*DIRECTORY_SIZE):(i*DIRECTORY_SIZE)+DIRECTORY_SIZE])

            if dir[7].decode('UTF-8').rstrip('\x00') != '':
                dirs.append(DirectoryEntry(dir, path))
            
        return dirs
    
    def _unpack_directory_entry(self, b):
        # Expects a 512 byte buffer
        return struct.unpack('<H2xI8sII8sH30x32s416x', b)
    
    def _read_allocatable_cluster(self, offset):
        o1 = (self.alloc_offset * (self.cs + (self.ecc_len*self.pages_per_cluster))) + (offset * (self.cs + (self.ecc_len*self.pages_per_cluster)))
        
        return self._read_cluster_from(o1)
    
    def _read_absolute_cluster(self, cluster_num):
        o1 = (cluster_num * (self.cs + (self.ecc_len*self.pages_per_cluster)))

        return self._read_cluster_from(o1)
    
    def _read_cluster_from(self, offset):
        o1 = offset

        buffer = bytes()

        for i in range(self.pages_per_cluster):
            buffer += self.img[o1:o1+self.page_size]
            o1 += self.page_size + self.ecc_len

        return buffer
    
    def _read_file(self, file):
        f = self._read_file_starting_at_cluster(file.cluster)

        return f[:file.length]
    
    def write_all_to_disk(self, dir):
        for f in self.files:
            contents = self._read_file(f)

            path = dir / f.to_path()

            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open(mode='wb') as fd:
                fd.write(contents)