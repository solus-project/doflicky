#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of doflicky
#
#  Copyright © 2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#

from doflicky.detection import DriverBundlePCI


class DriverBundleBroadcom(DriverBundlePCI):
    """ Main NVIDIA driver (nvidia-glx-driver) """

    def __init__(self):
        DriverBundlePCI.__init__(self, "broadcom-sta.modaliases")

    def get_name(self):
        return "Broadcom's IEEE 802.11a/b/g/n hybrid Linux device driver"

    def get_icon(self):
        return "network-server"

    def has_emul32(self):
        return False

    def get_base(self):
        return "broadcom-sta"

    def get_priority(self):
        return 1

    def get_packages(self, context, emul32=False):
        if context.get_active_kernel_series() == "current":
            return ["broadcom-sta-current"]
        return ["broadcom-sta"]
