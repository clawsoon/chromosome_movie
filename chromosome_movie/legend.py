#!/usr/bin/env python3

import sqlite3
from xml.sax import saxutils

from . import svg2png
from . import drop_shadow
from . import chromosome_position


class Legend():

    def __init__(self, cfg):
        self.cfg = cfg

    def radius(self, proportion, cfg, shrink=False):
        if shrink:
            proportion *= self.cfg.layers.local_frequencies.shrink_factor
        radius = proportion**.5 * cfg.max_radius - cfg.stroke_width / 2
        radius = max(radius, 1)
        return radius

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'
        if self.cfg.shadows:
            svg += drop_shadow.filter
        svg += self.svg()
        svg += '</svg>\n'

        with open(self.svg_path(), 'w') as output:
            output.write(svg)

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg2png.svg2png(self.cfg, self.svg_path(), self.png_path())

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)
        


class Frequency(Legend):
    # The only reason we're subclassing is for the radius function.
    # Seems not quite worth it.

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.legend_frequency
        self.frequencycfg = self.cfg.layers.local_frequencies

    def svg(self, variant=None):
        svg = ''
        shadow = drop_shadow.style if self.cfg.shadows else ''

        #for num, frequency in enumerate(self.layercfg.frequencies):
        #    percentage = saxutils.escape(f'{frequency*100:g}%')
        #    radius = self.radius(frequency, self.frequencycfg)

        #    circle_x = self.frequencycfg.max_radius * 2
        #    circle_y = self.layercfg.font_size * (num + 2)

        #    text_x = self.frequencycfg.max_radius * 5
        #    text_y = self.layercfg.font_size * (num + 2)

        #    svg += f'  <circle cx="{circle_x}" cy="{circle_y}" r="{radius}" stroke-width="{self.frequencycfg.stroke_width}" style="{self.frequencycfg.style}"/>\n'

        #    svg += f'  <text text-anchor="start" dominant-baseline="middle" x="{text_x}" y="{text_y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{percentage}</text>\n'

        if self.layercfg.orientation == 'horizontal':
            horizontal_total = len(self.layercfg.frequencies) * len(self.layercfg.legends)
            vertical_total = 2
            horizontal_spacing = 3 * self.layercfg.font_size
        else:
            horizontal_total = 2
            vertical_total = len(self.layercfg.frequencies)
            horizontal_spacing = 2 * self.layercfg.font_size

        if self.layercfg.title:
            vertical_total += 1

        x = lambda n: (n - (horizontal_total - 1) / 2) * horizontal_spacing + self.layercfg.width / 2
        y = lambda n: (n - (vertical_total - 1) / 2) * self.layercfg.line_spacing * self.layercfg.font_size + self.layercfg.height / 2

        for num_legend, legend in enumerate(self.layercfg.legends):

            if self.layercfg.orientation == 'horizontal':
                offset = num_legend * len(self.layercfg.frequencies)
                title_x = x(offset + (len(self.layercfg.frequencies)-1)/2)
                title_y = y(0)
            else:
                offset = num_legend * vertical_total
                title_x = x(0)
                title_y = y(offset)

            if self.layercfg.title:
                title = saxutils.escape(self.layercfg.title % legend['title'])
                svg += f'  <text text-anchor="middle" dominant-baseline="middle" x="{title_x}" y="{title_y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{title}</text>\n'

            for num_frequency, frequency in enumerate(self.layercfg.frequencies):

                percentage = saxutils.escape(f'{frequency*100:g}%')
                radius = self.radius(frequency, self.frequencycfg, shrink=legend['shrink'])

                if self.layercfg.orientation == 'horizontal':
                    circle_x = text_x = x(offset + num_frequency)
                    if self.layercfg.title:
                        circle_y = y(1)
                        text_y = y(2)
                    else:
                        circle_y = y(0)
                        text_y = y(1)
                else:
                    circle_x = x(-0.5)
                    text_x = x(0.5)
                    if self.layercfg.title:
                        circle_y = text_y = y(offset + num_frequency + 1)
                    else:
                        circle_y = text_y = y(offset + num_frequency)

                if legend['shrink']:
                    style = self.frequencycfg.shrink_style
                else:
                    style = self.frequencycfg.style

                svg += f'  <circle cx="{circle_x}" cy="{circle_y}" r="{radius}" stroke-width="{self.frequencycfg.stroke_width}" style="{style}"/>\n'

                svg += f'  <text text-anchor="middle" dominant-baseline="middle" x="{text_x}" y="{text_y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{percentage}</text>\n'

        return svg

class Position(Legend):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.legend_position
        self.frequencycfg = self.cfg.layers.local_frequencies
        self.locationcfg = self.cfg.layers.average_location
        self.positioncfg = self.cfg.layers.chromosome_position

    def svg(self, variant=None):

        svg = ''
        shadow = drop_shadow.style if self.cfg.shadows else ''

        position = chromosome_position.ChromosomePosition(self.cfg)

        x = self.layercfg.font_size

        ycenter = self.layercfg.height / 2

        ## Geographic location

        #y = ycenter - self.layercfg.font_size * 1.25

        #svg += f'  <circle cx="{x}" cy="{y}" r="{self.frequencycfg.max_radius}" stroke-width="{self.frequencycfg.stroke_width}" style="{self.frequencycfg.style}"/>\n'

        #svg += f'  <text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="1em" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Geographic location</text>\n'

        # Geographic center

        y = ycenter + self.layercfg.font_size * 1.25 / 2

        # Apparently dx and dy don't work on circles?
        svg += f'<circle cx="{x}" cy="{y}" r="{self.locationcfg.max_radius}" stroke-width="{self.locationcfg.stroke_width}" style="{self.locationcfg.style}"/>\n'

        svg += f'<text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="1em" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Geographic center</text>\n'

        # Chromosome location

        y = ycenter - self.layercfg.font_size * 1.25 / 2

        # TODO: Make a config for chromosome position circles and use it.
        svg += position.circle(x, y)

        svg += f'<text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="1em" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Chromosome location</text>\n'

        return svg


class PopulationHistogram(Legend):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.legend_population_histogram

        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        cursor = database.cursor()
        cursor.execute('SELECT COUNT(*) FROM population')
        self.population_count = cursor.fetchone()[0]

    def svg(self, variant=None):

        svg = ''
        if not variant or variant[f'order_{self.cfg.order}'] >= self.layercfg.start_order:

            shadow = drop_shadow.magenta_style if self.cfg.shadows else ''

            x = self.layercfg.width / 2

            y = self.layercfg.height / 2

            svg += f'<text text-anchor="middle" dominant-baseline="middle" x="{x}" y="{y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Population count</text>\n'

            svg += f'<text text-anchor="end" x="0" dx="-0.2em" y="{self.layercfg.height}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">1</text>\n'

            svg += f'<text text-anchor="start" x="{self.layercfg.width}" dx="0.2em" y="{self.layercfg.height}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{self.population_count}</text>\n'

        return svg

