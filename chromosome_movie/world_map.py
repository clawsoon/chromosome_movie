#!/usr/bin/env python3

import shutil

class WorldMap():

    def __init__(self, cfg):
        self.cfg = cfg
        self.laycfg = cfg.layers.world_map

    def write_png(self):
        source = self.cfg.default_world_map
        destination = str(self.laycfg.png) % 0
        shutil.copy(source, destination)

    def svg_path(self, variant, frame):
        return str(self.laycfg.svg) % 0

    def png_path(self, variant, frame):
        return str(self.laycfg.png) % 0

