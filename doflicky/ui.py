#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
#  ui.py
#
#  Copyright 2015-2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
from gi.repository import Gtk, GObject
from doflicky.widgets import PackageLabel

import comar
import pisi.db
from pisi.operations.install import plan_install_pkg_names
from pisi.operations.remove import plan_remove
from pisi.operations.upgrade import plan_upgrade
import dbus


class CompletionPage(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)
        self.set_valign(Gtk.Align.CENTER)
        self.set_border_width(20)

        self.lab = Gtk.Label("")
        self.lab.set_use_markup(True)
        self.pack_start(self.lab, True, True, 0)

        self.btn = Gtk.Button("Restart")
        self.btn.set_hexpand(False)
        self.btn.set_halign(Gtk.Align.CENTER)

        self.pack_start(self.btn, False, False, 4)

        self.btn.connect('clicked', self.reboot)
        self.set_cancelled(False)

    def set_cancelled(self, c=False):
        self.btn.set_visible(not c)
        self.btn.set_sensitive(not c)
        if c:
            self.lab.set_markup("<big>User cancelled operation, please just "
                                "close this window</big>")
        else:
            self.lab.set_markup("<big>Please restart your device to complete "
                                "system configuration</big>")

    def reboot(self, btn, udata=None):
        try:
            bus = dbus.SystemBus()
            rskel = bus.get_object('org.freedesktop.login1',
                                   '/org/freedesktop/login1')
            iface = dbus.Interface(rskel, 'org.freedesktop.login1.Manager')
            iface.Reboot(True)
        except Exception, ex:
            print("Exception rebooting: %s" % ex)


