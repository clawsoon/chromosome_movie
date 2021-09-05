import datetime
from xml.sax import saxutils
import sqlite3

import srt

from . import svg2png
from . import drop_shadow

class Text():

    def __init__(self, cfg):
        self.cfg = cfg
        self.order_key = f'order_{self.cfg.order}'

    def text(self, contents):
        lines = contents.split('\n')
        svg = ''
        shadow = drop_shadow.style if self.cfg.shadows else ''

        #offsets = [f'{-.5*(len(lines)-1)+i}em' for i in range(len(lines))]
        offsets = []
        offset = 0
        for line in lines:
            offsets.append(offset)
            # Give blank lines half a line.
            offset += 1 if line.strip() else 0.5
        half = offsets[-1] / 2
        offsets = [f'{offset - half}em' for offset in offsets]

        for offset, line in zip(offsets, lines):
            escaped = saxutils.escape(line)
            #x, y = self.layercfg.center
            x = self.layercfg.width / 2
            y = self.layercfg.height / 2
            svg += f'<text text-anchor="middle" dominant-baseline="middle" x="{x}" y="{y}" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{escaped}</text>\n'
        return svg

    def write_svg_file(self, path, contents):
        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'
        if self.cfg.shadows:
            svg += drop_shadow.filter
        self += contents
        svg += '</svg>'
        with open(path, 'w') as output:
            output.write(svg)

    def write_png(self):
        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, self.select(), frame_convert=self.index)

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)


class Subtitle(Text):

    # This module will be inefficient if we have a large number of subtitles.
    def __init__(self, cfg):
        super().__init__(cfg)
        self.count = 0
        # Inefficiency #1: Converting the generator to a list.
        self.subtitles = list(srt.parse(open(self.layercfg.srt, encoding='utf-8').read()))

    def index(self, variant, return_subtitle=False):
        # Inefficiency #2: Looping through the list for every search.
        frame = variant[self.order_key]
        time = datetime.timedelta(seconds=(frame / self.cfg.video_framerate))
        for num, subtitle in enumerate(self.subtitles):
            if subtitle.start <= time < subtitle.end:
                if self.layercfg.typing == 'words':
                    index = self.count
                    self.count += 1
                    words = subtitle.content.split()
                    subindex = (time - subtitle.start).total_seconds() * self.cfg.video_framerate
                    content = ' '.join(words[:int(subindex+1)])
                elif self.layercfg.typing == 'letters':
                    index = self.count
                    self.count += 1
                    subindex = (time - subtitle.start).total_seconds() * self.cfg.video_framerate
                    content = subtitle.content[:int(subindex+1)]
                else:
                    index = num
                    content = subtitle.content
                break
                #if return_subtitle:
                #    return subtitle
                #else:
                #    return index
                #    #return subtitle.index
        else:
            content = None
            index = 99999999
        if return_subtitle:
            return content
        else:
            return index

    def svg(self, variant):
        content = self.index(variant, return_subtitle=True)
        return self.text(content) if content else ''

    def write_svg(self):
        # FIXME: This does not match self.svg() if self.layercfg.typing.
        for index, subtitle in enumerate(self.subtitles):
            path = str(self.layercfg.svg) % index
            self.write_svg_file(path, self.svg(variant))
        # Blank frame.
        path = str(self.layercfg.svg) % 99999999
        self.write_svg_file(path, '')

    def select(self):
        if self.layercfg.typing == 'words':
            indexes = range(sum(len(subtitle.content.split()) for subtitle in self.subtitles))
        elif self.layercfg.typing == 'letters':
            indexes = range(sum(len(subtitle.content) for subtitle in self.subtitles))
        else:
            indexes = range(len(self.subtitles))
        for index in indexes:
            yield index
        yield 99999999

    def write_png(self):
        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, self.select())


class Caption(Subtitle):
    def __init__(self, cfg):
        self.layercfg = cfg.layers.caption
        super().__init__(cfg)


class Citation(Subtitle):
    def __init__(self, cfg):
        self.layercfg = cfg.layers.citation
        super().__init__(cfg)


class Date(Text):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.date

    def index(self, variant):
        # Skipping by ten seems like a reasonable way to capture
        # one decimal digit of date.
        return int(10 * variant['time'])

    def select(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        cursor.execute('SELECT DISTINCT time FROM variant')
        return cursor

    def svg(self, variant):
        return self.text(f'{int(self.layercfg.multiplier*variant["time"]):,}\nyears ago')

    def write_svg(self):
        for variant in self.select():
            self.write_svg_file(self.svg_path(variant), self.svg(variant))

class Variant(Text):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.layercfg = self.cfg.layers.variant

    def index(self, variant):
        return variant[self.order_key]

    def select(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        cursor.execute(f'SELECT id, chromosome_position, {self.order_key} FROM variant ORDER BY {self.order_key}')
        return cursor

    def svg(self, variant):
        content = [
            # TODO: Will the other trees have the same site ID?
            ('Site:', f'22_{int(variant["chromosome_position"])}'),
            ('Count:', f'{variant[self.order_key]+1:,}'),
            #('Position: ', f'{variant["chromosome_position"]:,}'),
        ]
        svg = ''
        shadow = drop_shadow.style if self.cfg.shadows else ''
        # Center multiple lines of text vertically.
        offsets = [f'{-.5*(len(content)-1)+i}em' for i in range(len(content))]
        for offset, line in zip(offsets, content):
            left = saxutils.escape(line[0])
            right = saxutils.escape(line[1])
            #x, y = self.layercfg.center
            x = self.layercfg.width / 2
            y = self.layercfg.height / 2
            svg += f'<text text-anchor="end" dominant-baseline="middle" x="{x}" y="{y}" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{left}</text>\n'
            svg += f'<text text-anchor="start" dominant-baseline="middle" x="{x}" y="{y}" dx="0.5em" dy="{offset}" font-size="{self.layercfg.font_size}" style="{self.layercfg.style}{shadow}">{right}</text>\n'
        return svg

    def write_svg(self):
        for variant in self.select():
            self.write_svg_file(self, self.svg_path(variant), self.svg(variant))

