#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
#  ui.py
#  
#  Copyright 2015 Ikey Doherty <ikey@solus-project.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
from gi.repository import Gtk, GLib, Gdk, GObject, Gio

class OpPage(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)

        lab = Gtk.Label("<big>This page is not yet implemented</big>")
        lab.set_use_markup(True)

        self.pack_start(lab, True, True, 0)


