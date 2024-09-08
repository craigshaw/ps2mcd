# ps2mcd
ps2mcd is a command line tool that extracts save files from PS2 memory card images, making it easy to back up, transfer or hack your game saves

```
usage: ps2mcd.py [-h] [-d DIR] [-l] vmc

positional arguments:
  vmc                Path to PS2 memory card image to be dumped

optional arguments:
  -h, --help         Show help
  -d DIR, --dir DIR  Directory to output dumped files to. If not provided, save files will be extracted to a directory under the working directory with the name of the memory card being      
                     dumped
  -l, --list         List files on VMC only, don't dump them to disk
  ```