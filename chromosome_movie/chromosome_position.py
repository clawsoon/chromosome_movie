#!/usr/bin/env python3

import sqlite3

from . import svg2png

class ChromosomePosition():

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = self.cfg.layers.chromosome_position


        self.database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        self.cursor = self.database.cursor()

        self.cursor.execute('SELECT map_rate, map_offset FROM chromosome WHERE name=?', (self.cfg.chromosome,))
        self.rate, self.offset = self.cursor.fetchone()

        self.coordinates = {}
        self.cursor.execute('SELECT map_index, x, y FROM chromosome_map')
        for row in self.cursor:
            self.coordinates[row[0]] = (row[1], row[2])


    def circle(self, x, y):
        # TODO: Make this into a configurable style.
        return f'''
 <circle cx="{x}" cy="{y}" r="16" fill="orange" stroke="red" stroke-width="4.0"/>
 <circle cx="{x}" cy="{y}" r="4" fill="black" stroke="rgb(160,160,160)" stroke-width="3.0"/>
'''

    def svg(self, variant):
        index = self.index(variant)
        x, y = self.coordinates[index]
        return self.circle(x, y)


    def write_svg(self):

        # I am 1000% sure that there's a more efficient way to create 14,000
        # single dots than to create a separate file for each one.

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        for index, x, y in sorted(self.coordinates):

            with open(self.svg_path(variant), 'w') as svg:
                svg.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.cfg.width}" height="{self.cfg.height}" inkscape:export-xdpi="96" inkscape:export-ydpi="96">\n')
                svg.write(self.circle(x, y))
                svg.write('</svg>')

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, sorted(self.coordinates))

    def index(self, variant):
        return int(self.rate * (variant['chromosome_position'] - self.offset))

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)

