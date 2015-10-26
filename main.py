#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
#  main.py
#  
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
from gi.repository import Gtk, GLib, Gdk, GObject
from doflicky import detection
import pisi.api
from threading import Thread

class DoFlicky(Gtk.Window):

    listbox = None

    def __init__(self):
        Gtk.Window.__init__(self)
        self.connect('destroy', Gtk.main_quit)

        hbar = Gtk.HeaderBar()
        hbar.set_show_close_button(True)
        self.set_titlebar(hbar)

        self.set_title("DoFlicky")
        hbar.set_title("DoFlicky")
        hbar.set_subtitle("Solus Driver Management")
        self.set_size_request(400, 400)

        mlayout = Gtk.VBox(0)
        self.add(mlayout)

        layout = Gtk.HBox(0)
        layout.set_border_width(20)
        mlayout.pack_start(layout, True, True, 0)

        self.set_icon_name("system-run-symbolic")
        img = Gtk.Image.new_from_icon_name("system-run-symbolic", Gtk.IconSize.INVALID)
        img.set_pixel_size(64)
        layout.pack_start(img, False, False, 0)

        text = """
In some cases you may gain improved performance or
features from the manufacturer's proprietary drivers.
Note that the Solus Project developers cannot audit this
closed source code."""

        
        lab = Gtk.Label(text)
        layout.pack_start(lab, True, True, 5)

        toolbar = Gtk.Toolbar()

        sep = Gtk.SeparatorToolItem()
        sep.set_expand(True)
        sep.set_draw(False)
        toolbar.add(sep)

        btn = Gtk.ToolButton.new(None, "Remove")
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-remove-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        btn = Gtk.ToolButton.new(None, "Install")
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-add-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        mlayout.pack_end(toolbar, False, False, 0)

        listbox = Gtk.ListBox()
        mlayout.pack_start(listbox, True, False, 3)

        # reserved widget
        self.rs = Gtk.Label("<b>Searching for available drivers</b>")
        self.rs.show_all()
        self.rs.set_use_markup(True)

        listbox.set_placeholder(self.rs)

        self.listbox = listbox

        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

        self.refresh()


    def refresh(self):
        t = Thread(target=self.detect_drivers)
        t.start()

    def add_pkg(self, pkg):
        meta,files = pisi.api.info(pkg)

        lab = Gtk.Label("%s - %s-%s" % (meta.package.name, meta.package.version, meta.package.release))
        lab.show_all()
        self.listbox.add(lab)

        return False


    def detect_drivers(self):
        for child in self.listbox.get_children():
            child.destroy()

        pkgs = detection.detect_hardware_packages()
        for pkg in pkgs:

            GObject.idle_add(lambda: self.add_pkg(pkg))

        if len(pkgs) == 0:
            GObject.idle_add(lambda: self.rs.set_markup("<b>No drivers were found for your system</b>"))
            
if __name__ == "__main__":
    GLib.threads_init()
    Gdk.threads_init()
    DoFlicky()
    Gtk.main()
