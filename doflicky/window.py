#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
#  window.py
#
#  Copyright 2015-2017 Ikey Doherty <ikey@solus-project.com>
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
import dbus.mainloop.glib
from .bundleset import BundleSet


class DoFlickyWindow(Gtk.ApplicationWindow):

    listbox = None
    installdb = None
    installbtn = None
    removebtn = None
    stack = None
    op_page = None
    package = None
    check_vga_emul32 = None
    bundleset = None
    driver = None

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

        self.set_icon_name("jockey")
        img = Gtk.Image.new_from_icon_name("jockey",
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
        lb = "Also install 32-bit driver (Required for some games)"
        self.check_vga_emul32 = Gtk.CheckButton.new_with_label(lb)
        self.check_vga_emul32.set_halign(Gtk.Align.START)
        mlayout.pack_start(self.check_vga_emul32, False, False, 0)
        self.check_vga_emul32.set_no_show_all(True)
        self.check_vga_emul32.set_property("margin-top", 3)
        self.check_vga_emul32.set_property("margin-bottom", 3)
        self.check_vga_emul32.set_property("margin-start", 12)

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
        self.op_page.connect('basket-changed', self.finished_handler)
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
            self.driver = None
            self.check_vga_emul32.hide()
            return
        child = row.get_child()

        self.driver = getattr(child, 'driver')
        emul32 = self.driver.has_emul32()
        self.check_vga_emul32.set_visible(emul32)

        packages = self.driver.get_packages(self.bundleset.context, False)
        installed = False
        for pkg in packages:
            if self.installdb.has_package(pkg):
                installed = True
                break

        self.installbtn.set_sensitive(not installed)
        self.removebtn.set_sensitive(installed)

    def refresh(self):
        self.layout.set_sensitive(False)
        t = Thread(target=self.detect_drivers)
        t.start()

    def install_package(self, udata=None):
        e32 = False
        if self.check_vga_emul32.get_visible():
            if self.check_vga_emul32.get_active():
                e32 = True

        desiredPackages = self.driver.get_packages(self.bundleset.context, e32)
        self.op_page.install_packages(desiredPackages)
        self.stack.set_visible_child_name("operations")
        self.op_page.apply_operations()

    def remove_package(self, udata=None):
        packages = []
        desiredPackages = self.driver.get_packages(self.bundleset.context,
                                                   True)
        for pkg in desiredPackages:
            if self.installdb.has_package(pkg):
                packages.append(pkg)

        self.op_page.remove_packages(packages)
        self.stack.set_visible_child_name("operations")
        self.op_page.apply_operations()

    def add_pkgs(self):
        for driver in self.bundleset.uniqueDrivers:
            iconName = driver.get_icon()

            hasPkg = True
            packages = driver.get_packages(self.bundleset.context, False)
            for pkg in packages:
                if not self.installdb.has_package(pkg):
                    hasPkg = False
                    break

            img = Gtk.Image.new_from_icon_name(iconName, Gtk.IconSize.BUTTON)
            img.set_margin_start(12)

            box = Gtk.HBox(0)
            box.pack_start(img, False, False, 0)

            suffix = " [installed]" if hasPkg else ""

            lab = Gtk.Label("<big>{}</big> - <small>{}</small>".format(
                driver.get_name(), suffix))
            lab.set_margin_start(12)
            lab.set_use_markup(True)
            box.pack_start(lab, False, True, 0)
            box.show_all()
            self.listbox.add(box)

            if hasPkg:
                lab.get_style_context().add_class("dim-label")
            setattr(box, "driver", driver)

        self.layout.set_sensitive(True)
        return False

    def detect_drivers(self):
        self.installdb = InstallDB()
        self.packagedb = PackageDB()

        for child in self.listbox.get_children():
            child.destroy()

        self.bundleset = BundleSet()
        self.bundleset.detect()

        pkgs = detection.detect_hardware_packages()
        GObject.idle_add(lambda: self.add_pkgs())

        if len(pkgs) == 0:
            d = "No drivers were found for your system"
            GObject.idle_add(lambda: self.rs.set_markup("<b>{}</b>".format(d)))
