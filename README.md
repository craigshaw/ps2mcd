# ps2mcd
ps2mcd is a command line tool that extracts save files from PS2 memory card images, making it easy to back up, transfer or hack your game saves

### Notes
Will work with raw memory card images complete with ECCs (error correction codes) and with memory card images without ECCs, such as those generated by the 8BitMods MemCard PRO2. Have tested with card images generated from this device and those generated by PCSX2.

Creates a folder in the working directory or at a specified location, named after the provided memory card. All directories and files from the card are then written into this folder.

### Usage Instructions
```bash
usage: ps2mcd.py [-h] [-d DIR] [-l] vmc

positional arguments:
  vmc                Path to PS2 memory card image to be dumped

optional arguments:
  -h, --help         Show help
  -d DIR, --dir DIR  Directory to output dumped files to. If not provided, save files will be extracted to a directory under the working directory with the name of the memory card being dumped
  -l, --list         List files on VMC only, don't dump them to disk
  -v, --version      show program's version number and exit
  ```

### Examples
List the files on the memory card image, `SLUS-21284-1.mc2`
```
$ ./ps2mcd.py -l SLUS-21274-1.mc2
Card: SLUS-21274-1.mc2
Size: 8388608 bytes
Page size: 512 bytes
Cluster size: 1024 bytes
Total files: 6
64302      Dec 31 1999 15:02:02    Dec 31 1999 15:02:03    BASLUS-21274\icon.ico
64302      Dec 31 1999 15:02:03    Dec 31 1999 15:02:04    BASLUS-21274\copy.ico
64302      Dec 31 1999 15:02:04    Dec 31 1999 15:02:05    BASLUS-21274\del.ico
512        Dec 31 1999 15:02:05    Jul 22 2024 19:11:32    BASLUS-21274\BASLUS-21274
1305700    Dec 31 1999 15:02:06    Jul 22 2024 19:11:32    BASLUS-21274\data
964        Jul 22 2024 19:11:33    Jul 22 2024 19:11:33    BASLUS-21274\icon.sys
```
This command lists all files on the memory card image `SLUS-21284-1.mc2`, displaying each file's size, creation date, last modified date, and file path
***
Dump the files on the memory card image, `Mcd001.ps2`, to a folder under the current directory
```bash
$ ./python.py ps2mcd.py Mcd001.ps2
```
This command extracts all the directories and files from `Mcd001.ps2` and saves them in a new folder named `Mcd001` created under the current working directory.  
***
Dump the files on the memory card image, `MemoryCard1-1.mc2`, to a specific directory
```bash
$ ./python.py ps2mcd.py MemoryCard1-1.mc2 -d ~/Projects/PS2
```
This command extracts all the directories and files from `MemoryCard1-1.mc2` and saves them in a new folder named `~/Projects/PS2/MemoryCard1-1` 
