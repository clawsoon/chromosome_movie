#!/usr/bin/env python3

import collections
import math
import sqlite3

from . import projections
from . import svg2png

# The SVG->PNG conversions from this script are the slowest part of the
# whole process.  I tried to speed things up by putting all the dots
# into a single file and using a series of inkscape actions like:
#         actions.append(f'select-by-id:{ID};object-set-attribute:style,display:inherit;export-filename:{png};export-do;object-set-attribute:style,display:none;select-clear;')
# ...but it was even slower than having inkscape load and export small
# SVGs individually.

Point = collections.namedtuple('Point', 'x y')

class Locations():


    def __init__(self, cfg):
        self.cfg = cfg

        self.projection = projections.get_projection(self.cfg.map_projection, self.cfg.map_rotation)

        self.database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        self.database.row_factory = sqlite3.Row
        self.location_cursor = self.database.cursor()

        self.order_key = f'order_{self.cfg.order}'


    def location_on_image(self, longitude, latitude):
        map_x, map_y = self.projection(longitude, latitude)
        map_y = -map_y
        x = map_x * self.cfg.map_height / 2 + self.cfg.map_width / 2
        y = map_y * self.cfg.map_height / 2 + self.cfg.map_height / 2
        return Point(x, y)


    def radius(self, variant_node_count, total_node_count):
        # Scaled by area, minus half stroke width.
        if hasattr(self.layercfg, 'fixed_radius') and self.layercfg.fixed_radius:
            radius = self.layercfg.max_radius
        else:
            proportion = variant_node_count / total_node_count
            if hasattr(self.layercfg, 'shrink_below_sample_count') and total_node_count < self.layercfg.shrink_below_sample_count:
                proportion /= 2
            radius = proportion**.5 * self.layercfg.max_radius - self.layercfg.stroke_width / 2
        # Inkscape gets weird if the radius gets too small.  And very weird if
        # it goes negative.
        min_radius = self.layercfg.min_radius if hasattr(self.layercfg, 'min_radius') else 1
        radius = max(radius, min_radius)
        return radius

    def write_svg_file(self, path, contents):
        svg = f'<svg viewBox="0 0 {self.cfg.map_width} {self.cfg.map_height}" xmlns="http://www.w3.org/2000/svg">\n'

        svg += contents

        svg += '</svg>\n'

        with open(path, 'w') as output:
            output.write(svg)


    def circles(self, locations):

        contents = ''

        # Add location circles.
        #for longitude, latitude, local_frequency in locations:
        for longitude, latitude, variant_node_count, total_node_count in locations:
            #radius = self.radius(local_frequency)
            radius = self.radius(variant_node_count, total_node_count)

            center = self.location_on_image(longitude, latitude)

            if hasattr(self.layercfg, 'shrink_below_sample_count') and total_node_count < self.layercfg.shrink_below_sample_count:
                style = self.layercfg.shrink_style
            else:
                style = self.layercfg.style

            contents += f'<circle cx="{center.x}" cy="{center.y}" r="{radius}" stroke-width="{self.layercfg.stroke_width}" style="{style}"/>\n'

        return contents

    def angle(self, point, center):
        return math.degrees(math.atan2(point.y - center.y, point.x - center.x))

    def direction(self, start_angle, middle_angle, end_angle):
        end_to_start = (end_angle - start_angle + 360) % 360
        end_to_middle = (end_angle - middle_angle + 360) % 360

        if end_to_middle < end_to_start:
            direction = 'positive'
            sweep_angle = end_to_start
        else:
            direction = 'negative'
            sweep_angle = 360 - end_to_start
        return direction, sweep_angle

    def trace_locations(self, variant):
        if variant[self.order_key] >= self.cfg.layers.traces.start_order:
            #self.location_cursor.execute('SELECT longitude, latitude FROM variant_location WHERE variant_id=?', (variant['local_counts_match_variant_id'],))
            self.location_cursor.execute('''
                SELECT
                    population.longitude AS longitude,
                    population.latitude AS latitude
                FROM
                    population
                JOIN
                    variant_population
                ON
                    population.id = variant_population.population_id
                WHERE
                    variant_population.variant_id = ?
            ''', (variant['population_counts_match_variant_id'],))
            locations = list(self.location_cursor)
            #if len(locations) == 2:
            #    return locations
            return locations
        return None

    def pacific_flip(self, variant, locations):

        if len(locations) == 2:
            lon0 = math.radians(locations[0][0])
            lat0 = math.radians(locations[0][1])
            lon1 = math.radians(locations[1][0])
            lat1 = math.radians(locations[1][1])
            x = (math.cos(lat0) * math.cos(lon0) + math.cos(lat1) * math.cos(lon1)) / 2
            y = (math.cos(lat0) * math.sin(lon0) + math.cos(lat1) * math.sin(lon1)) / 2
            z = (math.sin(lat0) + math.sin(lat1)) / 2
            average_longitude = math.degrees(math.atan2(y, x))
            average_latitude = math.degrees(math.atan2(z, (x**2 + y**2)**0.5))
        else:
            average_longitude = variant['average_longitude']
            average_latitude = variant['average_latitude']
        if self.cfg.layers.traces.prefer_pacific:
            start_angle = locations[0]['longitude']
            end_angle = locations[1]['longitude']
            start_new_world = 191 < (start_angle % 360) < 330
            end_new_world = 191 < (end_angle % 360) < 330
            if start_new_world != end_new_world:
                middle_angle = average_longitude
                direction, sweep_angle = self.direction(start_angle, middle_angle, end_angle)
                if (start_new_world and direction == 'positive') or (end_new_world and direction == 'negative'):
                    average_longitude += 180
                    if average_longitude > 180:
                        average_longitude -= 360
                    average_latitude = -average_latitude
        return average_longitude, average_latitude


