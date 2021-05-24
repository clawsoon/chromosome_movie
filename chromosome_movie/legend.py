#!/usr/bin/env python3

from xml.sax import saxutils

from . import svg2png
from . import drop_shadow
from . import chromosome_position


class Legend():

    def __init__(self, cfg):
        self.cfg = cfg

    def radius(self, proportion, cfg):
        return proportion**.5 * cfg.max_radius - cfg.stroke_width / 2

    def write_png(self):

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = [0]
        svg2png.svg2png(self.cfg, svg, png, frames)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % 0

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % 0
        


class Frequency(Legend):
    # The only reason we're subclassing is for the radius function.
    # Seems not quite worth it.

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.legend_frequency
        self.frequencycfg = self.cfg.layers.local_frequencies

    def write_svg(self):
        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'

        shadow = ''
        if self.cfg.shadows:
            svg += drop_shadow.filter
            shadow = drop_shadow.style

        for num, frequency in enumerate(self.layercfg.frequencies):
            percentage = saxutils.escape(f'{frequency*100:g}%')
            radius = self.radius(frequency, self.frequencycfg)

            circle_x = self.frequencycfg.max_radius * 2
            circle_y = self.layercfg.font_size * (num + 2)

            text_x = self.frequencycfg.max_radius * 5
            text_y = self.layercfg.font_size * (num + 2)

            svg += f'<circle cx="{circle_x}" cy="{circle_y}" r="{radius}" stroke-width="{self.frequencycfg.stroke_width}" style="{self.frequencycfg.style}"/>\n'

            svg += f'<text text-anchor="start" dominant-baseline="middle" x="{text_x}" y="{text_y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{percentage}</text>\n'

        svg += '</svg>\n'

        with open(self.svg_path(None, None), 'w') as output:
            output.write(svg)

class Position(Legend):

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = self.cfg.layers.legend_position
        self.locationcfg = self.cfg.layers.average_location
        self.positioncfg = self.cfg.layers.chromosome_position

    def write_svg(self):

        position = chromosome_position.ChromosomePosition(self.cfg)

        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'

        shadow = ''
        if self.cfg.shadows:
            svg += drop_shadow.filter
            shadow = drop_shadow.style

        x = self.layercfg.font_size

        ycenter = self.layercfg.height / 2
        y = ycenter - self.layercfg.font_size / 2

        # Apparently dx and dy don't work on circles?
        svg += f'<circle cx="{x}" cy="{y}" r="{self.locationcfg.max_radius}" stroke-width="{self.locationcfg.stroke_width}" style="{self.locationcfg.style}"/>\n'

        svg += f'<text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="1em" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Geographic center</text>\n'

        y = ycenter + self.layercfg.font_size / 2

        # TODO: Make a config for chromosome position circles and use it.
        svg += position.circle(x, y)

        svg += f'<text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="1em" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">Chromosome position</text>\n'

        svg += '</svg>\n'

        with open(self.svg_path(None, None), 'w') as output:
            output.write(svg)

