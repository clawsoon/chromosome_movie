#!/usr/bin/env python3

import sys

import sqlite3

from . import projections, svg2png

# The SVG->PNG conversions from this script are the slowest part of the
# whole process.  I tried to speed things up by putting all the dots
# into a single file and using a series of inkscape actions like:
#         actions.append(f'select-by-id:{ID};object-set-attribute:style,display:inherit;export-filename:{png};export-do;object-set-attribute:style,display:none;select-clear;')
# ...but it was even slower than having inkscape load and export small
# SVGs individually.


class Locations():


    def __init__(self, cfg):
        self.cfg = cfg

        self.projection = projections.get_projection(self.cfg.layers.world_map.projection, self.cfg.layers.world_map.rotation)

        self.database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        self.database.row_factory = sqlite3.Row


    def location_on_image(self, longitude, latitude):
        map_x, map_y = self.projection(longitude, latitude)
        x = map_x * self.cfg.layers.world_map.height / 2 + self.cfg.layers.world_map.center[0]
        y = map_y * self.cfg.layers.world_map.height / 2 + self.cfg.layers.world_map.center[1]
        return x, y


    def radius(self, proportion):
        # Scaled by area, minus half stroke width.
        return proportion**.5 * self.layercfg.max_radius - self.layercfg.stroke_width / 2


    def write_general_svg(self, path, locations):
        svg = f'<svg viewBox="0 0 {self.cfg.width} {self.cfg.height}" xmlns="http://www.w3.org/2000/svg">\n'

        # Add location circles.
        for longitude, latitude, local_frequency in locations:
            radius = self.radius(local_frequency)

            circle_x, circle_y = self.location_on_image(longitude, latitude)

            svg += f'<circle cx="{circle_x}" cy="{circle_y}" r="{radius}" stroke-width="{self.layercfg.stroke_width}" style="{self.layercfg.style}"/>\n'

        svg += '</svg>\n'

        with open(path, 'w') as output:
            output.write(svg)


class LocalFrequencies(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.local_frequencies


    def select(self):
        cursor = self.database.cursor()
        cursor.execute('SELECT DISTINCT local_counts_match_variant_id FROM variant')
        return cursor

    def write_svg(self):
        location_cursor = self.database.cursor()
        for variant in self.select():
            location_cursor.execute('SELECT longitude, latitude, local_frequency FROM variant_location WHERE variant_id=?', (variant['local_counts_match_variant_id'],))
            locations = location_cursor.fetchall()
            self.write_general_svg(self.svg_path(variant, None), locations)

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=tuple)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % variant['local_counts_match_variant_id']

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % variant['local_counts_match_variant_id']


class AverageLocation(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.average_location

        # Rounding to one digit after the decimal should give us
        # sub-pixel resolution while cutting down on the number of
        # images we need to make.  Hopefully SQLite and Python's
        # round() functions both work exactly the same way.
        self.digits = 1

    def select(self):
        cursor = self.database.cursor()
        cursor.execute('SELECT DISTINCT ROUND(average_longitude, ?) AS average_longitude, ROUND(average_latitude, ?) AS average_latitude FROM variant', (self.digits, self.digits))
        return cursor


    def write_svg(self):
        seen = set()
        for variant in self.select():
            location = (variant['average_longitude'], variant['average_latitude'], 1.0)
            if location in seen:
                continue
            self.write_general_svg(self.svg_path(variant, None), [location])

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=tuple)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % (round(variant['average_longitude'], self.digits), round(variant['average_latitude'], self.digits))

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % (round(variant['average_longitude'], self.digits), round(variant['average_latitude'], self.digits))



class MaxLocal(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.max_local


    def write_svg(self):
        cursor = self.database.cursor()
        cursor.execute('SELECT DISTINCT longitude, latitude FROM variant_location')
        locations = [(row['longitude'], row['latitude'], 1.0) for row in cursor]
        self.write_general_svg(self.svg_path(None, None), locations)

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = [0]
        svg2png.svg2png(self.cfg, svg, png, frames)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % 0

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % 0

