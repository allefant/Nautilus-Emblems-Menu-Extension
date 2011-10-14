# By ubuntu@allefant.com October 2011. Do with it what you want.
#
# I have close to 50 custom emblems and 1000ds of files with emblems
# for various purposes. In short I can't live without emblems. If
# Nautilus is going to completely remove them it won't be the end of
# the world, I can make a script which syncs them to KDE/Nepomuk tags.
# However Dolphin doesn't display icons for its tags on the files so it
# doesn't compare to Nautilus. (Nautilus and specifically emblems is
# the only reason I'm staying with Gnome.)
#
# So in short, Ubuntu Oneiric with Nautilus 3 was a very sad day for me
# with my emblems gone.
#
# This script is a bit of a stop-gap measure so I can keep on doing my
# work - it adds a menu entry with the same functionality as the
# removed side pane from the old Nautilus.
#
# Drop this file into /usr/share/nautilus-python/extensions/ and
# Nautilus should now have that extra menu item in the context menu of
# any file or folder.
#
# If someone knows any of the following:
#
# 1) How to retrieve the list of all available emblems from Nautilus.
# 2) How to retrieve the icon picture for an emblem from Nautilus.
# 3) How to add a custom picture to a Nautilus menu item.
# 4) How to set/clear emblems with the Nautilus API instead of GVFS.
#
# Please mail to ubuntu@allefant.com.
#

from gi.repository import Nautilus, GObject
import os, glob, subprocess

free_desktop_emblems = [
    "emblem-default",
    "emblem-documents",
    "emblem-downloads",
    "emblem-favorite",
    "emblem-important",
    "emblem-mail",
    "emblem-photos",
    "emblem-readonly",
    "emblem-shared",
    "emblem-symbolic-link",
    "emblem-synchronized",
    "emblem-system",
    "emblem-unreadable"]

USER_EMBLEMS_PATH = "~/.icons/hicolor/48x48/emblems"

class EmblemsMenu(GObject.GObject, Nautilus.MenuProvider):
    extra_emblems = None
    emblem_names = {}
    def __init__(self):
        
        # TODO: Is there a way to ask Nautilus for the list of all
        # possible emblems?
        if EmblemsMenu.extra_emblems is None:
            EmblemsMenu.extra_emblems = []
            usericons = os.path.expanduser(USER_EMBLEMS_PATH)
            for f in glob.glob(usericons + "/*.icon"):
                for row in open(f):
                    if row.startswith("DisplayName="):
                        name = row[len("DisplayName="):].strip()
                        n = os.path.basename(f)
                        n = os.path.splitext(n)[0]
                        EmblemsMenu.emblem_names[n] = name
                        EmblemsMenu.extra_emblems.append(n)
            EmblemsMenu.extra_emblems.sort()

    def get_file_items(self, window, files):
        menu_item = Nautilus.MenuItem(name = "EmblemsMenu::Emblems", 
            label = "Emblems", tip = "", icon = "")

        submenu = Nautilus.Menu()
        menu_item.set_submenu(submenu)
        for sub, emblems in [("Standard", free_desktop_emblems),
            ("User", EmblemsMenu.extra_emblems)]:
            if not emblems: continue

            sub_item = Nautilus.MenuItem(name = "EmblemsMenu::" + sub, 
                label = sub, tip = "", icon =  "")
            submenu.append_item(sub_item)

            emblems_menu = Nautilus.Menu()
            sub_item.set_submenu(emblems_menu)

            for e in emblems:
                display_name = EmblemsMenu.emblem_names.get(e,
                    e[len("emblem-"):])
                # TODO: How do we get the emblem icon image, and how
                # do we attach it to the menu as item?
                emblem_item = Nautilus.MenuItem(
                    name = "EmblemsMenu::" + e,
                    label = display_name, tip = "", icon = e)
                emblem_item.connect("activate", self.cb, (files, e))
                emblems_menu.append_item(emblem_item)

        sub_item = Nautilus.MenuItem(name = "EmblemsMenu::Clear", 
            label = "Clear", tip = "", icon =  "")
        sub_item.connect("activate", self.clear_cb, files)
        submenu.append_item(sub_item)

        return menu_item,

    def cb(self, menu, (files, emblem)):
        for f in files:
            f.add_emblem(emblem)
            # TODO: The above is not permanent? Why? Using GVFS instead
            # seems to work.
            p = subprocess.Popen(["gvfs-info", "-a",
                "metadata::emblems", f.get_name()],
            stdout = subprocess.PIPE)
            out, err = p.communicate()
            print(out)
            emblems = []
            for row in out.splitlines()[1:]:
                row = row.strip()
                if row.startswith("metadata::emblems:"):
                    row = row[len("metadata::emblems:"):].strip("[ ]")
                    emblems.extend([x.strip() for x in
                        row.split(",")])
            emblems.append(emblem)
            print(emblems)
            p = subprocess.Popen(["gvfs-set-attribute", "-t", "stringv",
                f.get_name(), "metadata::emblems"] + emblems)
            p.communicate()

    def clear_cb(self, menu, files):
        # TODO: How do I use Nautilus instead of gvfs?
        for f in files:
            p = subprocess.Popen(["gvfs-set-attribute", "-t", "unset",
                f.get_name(), "metadata::emblems"])
            p.communicate()
