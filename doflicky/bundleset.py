#!/usr/bin/env python2.7
#
#  bundleset - core detection routine
#
#  Copyright 2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#

from doflicky import OSContext
from doflicky.driver.nvidia import DriverBundleNvidia
from doflicky.driver.nvidia import DriverBundleNvidia304
from doflicky.driver.nvidia import DriverBundleNvidia340
from doflicky.driver.broadcom import DriverBundleBroadcom
from pisi.db.installdb import InstallDB


class BundleSet:

    drivers = None
    allDrivers = None
    uniqueDrivers = None
    emul32Triggers = None
    db = None
    context = None

    def __init__(self):
        """ Initialise the potential driver bundle set """
        self.drivers = [
            DriverBundleNvidia340(),
            DriverBundleNvidia(),
            DriverBundleNvidia304(),
            DriverBundleBroadcom(),
        ]
        self.allDrivers = list()
        self.uniqueDrivers = list()
        self.emul32Triggers = dict()
        self.context = OSContext()

        self.db = InstallDB()
        for driver in self.drivers:
            for pkg in driver.triggers_emul32():
                if self.db.has_package(pkg):
                    self.emul32Triggers[driver] = True

    def detect(self):
        """ Perform main detection routine """
        for driver in self.drivers:
            if driver.is_present():
                self.add_driver(driver)

    def add_driver(self, driver):
        """ Attempt to add a driver to the set and avoid conflicts """
        b = driver.get_base()
        self.allDrivers.append(driver)
        if b is not None:
            otherDrivers = [x for x in self.uniqueDrivers if x.get_base() == b]

            for existing in otherDrivers:
                if existing.get_priority() > driver:
                    print("DEBUG: {} shadowed by existing {}".format(
                        driver.get_name(), existing.get_name()))
                    return
                elif driver.get_priority() > existing.get_priority():
                    self.uniqueDrivers.remove(existing)
                    self.uniqueDrivers.append(driver)

            if len(otherDrivers) < 1:
                self.uniqueDrivers.append(driver)
        else:
            self.uniqueDrivers.append(driver)