class OpPage(Gtk.VBox):

    __gsignals__ = {
        'basket-changed': (GObject.SIGNAL_RUN_FIRST, None,
                           (object,)),
        'apply': (GObject.SIGNAL_RUN_FIRST, None,
                  (object,)),
        'complete': (GObject.SIGNAL_RUN_FIRST, None,
                     (object,)),
        'cancelled': (GObject.SIGNAL_RUN_FIRST, None,
                      (object,))
    }

    def __init__(self,
                 packagedb=pisi.db.packagedb.PackageDB,
                 installdb=pisi.db.installdb.InstallDB()):
        Gtk.VBox.__init__(self)
        self.set_valign(Gtk.Align.CENTER)
        self.set_border_width(20)

        self.packagedb = packagedb
        self.installdb = installdb

        self.title = Gtk.Label("")
        self.pack_start(self.title, False, False, 0)

        self.progress = Gtk.ProgressBar()
        self.pack_start(self.progress, False, False, 0)

        self.operations = dict()

        self.update_ui()

        self.cb = None
        self.link = comar.Link()
        self.pmanager = self.link.System.Manager['pisi']
        self.link.listenSignals("System.Manager", self.pisi_callback)

        self.current_operations = None

        self.downloaded = 0
        self.current_package = None

    def set_progress(self, fraction, label):
        if fraction is None:
            # Hide
            self.update_ui()
            return
        # print "%s %f" % (label, fraction)
        self.title.set_markup(label)
        self.progress.set_fraction(fraction)

    def update_ui(self):
        count = self.operation_count()
        if count == 0:
            return
        if count > 1:
            self.title.set_markup("{} operations pending".format(
                self.operation_count()))
        else:
            self.title.set_markup("One operation pending")

    def operation_for_package(self, package):
        if package.name in self.operations:
            return self.operations[package.name]
        return None

    def operation_count(self):
        return len(self.operations)

    def forget_package(self, package):
        if package.name in self.operations:
            self.operations.pop(package.name, None)
        self.update_ui()

    def remove_package(self, old_package):
        print("-REMOVE " + old_package)
        self.operations[old_package] = 'UNINSTALL'
        self.update_ui()

    def remove_packages(self, packages):
        for pkg in packages:
            if self.installdb.has_package(pkg):
                self.remove_package(pkg)

    def install_package(self, new_package):
        print("+INSTALL " + new_package)
        self.operations[new_package] = 'INSTALL'
        self.update_ui()

    def install_packages(self, packages):
        for pkg in packages:
            self.install_package(pkg)

    def update_package(self, old_package, new_package):
        self.operations[old_package.name] = 'UPDATE'
        self.update_ui()

    def _get_prog(self, step):
        self.progress_current = step
        total = float(self.progress_total)
        current = float(self.progress_current)

        fract = float(current/total)
        return fract

    def pisi_callback(self, package, signal, args):
        if signal == 'status':
            cmd = args[0]
            what = args[1]
            if cmd == 'updatingrepo':
                self.set_progress(1.0, "Updating %s repository" % what)
            elif cmd == 'extracting':
                prog = self._get_prog(self.progress_current + self.step_offset)
                msg = "Extracting {} of {}: {}".format(
                    self.current_package, self.total_packages, what)
                self.set_progress(prog, msg)
            elif cmd == 'configuring':
                prog = self._get_prog(self.progress_current + self.step_offset)
                msg = "Configuring {} of {}: {}".format(
                    self.current_package, self.total_packages, what)
                self.set_progress(prog, msg)
            elif cmd in ['removing', 'installing']:
                prog = self._get_prog(self.progress_current + self.step_offset)
                lab = "Installing %s: %s"
                if cmd == 'removing':
                    lab = "Removing %s: %s"
                count = "{} of {}".format(
                    self.current_package, self.total_packages)
                self.set_progress(prog, lab % (count, what))
            elif cmd in ['upgraded', 'installed', 'removed']:
                prog = self._get_prog(self.progress_current + self.step_offset)
                if cmd == 'upgraded':
                    lab = "Upgraded %s: %s"
                elif cmd == 'removed':
                    lab = "Removed %s: %s"
                elif cmd == 'installed':
                    lab = "Installed %s: %s"
                count = "{} of {}".format(
                    self.current_package,
                    self.total_packages)
                self.set_progress(prog, lab % (count, what))
                self.current_package += 1

        if signal == 'progress':
            cmd = args[0]
            if cmd == 'fetching':
                if self.current_operations is not None:
                    # Doing real operations now.
                    package = args[1]
                    # whatisthis = args[2]
                    speed_number = args[3]
                    speed_label = args[4]
                    downloaded = args[5]
                    download_size = args[6]
                    # down = downloaded
                    speed = "%d %s" % (speed_number, speed_label)

                    diff = downloaded - download_size
                    inc = self.total_size + diff
                    prog = self._get_prog(inc)

                    cd = self.current_dl_package
                    if cd == 0 and self.total_packages == 0:
                        self.set_progress(prog, "Downloading {} ({})".format(
                            package, speed))
                    else:
                        disp = "Downloading {} of {}: {} ({})"
                        self.set_progress(prog, disp.format(
                            self.current_dl_package,
                            self.total_packages, package, speed))

                    if downloaded >= download_size:
                        self.current_dl_package += 1
                else:
                    # print args
                    self.set_progress(1.0, "Downloading %s" % args[1])
        elif signal == 'finished' or signal is None:
            if self.cb is not None:
                self.cb()
            self.cb = None
            self.set_progress(None, None)
            self.update_ui()
            return
        elif str(signal).startswith("tr.org.pardus.comar.Comar.PolicyKit"):
            if self.cb is not None:
                self.cb()
            self.cb = None
            self.set_progress(None, None)
            self.update_ui()
            return

    def update_repo(self, cb=None):
        self.cb = cb
        self.pmanager.updateAllRepositories()

    def get_sizes(self, packages):
        totalSize = 0
        packages = [self.packagedb.get_package(pkg) for pkg in packages]
        for package in packages:
            totalSize += package.packageSize
        return totalSize

    def invalidate_all(self):
        # Handle operations that finished.
        self.operations = dict()
        self.emit('basket-changed', None)

    def show_dialog(self, pkgs, remove=False, update=False, install=True):
        markup = "<big>{}</big>".format(
            "The following dependencies need to be installed to continue")

        dlg = Gtk.Dialog(use_header_bar=1)
        dlg.set_title("Installation confirmation")
        if remove:
            markup = "<big>The following dependencies need to be removed to " \
                     "continue</big>"
            dlg.set_title("Removal confirmation")
        elif update:
            markup = "<big>The following dependencies need to be updated to " \
                     "continue</big>"
            dlg.set_title("Update confirmation")

        lab = Gtk.Label(markup)
        lab.set_use_markup(True)
        box = Gtk.HBox(0)
        box.set_property("margin", 5)
        box.pack_start(lab, True, True, 0)
        dlg.get_content_area().pack_start(box, False, False, 0)
        dlg.get_content_area().set_border_width(5)
        dlg.get_action_area().set_border_width(5)

        scroll = Gtk.ScrolledWindow(None, None)
        lbox = Gtk.ListBox()
        scroll.add(lbox)
        scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scroll.set_property("margin", 5)

        for pkg in pkgs:
            if remove:
                package = self.installdb.get_package(pkg)
            else:
                package = self.packagedb.get_package(pkg)
            panel = PackageLabel(package, None, interactive=False)
            lbox.add(panel)
        dlg.get_content_area().pack_start(scroll, True, True, 0)
        dlg.get_content_area().show_all()

        btn = dlg.add_button("Cancel", Gtk.ResponseType.CANCEL)
        if not remove:
            btn = dlg.add_button("Install" if install else "Update",
                                 Gtk.ResponseType.OK)
            btn.get_style_context().add_class("suggested-action")
        else:
            btn = dlg.add_button("Remove", Gtk.ResponseType.OK)
            btn.get_style_context().add_class("destructive-action")
        dlg.set_default_size(250, 400)
        res = dlg.run()
        dlg.destroy()
        if res == Gtk.ResponseType.OK:
            return True
        return False

    def apply_operations(self):
        self.doing_things = True
        updates = [
            i for i in self.operations if self.operations[i] == 'UPDATE'
        ]
        installs = [
            i for i in self.operations if self.operations[i] == 'INSTALL'
        ]
        removals = [
            i for i in self.operations if self.operations[i] == 'UNINSTALL'
        ]

        # We monitor 4 post events
        STEPS = 4

        self.installdb = pisi.db.installdb.InstallDB()
        self.packagedb = pisi.db.packagedb.PackageDB()

        self.emit('apply', None)
        # print "%d packages updated" % len(updates)
        # print "%d packages installed" % len(installs)
        # print "%d packages removed" % len(removals)

        setAct = False

        for packageset in [updates, installs, removals]:
            if len(packageset) == 0:
                continue

            self.current_package = 1
            self.current_dl_package = 1

            if packageset == installs:
                (pg, pkgs) = plan_install_pkg_names(packageset)
                if len(pkgs) > len(packageset):
                    p = [x for x in pkgs if x not in packageset]
                    if self.show_dialog(p):
                        installs = packageset = pkgs
                    else:
                        # print "Not installing"
                        continue
            elif packageset == removals:
                (pk, pkgs) = plan_remove(packageset)
                if len(pkgs) > len(packageset):
                    p = [x for x in pkgs if x not in packageset]
                    if self.show_dialog(p, remove=True):
                        removals = packageset = pkgs
                    else:
                        # print "Not removing"
                        continue
            elif packageset == updates:
                (pk, pkgs) = plan_upgrade(packageset)
                if len(pkgs) > len(packageset):
                    p = [x for x in pkgs if x not in packageset]
                    if self.show_dialog(p, update=True):
                        updates = packageset = pkgs
                    else:
                        # print Not continuing
                        continue
            self.total_packages = len(packageset)
            setAct = True

            if packageset != removals:
                self.total_size = self.get_sizes(packageset)
                # one tenth of progress is post install
                self.step_offset = self.total_size / 10
                self.progress_total = self.total_size + \
                    ((self.step_offset * self.total_packages) * STEPS)
            else:
                self.total_size = self.total_packages * (STEPS / 2)
                self.step_offset = 1
                self.progress_total = self.total_size
            self.progress_current = 0

            self.current_operations = packageset

            self.cb = self.invalidate_all
            if packageset == updates:
                self.pmanager.updatePackage(
                    ",".join(packageset), async=self.pisi_callback)
            elif packageset == installs:
                self.pmanager.installPackage(
                    ",".join(packageset), async=self.pisi_callback)
            elif packageset == removals:
                self.pmanager.removePackage(
                    ",".join(packageset), async=self.pisi_callback)
        if not setAct:
            self.invalidate_all()
            self.update_ui()
