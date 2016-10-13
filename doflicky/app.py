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

import sys
from gi.repository import GLib, Gtk, Gdk, Gio
from .window import DoFlickyWindow

class DoFlicky(Gtk.Application):
    """ Main entry into DoFlicky """

    app_win = None

    def __init__(self):
        Gtk.Application.__init__(self,
                                 application_id="com.solus_project.DoFlicky",
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)

        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        if self.app_win is not None:
            self.app_win.present()
            return
        self.app_win = DoFlickyWindow()
        app.add_window(self.app_win)
        self.app_win.present()
        self.app_win.show_all()
        self.app_win.refresh()

def doflicky_main():
    GLib.threads_init()
    Gdk.threads_init()
    app = DoFlicky()
    app.run(sys.argv)
