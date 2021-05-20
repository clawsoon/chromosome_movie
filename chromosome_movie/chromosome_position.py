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



    def select(self):
        self.coordinates = {}
        self.cursor.execute('SELECT map_index, x, y FROM chromosome_map')
        #for row in self.cursor:
        #    self.coordinates[row[0]] = (row[1], row[2])


    def write_svg(self):

        # I am 1000% sure that there's a more efficient way to create 14,000
        # single dots than to create a separate file for each one.

        seen = set()
        for index, x, y in self.select():
            if index in seen:
                continue
            seen.add(index)

            path = str(self.layercfg.svg) % index
            with open(path, 'w') as svg:
                svg.write(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.cfg.width}" height="{self.cfg.height}" inkscape:export-xdpi="96" inkscape:export-ydpi="96">
 <circle cx="{x}" cy="{y}" r="16" fill="orange" stroke="red" stroke-width="4.0"/>
 <circle cx="{x}" cy="{y}" r="4" fill="black" stroke="rgb(160,160,160)" stroke-width="3.0"/>
</svg>
''')


    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = [row[0] for row in self.select()]
        svg2png.svg2png(self.cfg, svg, png, frames)

    def get_index(self, position):
        return int(self.rate * (position - self.offset))

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % self.get_index(variant['chromosome_position'])

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % self.get_index(variant['chromosome_position'])

