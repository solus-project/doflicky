#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of solus-sc
#
#  Copyright © 2013-2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#

import gi.repository
gi.require_version('Gtk', '3.0')


class DriverBundle:
    """ A driver bundle is the base type and corresponds to a set of packages
        that should be present for the hardware to correctly work
    """

    def has_emul32():
        """ By default most packages are native arch, and don't have a 32-bit
            equivalent. This differs for the NVIDIA drivers
        """
        return False

    def get_packages(emul32=False):
        """ Return the package set required for this bundle. The bundle should
            add more packages if emul32 has actually been requested, and it
            indeed supports emul32
        """
        return []

    def get_name():
        """ Return the name for this driver bundle """
        return "Not implemented"

    def get_icon():
        """ Return a usable display icon name to be presented to the user in
            the UI listing if this hardware is present """
        return "image-missing"

    def is_present():
        """ Allow the driver manager to know whether the hardware represented
            by the bundle is actually present or not.
        """
        return False
