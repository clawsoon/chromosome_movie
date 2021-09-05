#!/usr/bin/env python3

import sys
import os
import shutil

class WorldMap():

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = cfg.layers.world_map

    def path(self):
        if self.cfg.default_world_map.suffix == '.png':
            path = self.png_path()
        elif self.cfg.default_world_map.suffix == '.svg':
            path = self.svg_path()
        else:
            raise Exception('Map extension not recognized')
        return path

    def svg(self, variant=None):
        # We're making some assumptions here.
        if 'world_map' in self.cfg.background_layers:
            path = os.path.relpath(self.path(), self.cfg.layers.background.png.parent).replace('\\', '/')
        elif 'world_map' in self.cfg.foreground_layers:
            path = os.path.relpath(self.path(), self.cfg.layers.foreground.svg.parent).replace('\\', '/')
        else:
            raise Exception('Not sure which layer to put world map.')

        if self.cfg.map_format == 'svg':
            # "use" gives a much cleaner result than "image" for the
            # bertin map.  I think it's because the bertin map is being
            # scaled up from 700x475.
            svg = f' <use xlink:href="{path}#base%20map"/>\n'
        elif self.cfg.map_format == 'png':
            svg = f' <image xlink:href="{path}" width="{self.layercfg.width}" height="{self.layercfg.height}" preserveAspectRatio="xMidYMid"/>\n'
        else:
            raise Exception('Map format not recognized.')

        return svg

    def write(self):
        source = self.cfg.default_world_map
        destination = self.path()
        if os.path.exists(source):
            sys.stderr.write(f'Copying {source} -> {destination}\n')
            shutil.copy(source, destination)

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)

