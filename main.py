#!/usr/bin/env python
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
from doflicky import detection
import pisi.api

def main():
    pkgs = detection.detect_hardware_packages()
    if len(pkgs) == 0:
        print("No hardware support discovered")
        sys.exit(1)
    print("Discovered package(s): %s" % ", ".join(pkgs))
    for pkg in pkgs:
        meta,files = pisi.api.info(pkg)
        print "%s - %s-%s" % (meta.package.name, meta.package.version, meta.package.release)

if __name__ == "__main__":
    main()
