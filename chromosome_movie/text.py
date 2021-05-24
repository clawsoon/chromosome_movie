import datetime
from xml.sax import saxutils
import sqlite3

import srt

from . import svg2png
from . import drop_shadow

class Text():

    def __init__(self, cfg):
        self.cfg = cfg

    def make_svg(self, content, path):
        lines = content.split('\n')
        svg = f'<svg viewBox="0 0 {self.cfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'
        shadow = ''
        if self.cfg.shadows:
            svg += drop_shadow.filter
            shadow = drop_shadow.style
        # Center multiple lines of text vertically.
        offsets = [f'{-.5*(len(lines)-1)+i}em' for i in range(len(lines))]
        for offset, line in zip(offsets, lines):
            escaped = saxutils.escape(line)
            svg += f'<text text-anchor="middle" dominant-baseline="middle" x="50%" y="50%" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{escaped}</text>'
        svg += '</svg>'

        with open(path, 'w') as output:
            output.write(svg)

    def write_png(self):
        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.select(), frame_convert=self.index)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % self.index(variant, frame)

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % self.index(variant, frame)


class Caption(Text):

    # This module will be inefficient if we have a large number of subtitles.
    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.caption
        # Inefficiency #1: Converting the generator to a list.
        self.subtitles = list(srt.parse(open(self.layercfg.captions).read()))

    def index(self, variant, frame):
        # Inefficiency #2: Looping through the list for every search.
        time = datetime.timedelta(seconds=(frame / self.cfg.video_framerate))
        for subtitle in self.subtitles:
            if subtitle.start <= time <= subtitle.end:
                return subtitle.index
        return 0

    def frames(self):
        return [0] + [subtitle.index for subtitle in self.subtitles]

    def write_svg(self):
        for subtitle in self.subtitles:
            path = str(self.layercfg.svg) % subtitle.index
            self.make_svg(subtitle.content, path)
        # Zero-th frame is blank.
        path = str(self.layercfg.svg) % 0
        self.make_svg('', path)

    def write_png(self):
        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        svg2png.svg2png(self.cfg, svg, png, self.frames())


class Date(Text):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.date

    def index(self, variant, frame=None):
        # Skipping by ten seems like a reasonable way to capture
        # one decimal digit of date.
        return int(10 * variant['time'])

    def select(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        cursor.execute('SELECT DISTINCT time FROM variant')
        return cursor

    def write_svg(self):
        for variant in self.select():
            path = self.svg_path(variant, None)
            content = f'{int(self.layercfg.multiplier*variant["time"]):,}\nyears ago'
            self.make_svg(content, path)

class Variant(Text):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.variant

    def index(self, variant, frame=None):
        return variant['id']

    def select(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        cursor.execute('SELECT id, chromosome_position, %s FROM variant WHERE id=3879' % self.cfg.order)
        return cursor

    def write_svg(self):
        for variant in self.select():
            path = self.svg_path(variant, None)
            content = [
                # TODO: Will the other trees have the same site ID?
                ('Site:', f'22_{int(variant["chromosome_position"])}'),
                ('Count:', f'{variant[self.cfg.order]:,}'),
                #('Position: ', f'{variant["chromosome_position"]:,}'),
            ]
            self.make_svg(content, path)

    def make_svg(self, content, path):
        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'
        shadow = ''
        if self.cfg.shadows:
            svg += drop_shadow.filter
            shadow = drop_shadow.style
        # Center multiple lines of text vertically.
        offsets = [f'{-.5*(len(content)-1)+i}em' for i in range(len(content))]
        for offset, line in zip(offsets, content):
            left = saxutils.escape(line[0])
            right = saxutils.escape(line[1])
            svg += f'<text text-anchor="end" dominant-baseline="middle" x="50%" y="50%" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{left}</text>'
            svg += f'<text text-anchor="start" dominant-baseline="middle" x="50%" y="50%" dx="0.5em" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{right}</text>'
        svg += '</svg>'

        with open(path, 'w') as output:
            output.write(svg)


