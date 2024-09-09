#!/usr/bin/env python3

import argparse

from pathlib import Path
from ps2mc import PS2MC

def main():
    args = read_args()

    try:
        out_dir = set_out_dir(args)

        mc = PS2MC(args.vmc)

        if args.list:
            print(mc)
        else:
            mc.write_all_to_disk(out_dir)

    except Exception as e:
        print(f"Failed to dump files: {e}")

def set_out_dir(args) -> Path:
    if args.dir != None:    
        out_path = Path(args.dir).resolve()
    else:
        ext_idx = args.vmc.find('.')
        out_path = Path.cwd() /  Path(args.vmc[:ext_idx]) if ext_idx != -1 else Path(args.vmc)

    # Make sure it exists
    out_path.mkdir(parents=True, exist_ok=True)

    return out_path

def read_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='''ps2mcd is a command line tool that dumps save files from PS2 memory card images, making it easy to back up, 
            transfer or hack your game saves''')
    parser.add_argument('vmc', type=str, help='Path to PS2 memory card image to be dumped')
    parser.add_argument('-d', '--dir', type=str, help='''Directory to output dumped files to. If not provided, save files will be 
                        extracted to a directory under the working directory with the name of the memory card being dumped''')
    parser.add_argument('-l', '--list', action='store_true', help="List files on VMC only, don't dump them to disk")
    return parser.parse_args()

if __name__ == "__main__":
    main()