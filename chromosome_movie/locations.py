#!/usr/bin/env python3

import sqlite3

from . import projections
from . import svg2png

# The SVG->PNG conversions from this script are the slowest part of the
# whole process.  I tried to speed things up by putting all the dots
# into a single file and using a series of inkscape actions like:
#         actions.append(f'select-by-id:{ID};object-set-attribute:style,display:inherit;export-filename:{png};export-do;object-set-attribute:style,display:none;select-clear;')
# ...but it was even slower than having inkscape load and export small
# SVGs individually.


class Locations():


    def __init__(self, cfg):
        self.cfg = cfg

        self.projection = projections.get_projection(self.cfg.map_projection, self.cfg.map_rotation)

        self.database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        self.database.row_factory = sqlite3.Row


    def location_on_image(self, longitude, latitude):
        map_x, map_y = self.projection(longitude, latitude)
        map_y = -map_y
        x = map_x * self.cfg.map_height / 2 + self.cfg.map_width / 2
        y = map_y * self.cfg.map_height / 2 + self.cfg.map_height / 2
        return x, y


    def radius(self, proportion):
        # Scaled by area, minus half stroke width.
        return proportion**.5 * self.layercfg.max_radius - self.layercfg.stroke_width / 2


    def write_general_svg(self, path, locations):
        svg = f'<svg viewBox="0 0 {self.cfg.map_width} {self.cfg.map_height}" xmlns="http://www.w3.org/2000/svg">\n'

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

    def select(self):
        cursor = self.database.cursor()
        cursor.execute('SELECT DISTINCT average_longitude, average_latitude FROM variant')
        seen = set()
        for variant in cursor:
            index = self.index(variant)
            if index in seen:
                # Skip the repeats.
                continue
            seen.add(index)
            yield variant

    def index(self, variant):
        # Clipping to one decimal gives us sub-pixel resolution while
        # cutting down on the number of images we need to generate and
        # allowing us to put the full index into 8 digits.
        return int((variant['average_longitude']%360)*10)*10000 + int((variant['average_latitude']%360))

    def write_svg(self):
        for variant in self.select():
            location = (variant['average_longitude'], variant['average_latitude'], 1.0)
            self.write_general_svg(self.svg_path(variant, None), [location])

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=self.index)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % self.index(variant)



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


class AllAverageLocations(AverageLocation):

    '''
    Convenience class to see all spots covered by average locations.
    '''

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.all_average_locations

    def write_png(self):
        import numpy
        import PIL.Image
        data = numpy.full((self.layercfg.height, self.layercfg.width, 4), (0,0,0,0), dtype=numpy.uint8)

        seen = set()
        for variant in self.select():
            location = (variant['average_longitude'], variant['average_latitude'], 1.0)
            if location in seen:
                continue
            x, y = self.location_on_image(variant['average_longitude'], variant['average_latitude'])
            x = int(round(x))
            y = int(round(y))
            data[y-4:y+4, x-4:x+4] = (255,255,255,255)
        image = PIL.Image.fromarray(data, 'RGBA')
        image.save(str(self.layercfg.png) % 0)


class GraticuleVertices(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.graticule_vertices

    def write_svg(self):
        locations = []
        for longitude in range(-180, 181, self.layercfg.spacing):
            for latitude in range(-90, 91, self.layercfg.spacing):
                locations.append((longitude, latitude, 1.0))
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