class LocalFrequencies(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.local_frequencies


    def select(self):
        cursor = self.database.cursor()
        #cursor.execute('SELECT DISTINCT local_counts_match_variant_id FROM variant ORDER BY time DESC')
        cursor.execute('SELECT DISTINCT population_counts_match_variant_id FROM variant ORDER BY time DESC')
        return cursor

    def svg(self, variant):
        #self.location_cursor.execute('SELECT longitude, latitude, local_frequency FROM variant_location WHERE variant_id=?', (variant['local_counts_match_variant_id'],))
        self.location_cursor.execute('''
            SELECT
                population.longitude,
                population.latitude,
                variant_population.node_count,
                population.node_count
            FROM
                population
            JOIN
                variant_population
            ON
                population.id = variant_population.population_id
            WHERE variant_population.variant_id = ?
        ''', (variant['population_counts_match_variant_id'],))
        locations = self.location_cursor.fetchall()
        return self.circles(locations)

    def write_svg(self):
        for variant in self.select():
            self.write_svg_file(self.svg_path(variant), self.svg(variant))

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=tuple)

    def svg_path(self, variant):
        return str(self.layercfg.svg) % variant['population_counts_match_variant_id']

    def png_path(self, variant):
        return str(self.layercfg.png) % variant['population_counts_match_variant_id']


