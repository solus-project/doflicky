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
from pisi.db.installdb import InstallDB

class DoFlicky(Gtk.Window):

    listbox = None
    installdb = None
    installbtn = None
    removebtn = None

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

        self.set_icon_name("cs-cat-hardware")
        img = Gtk.Image.new_from_icon_name("cs-cat-hardware", Gtk.IconSize.INVALID)
        img.set_pixel_size(64)
        layout.pack_start(img, False, False, 0)

        text = """
In some cases you may gain improved performance or
features from the manufacturer's proprietary drivers.
Note that the Solus Project developers cannot audit this
closed source code."""

        
        lab = Gtk.Label(text)
        lab.set_margin_start(20)
        layout.pack_start(lab, True, True, 5)

        toolbar = Gtk.Toolbar()

        sep = Gtk.SeparatorToolItem()
        sep.set_expand(True)
        sep.set_draw(False)
        toolbar.add(sep)

        btn = Gtk.ToolButton.new(None, "Remove")
        self.removebtn = btn
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-remove-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        btn = Gtk.ToolButton.new(None, "Install")
        self.installbtn = btn
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-add-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        mlayout.pack_end(toolbar, False, False, 0)

        listbox = Gtk.ListBox()
        scl = Gtk.ScrolledWindow(None, None)
        scl.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scl.add(listbox)

        mlayout.pack_end(scl, True, True, 0)

        # reserved widget
        self.rs = Gtk.Label("<b>Searching for available drivers</b>")
        self.rs.show_all()
        self.rs.set_use_markup(True)

        listbox.set_placeholder(self.rs)

        self.listbox = listbox
        self.listbox.connect("row-selected", self.row_handler)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

        self.refresh()


    def row_handler(self, box, row):
        """ Ensure we only enable the correct buttons """
        if not row:
            self.installbtn.set_sensitive(False)
            self.removebtn.set_sensitive(False)
            return
        child = row.get_child()

        installed = hasattr(child, 'ipackage')
        self.installbtn.set_sensitive(not installed)
        self.removebtn.set_sensitive(installed)

    def refresh(self):
        t = Thread(target=self.detect_drivers)
        t.start()

    def add_pkgs(self, pkgs):
        for pkg in pkgs:
            meta,files = pisi.api.info(pkg)

            iconName = "video-display"
            if meta.package.partOf != "xorg.driver":
                iconName = "drive-removable-media"

            img = Gtk.Image.new_from_icon_name(iconName, Gtk.IconSize.BUTTON)
            img.set_margin_start(12)

            box = Gtk.HBox(0)
            box.pack_start(img, False, False, 0)

            hasPkg = self.installdb.has_package(pkg)
            suffix = " [installed]" if hasPkg else ""

            lab = Gtk.Label("<big>%s</big> - <small>%s%s</small>" % (meta.package.summary, meta.package.version, suffix))
            lab.set_margin_start(12)
            lab.set_use_markup(True)
            box.pack_start(lab, False, True, 0)
            box.show_all()
            self.listbox.add(box)

            if hasPkg:
                setattr(box, "ipackage", self.installdb.get_package(pkg))
                lab.get_style_context().add_class("dim-label")

        return False

    def detect_drivers(self):
        self.installdb = InstallDB()

        for child in self.listbox.get_children():
            child.destroy()

        pkgs = detection.detect_hardware_packages()
        GObject.idle_add(lambda: self.add_pkgs(pkgs))

        if len(pkgs) == 0:
            GObject.idle_add(lambda: self.rs.set_markup("<b>No drivers were found for your system</b>"))
            
if __name__ == "__main__":
    GLib.threads_init()
    Gdk.threads_init()
    DoFlicky()
    Gtk.main()
