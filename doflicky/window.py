#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
#  window.py
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#

from gi.repository import Gtk, GObject
from doflicky import detection
from doflicky.ui import OpPage, CompletionPage
from threading import Thread
from pisi.db.installdb import InstallDB
from pisi.db.packagedb import PackageDB
import pisi.api
import dbus.mainloop.glib


class DoFlickyWindow(Gtk.ApplicationWindow):

    listbox = None
    installdb = None
    installbtn = None
    removebtn = None
    stack = None
    selection = None
    op_page = None
    package = None
    check_vga_emul32 = None

    def __init__(self):
        Gtk.ApplicationWindow.__init__(self)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        hbar = Gtk.HeaderBar()
        hbar.set_show_close_button(True)
        self.set_titlebar(hbar)

        self.set_title("DoFlicky")
        hbar.set_title("DoFlicky")
        hbar.set_subtitle("Solus Driver Management")
        self.set_size_request(400, 400)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(
            Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        mlayout = Gtk.VBox(0)
        self.stack.add_named(mlayout, "main")
        self.add(self.stack)
        self.layout = mlayout

        layout = Gtk.HBox(0)
        layout.set_border_width(20)
        mlayout.pack_start(layout, True, True, 0)

        self.set_icon_name("cs-cat-hardware")
        img = Gtk.Image.new_from_icon_name("cs-cat-hardware",
                                           Gtk.IconSize.INVALID)
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

        # Allow installing 32-bit drivers..
        lb = "Also install 32-bit driver (Required for Steam & Wine)"
        self.check_vga_emul32 = Gtk.CheckButton.new_with_label(lb)
        self.check_vga_emul32.set_halign(Gtk.Align.END)
        mlayout.pack_start(self.check_vga_emul32, False, False, 0)
        self.check_vga_emul32.set_no_show_all(True)

        toolbar = Gtk.Toolbar()

        sep = Gtk.SeparatorToolItem()
        sep.set_expand(True)
        sep.set_draw(False)
        toolbar.add(sep)

        btn = Gtk.ToolButton.new(None, "Remove")
        btn.connect('clicked', self.remove_package)
        self.removebtn = btn
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-remove-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        btn = Gtk.ToolButton.new(None, "Install")
        btn.connect('clicked', self.install_package)
        self.installbtn = btn
        btn.set_sensitive(False)
        btn.set_property("icon-name", "list-add-symbolic")
        btn.set_is_important(True)
        toolbar.add(btn)

        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        mlayout.pack_end(toolbar, False, False, 0)

        listbox = Gtk.ListBox()
        scl = Gtk.ScrolledWindow(None, None)
        scl.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
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

        # update page..
        page = OpPage()
        self.op_page = page
        self.op_page.connect('complete', self.finished_handler)
        self.op_page.connect('cancelled', self.cancelled_handler)
        self.stack.add_named(page, "operations")
        self.show_all()

        self.cpage = CompletionPage()
        self.stack.add_named(self.cpage, "complete")

    def finished_handler(self, page, udata=None):
        if self.stack.get_visible_child_name() != "complete":
            self.stack.set_visible_child_name("complete")

    def cancelled_handler(self, page, udata=None):
        self.cpage.set_cancelled(True)
        if self.stack.get_visible_child_name() != "complete":
            self.stack.set_visible_child_name("complete")

    def row_handler(self, box, row):
        """ Ensure we only enable the correct buttons """
        if not row:
            self.installbtn.set_sensitive(False)
            self.removebtn.set_sensitive(False)
            self.selection = None
            self.check_vga_emul32.hide()
            return
        child = row.get_child()

        installed = hasattr(child, 'ipackage')
        self.selection = getattr(child, 'packagen')
        self.package = getattr(child, 'package')
        # Update emul32 switch based on type of package
        if self.package.partOf != "xorg.driver":
            self.check_vga_emul32.hide()
        else:
            self.check_vga_emul32.show()
        self.installbtn.set_sensitive(not installed)
        self.removebtn.set_sensitive(installed)

    def refresh(self):
        self.layout.set_sensitive(False)
        t = Thread(target=self.detect_drivers)
        t.start()

    def install_package(self, udata=None):
        emul32 = False
        if self.check_vga_emul32.get_visible():
            if self.check_vga_emul32.get_active():
                emul32 = True

        self.op_page.install_package(self.package, emul32=emul32)
        self.stack.set_visible_child_name("operations")
        self.op_page.apply_operations()

    def remove_package(self, udata=None):
        self.op_page.remove_package(self.package)
        self.stack.set_visible_child_name("operations")
        self.op_page.apply_operations()

    def add_pkgs(self, pkgs):
        # If wine-32bit or steam is installed, pre-select 32-bit drivers
        do_emul32 = False
        if self.installdb.has_package("steam"):
            do_emul32 = True
        elif self.installdb.has_package("wine-32bit"):
            do_emul32 = True
        self.check_vga_emul32.set_active(do_emul32)

        for pkg in pkgs:
            meta, files = pisi.api.info(pkg)

            iconName = "video-display"
            if meta.package.partOf != "xorg.driver":
                iconName = "drive-removable-media"

            img = Gtk.Image.new_from_icon_name(iconName, Gtk.IconSize.BUTTON)
            img.set_margin_start(12)

            box = Gtk.HBox(0)
            box.pack_start(img, False, False, 0)

            hasPkg = self.installdb.has_package(pkg)
            suffix = " [installed]" if hasPkg else ""

            lab = Gtk.Label("<big>{}</big> - <small>{}{}</small>".format(
                meta.package.summary, meta.package.version, suffix))
            lab.set_margin_start(12)
            lab.set_use_markup(True)
            box.pack_start(lab, False, True, 0)
            box.show_all()
            self.listbox.add(box)

            if hasPkg:
                setattr(box, "ipackage", self.installdb.get_package(pkg))
                lab.get_style_context().add_class("dim-label")
            setattr(box, "package", self.packagedb.get_package(pkg))
            setattr(box, "packagen", pkg)

        self.layout.set_sensitive(True)
        return False

    def detect_drivers(self):
        self.installdb = InstallDB()
        self.packagedb = PackageDB()

        for child in self.listbox.get_children():
            child.destroy()

        pkgs = detection.detect_hardware_packages()
        GObject.idle_add(lambda: self.add_pkgs(pkgs))

        if len(pkgs) == 0:
            d = "No drivers were found for your system"
            GObject.idle_add(lambda: self.rs.set_markup("<b>{}</b>".format(d)))