class Traces(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.traces

        self.contents = collections.deque(maxlen=self.layercfg.deque_length)

    def line(self, start, end):
        return f'<path d="M {start.x} {start.y} L {end.x} {end.y}" style="{self.layercfg.style}"/>'

    def arc(self, start, middle, end, center):
        start_angle = self.angle(start, center)
        middle_angle = self.angle(middle, center)
        end_angle = self.angle(end, center)

        direction, sweep_angle = self.direction(start_angle, middle_angle, end_angle)

        radius = ((start.x - center.x)**2 + (start.y - center.y)**2)**.5
        x_axis_rotation = 0
        large_arc_flag = 1 if sweep_angle > 180 else 0
        sweep_flag = 1 if direction == 'positive' else 0

        return f'<path d="M {start.x} {start.y} A {radius} {radius} {x_axis_rotation} {large_arc_flag} {sweep_flag} {end.x} {end.y}" style="{self.layercfg.style}"/>'


    def threepoint(self, start, middle, end):
        '''
        Figure out exactly what kind of arc - or straight line - goes through
        three points.
        '''

        # I'm sure that someone smart could make this whole function much
        # more compact.

        startmiddle_x = (start.x + middle.x) / 2
        startmiddle_y = (start.y + middle.y) / 2
        middleend_x = (middle.x + end.x) / 2
        middleend_y = (middle.y + end.y) / 2

        if start.y == middle.y and middle.y == end.y:
            path = self.line(start, end)
        elif start.x == middle.x and middle.x == end.x:
            path = self.line(start, end)
        elif start.y == middle.y:
            center_x = startmiddle_x
            middleend_inverse_slope = (middle.x - end.x) / (end.y - middle.y)
            center_y = (center_x - middleend_x) * middleend_inverse_slope + middleend_y
            center = Point(center_x, center_y)
            path = self.arc(start, middle, end, center)
        elif middle.y == end.y:
            center_x = middleend_x
            startmiddle_inverse_slope = (start.x - middle.x) / (middle.y - start.y)
            center_y = (center_x - startmiddle_x) * startmiddle_inverse_slope + startmiddle_y
            center = Point(center_x, center_y)
            path = self.arc(start, middle, end, center)
        else:
            startmiddle_inverse_slope = (start.x - middle.x) / (middle.y - start.y)
            middleend_inverse_slope = (middle.x - end.x) / (end.y - middle.y)
            if startmiddle_inverse_slope == middleend_inverse_slope:
                path = self.line(start, end)
            else:
                center_x = ((startmiddle_x * startmiddle_inverse_slope - startmiddle_y) - (middleend_x * middleend_inverse_slope - middleend_y)) / (startmiddle_inverse_slope - middleend_inverse_slope)
                center_y = (center_x - startmiddle_x) * startmiddle_inverse_slope + startmiddle_y
                center = Point(center_x, center_y)
                path = self.arc(start, middle, end, center)

        return path


    def trace(self, variant, locations):
        average_longitude, average_latitude = self.pacific_flip(variant, locations)
        start = self.location_on_image(locations[0]['longitude'], locations[0]['latitude'])
        middle = self.location_on_image(average_longitude, average_latitude)
        end = self.location_on_image(locations[1]['longitude'], locations[1]['latitude'])

        return self.threepoint(start, middle, end)


    def select(self):
        cursor = self.database.cursor()
        sql = f'SELECT id, population_counts_match_variant_id, time, average_longitude, average_latitude, {self.order_key}, lap_{self.cfg.order} FROM variant WHERE {self.order_key} >=? ORDER BY {self.order_key}'
        if self.cfg.movie_limit:
            sql += f' LIMIT {self.cfg.movie_limit}'
        cursor.execute(sql, self.layercfg.start_order)
        return cursor

    def svg(self, variant):
        # Note that this function only gives good results for repeated calls
        # if the calls are in the desired order, because it accumulates
        # traces up to deque_length.

        locations = self.trace_locations(variant)
        if locations:
            # self.contents is a deque, so old entries will roll off when
            # it's full.
            #self.contents.append(self.trace(variant, locations))
            for snum, start in enumerate(locations[:-1]):
                for end in locations[snum+1:]:
                    self.contents.append(self.trace(variant, (start, end)))
        return '\n'.join(self.contents) + '\n'

        ## TODO: Make "on" time a config variable.
        #if variant['time'] != 1:
        #    return ''
        #self.location_cursor.execute('SELECT longitude, latitude FROM variant_location WHERE variant_id=?', (variant['local_counts_match_variant_id'],))
        #locations = list(self.location_cursor)
        #if len(locations) == 2:
        #    self.contents.append(self.trace(variant, locations))
        #return '\n'.join(self.contents) + '\n'


    def write_svg(self):
        #location_cursor = self.database.cursor()
        #lap = None
        #contents = collections.deque(maxlen=self.layercfg.deque_length)
        for variant in self.select():
            #if lap != variant[f'lap_{self.cfg.order}']:
            #    # Clear the map of traces.
            #    contents = contents.clear()
            #lap = variant[f'lap_{self.cfg.order}']
            #self.location_cursor.execute('SELECT longitude, latitude FROM variant_location WHERE variant_id=?', (variant['local_counts_match_variant_id'],))
            #locations = list(location_cursor)
            #if len(locations) == 2:
            #    contents.append(self.trace(variant, locations))
            #self.write_svg_file(self.svg_path(variant), '\n'.join(contents))
            self.write_svg_file(self.svg_path(variant), self.svg(variant))

        self.write_svg_file(self.svg_path({'time': -1}, None), '')


    def index(self, variant):
        if variant['time'] > self.layercfg.start_time:
            #index = 999_999_999_999
            index = -1
        else:
            index = variant[self.order_key]
        return index

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=self.index)

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)


class AverageLocation(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.average_location

    def select(self):
        cursor = self.database.cursor()
        cursor.execute('SELECT DISTINCT average_longitude, average_latitude FROM variant ORDER BY time DESC')
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

    def svg(self, variant):
        locations = self.trace_locations(variant)
        if locations:
            average_longitude, average_latitude = self.pacific_flip(variant, locations)
        else:
            average_longitude, average_latitude = variant['average_longitude'], variant['average_latitude']
        location = (average_longitude, average_latitude, 1, 1)
        return self.circles([location])


    def write_svg(self):
        for variant in self.select():
            self.write_svg_file(self.svg_path(variant), self.svg(variant))

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=self.index)

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)



class MaxLocal(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.max_local

    def svg(self, variant=None):
        cursor = self.database.cursor()
        #cursor.execute('SELECT DISTINCT longitude, latitude FROM variant_location')
        cursor.execute('SELECT longitude, latitude FROM population')
        locations = [(row['longitude'], row['latitude'], 1, 1) for row in cursor]
        return self.circles(locations)

    def write_svg(self):
        self.write_svg_file(self.svg_path(), self.svg())

    def write_png(self):
        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png)

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)


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
            point = self.location_on_image(variant['average_longitude'], variant['average_latitude'])
            x = int(round(point.x))
            y = int(round(point.y))
            data[y-4:y+4, x-4:x+4] = (255,255,255,255)
        image = PIL.Image.fromarray(data, 'RGBA')
        image.save(str(self.layercfg.png) % 0)


class GraticuleVertices(Locations):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.graticule_vertices

    def svg(self, variant=None):
        locations = []
        for longitude in range(-180, 181, self.layercfg.spacing):
            for latitude in range(-90, 91, self.layercfg.spacing):
                locations.append((longitude, latitude, 1, 1))
        return self.circles(locations)

    def write_svg(self):
        self.write_svg_file(self.svg_path(), self.svg())

    def write_png(self):
        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png)

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)

