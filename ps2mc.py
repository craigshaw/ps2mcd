import array
import struct

from directory import DirectoryEntry

EXPECTED_FILE_HEADER = "Sony PS2 Memory Card Format "
SUPERBLOCK_SIZE = 340
DIRECTORY_SIZE = 512

class UnsupportedFileTypeError(Exception):
    pass

class PS2MC():
    def __init__(self, path):
        with open(path, mode='rb') as file:
            self.img = file.read()

        # Read the superblock
        sb = struct.unpack('<28s12sHHHHIIIIII8x128s128sBBH', self.img[:SUPERBLOCK_SIZE])

        if sb[0].decode('UTF-8').rstrip('\x00') != EXPECTED_FILE_HEADER:
            raise UnsupportedFileTypeError("File is not a valid PS2 memory card image")
        
        self.path = path
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

        # Extract the FAT
        self.fat = self._flatten_fat()

        # Enumerate all files on the card
        self.files = self._enumerate_all_files()

    def __str__(self) -> str:
        return f'Card: {self.path}\nSize: {len(self.img)} bytes\nPage size: {self.page_size} bytes\nCluster size: {self.cs} bytes\n' \
            f'Total files: {len(self.files)}\n' + ''.join([f'{f}\n' for f in self.files])
    
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
    
    def _enumerate_all_files(self):
        files=[]
        self._read_files_recursive(files, self.dir_root, '')
        return files
    
    def _read_files_recursive(self, files, cluster_num, path):
        dirs = self._read_directory(cluster_num, path)
        for d in dirs:
            if d.is_file():
                files.append(d)
            elif d.is_dir() and d.name != '.' and d.name != '..':
                self._read_files_recursive(files, d.cluster, f'{path}{d.name}/')

    def _read_directory(self, first_cluster_num, path):
        rd = self._read_file_starting_at_cluster(first_cluster_num)
        return self._unpack_dirs(rd, path)
    
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
    
    def _unpack_dirs(self, dbuffer, path):
        dirs = []

        for i in range(len(dbuffer)//DIRECTORY_SIZE):
            dir = self._unpack_directory_entry(dbuffer[(i*DIRECTORY_SIZE):(i*DIRECTORY_SIZE)+DIRECTORY_SIZE])
            
            if dir[7].decode('UTF-8').rstrip('\x00') != '':
                dirs.append(DirectoryEntry(dir, path))
            
        return dirs
    
    def _unpack_directory_entry(self, b):
        # Expects a 512 byte buffer
        return struct.unpack('<H2xI8sII8sH30x32s416x', b)
    
    def _read_allocatable_cluster(self, offset):
        s1 = (self.alloc_offset * self.cs) + (offset * self.cs)
        s2 = s1 + self.cs
        return self.img[s1:s2]
    
    def _read_absolute_cluster(self, cluster_num) -> bytes:
        o1 = (cluster_num * self.cs)
        o2 = o1 + self.cs
        return self.img[o1:o2]
    
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