#!/usr/bin/env python3
# By ubuntu@allefant.com, October 2011. Do with it what you want.
"""
This is a quick script to one-way sync emblems from Nautilus to Thunar.

Dependencies:
- python3 (with python3-gobject bindings)
- gvfs-info
- tdbtool

The script will then simply walk the given directory (ontionally
recursively), call gvfs-info on each file and look for Nautilus emblem
metadata and if there are emblems use tdbtool to write Thunar metadata
for them. The emblems will be merged with existing Thunar emblems.

FIXME:
Any other Thunar metadata on affected file will be destroyed.

If you know a better way to set Thunar metadata please mail to

ubuntu@allefant.com

"""
import sys, os, argparse, subprocess
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
			emblems = [x.strip() for x in row.split(",")]
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

def parse(d, r):
	for f in os.listdir(d):
		name = os.path.join(d, f)
		
		nautilus_emblems = read_nautilus_emblems(name)
		thunar_emblems = read_thunar_emblems(name)
		if nautilus_emblems:
			nautilus_emblems = ["emblem-" + x for x in nautilus_emblems]
			new_emblems = set(nautilus_emblems + thunar_emblems)
			if new_emblems != set(thunar_emblems):
				new_emblems = list(new_emblems)
				print("New emblems for " + name + ": " + ", ".join(new_emblems))
				set_thunar_emblems(name, new_emblems)
		
		if r and os.path.isdir(name):
			parse(name, r)

def main():
	global thunar

	parser = argparse.ArgumentParser()
	parser.add_argument("-d",
		help = "Emblems for all files in the directory (but not the " +
		 " directory itself) will be transferred.")
	parser.add_argument("-r", action = "store_true",
		help = "Descent into subdirectories.")
	args = parser.parse_args()

	class T: pass
	thunar = T()
	thunar.meta = os.path.expanduser(THUNAR_METADATA)
	parse(os.path.abspath(args.d), args.r)

if __name__ == "__main__":
	main()
