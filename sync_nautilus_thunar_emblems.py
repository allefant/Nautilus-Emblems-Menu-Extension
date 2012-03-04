#!/usr/bin/env python3
# By ubuntu@allefant.com, October 2011. Do with it what you want.
"""
This is a quick script to sync emblems between Nautilus to Thunar.

Dependencies:
- python3 (with python3-gobject bindings)
- gvfs-info
- tdbtool

The script will then simply walk the given directory (optionally
recursively), call gvfs-info on each file and look for Nautilus emblem
metadata and if there are emblems use tdbtool to write Thunar metadata
for them. The emblems will be merged with existing Thunar emblems.

FIXME:
Any other Thunar metadata on affected file will be destroyed.

If you know a better way to set Thunar metadata please mail to

ubuntu@allefant.com

"""
import sys, os, argparse, subprocess, time, glob
from gi.repository import Gio as gio

THUNAR_METADATA = "~/.cache/Thunar/metafile.tdb"

def run(args):
    p = subprocess.Popen(args,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE)
    out, err = p.communicate()
    return out.decode("utf8")

def read_nautilus_emblems(path):
    out = run(["gvfs-info", path, "-a", "metadata"])
    for row in out.splitlines():
        row = row.strip()
        s = "metadata::emblems:"
        if row.startswith(s):
            row = row[len(s):].strip("[ ]")
            emblems = ["emblem-" + x.strip() for x in row.split(",")]
            return emblems
    return []
        
def read_thunar_emblems(path):
    f = gio.file_parse_name(path)
    out = run(["tdbtool", thunar.meta, "show", f.get_uri()])
    if out == "fetch failed\n": return []
    n = 0
    data = ""
    for row in out.splitlines():
        row = row.strip()
        if row.startswith("[%03x]" % n):
            vals = row[6:6+49].split()
            data += "".join([chr(int(x, 16)) for x in vals])
            n += 16
    data = data[1:]
    if data.find("\x00") >= 0:
        data = data[:data.find("\x00")]
    data = data.split(";")
    return data

def set_thunar_emblems(path, emblems):
    f = gio.file_parse_name(path)
    data = chr(0) + ";".join(emblems) + chr(0)
    data = data.encode("utf8")
    n = len(data)
    pad = (n + 3) // 4 * 4 - n
    data += bytes(pad)

    data = data.replace(b"\x00", b"\\00")
    out = run(["tdbtool", thunar.meta, "store", f.get_uri(), data])

def set_nautilus_emblems(path, emblems):
    emblems = [x[len("emblem-"):] for x in emblems]
    out = run(["gvfs-set-attribute", "-t", "stringv",
        path, "metadata::emblems"] + emblems)

def parse(d, r):
    for f in os.listdir(d):
        name = os.path.join(d, f)
        
        t = time.time()
        if t > thunar.time + 5:
            thunar.time = t
            print("\r%d files searched for emblems so far..." %
				thunar.counter)

        thunar.counter += 1
        
        nautilus_emblems = read_nautilus_emblems(name)
        thunar_emblems = read_thunar_emblems(name)
        if nautilus_emblems or thunar_emblems:
            new_emblems = set(nautilus_emblems + thunar_emblems)
            if new_emblems != set(thunar_emblems):
                print("New Thunar emblems for " + name + ": " +
					", ".join(new_emblems))
                set_thunar_emblems(name, new_emblems)
            if new_emblems != set(nautilus_emblems):
                print("New Nautilus emblems for " + name + ": " +
					", ".join(new_emblems))
                set_nautilus_emblems(name, new_emblems)
        
        if r and os.path.isdir(name):
            parse(name, r)

def main():
    global thunar

    parser = argparse.ArgumentParser(
		"Synchronize Nautilus and Thunar emblems.")
    parser.add_argument("directories", nargs = "*",
        help = "Emblems for all files in the specified directories " +
            "(but not the directories themselves) " +
            "will be synchronized.")
    parser.add_argument("--recursive", "-r", action = "store_true",
        help = "Descent into subdirectories.")
    parser.add_argument("--get", "-g",
        help = "Get the (comma separated) emblems for the given file.")
    parser.add_argument("--set", "-s", nargs = 2,
        help = "Set the (comma separated) emblems for the given file.")
    parser.add_argument("--rename", "-n",
        help = "If you renamed/moved a folder, cd into it then give the path " +
        "to the old location. Emblems will be fixed.")
        
    args = parser.parse_args()

    class T: pass
    thunar = T()
    thunar.meta = os.path.expanduser(THUNAR_METADATA)
    thunar.time = time.time()
    thunar.counter = 0

    if args.get:
        d = os.path.abspath(args.get)
        print(",".join(read_thunar_emblems(d)))

    if args.set:
        d = os.path.abspath(args.set[0])
        e = args.set[1].split(",")
        set_thunar_emblems(d, e)
    
    if args.rename:
        for f in glob.glob("*"):
            path = os.path.abspath(f)
            old_path = os.path.abspath(os.path.join(args.rename, f))
            old_emblems = read_thunar_emblems(old_path)
            emblems = read_thunar_emblems(old_path)
            emblems = list(set(emblems + old_emblems))
            set_thunar_emblems(path, emblems)

    for d in args.directories:
        if not os.path.isdir(d): continue
        parse(os.path.abspath(d), args.recursive)

if __name__ == "__main__":
    main()
