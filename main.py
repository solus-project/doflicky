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

from doflicky.detection import *
import sys

MODDIR = "/usr/share/doflicky/modaliases"

def main():
    if not os.path.exists(MODDIR):
        print("Moddir not found: %s" % MODDIR)
        sys.exit(1)

    pkgs = dict()

    for item in os.listdir(MODDIR):
        if not item.endswith(".modaliases"):
            continue
        with open(os.path.join(MODDIR, item), "r") as inp:
            for line in inp.readlines():
                line = line.replace("\r","").replace("\n","").strip()
                splits = line.split()
                if len(splits) != 4:
                    continue
                if splits[0] != "alias":
                    continue
                id = splits[1]
                pkg = splits[3]
                if pkg not in pkgs:
                    pkgs[pkg] = list()
                pkgs[pkg].append(HardwareID("modalias", id))

    aliases = get_modaliases()
    for alias in aliases:
        for pkg in pkgs:
            if alias in pkgs[pkg]:
                print("%s discovered with ID %s" % (pkg, alias))

if __name__ == "__main__":
    main()
