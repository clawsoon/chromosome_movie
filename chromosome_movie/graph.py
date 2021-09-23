import collections
import sqlite3

from . import svg2png

class Graph():

    def __init__(self, cfg):
        self.cfg = cfg
        self.order_key = f'order_{self.cfg.order}'

        self.window = collections.deque(maxlen=self.layercfg.deque_length)
        self.frequencies = collections.Counter()

        self.database = sqlite3.connect(cfg.database_readonly_uri, uri=True)
        self.database.row_factory = sqlite3.Row

    def write_svg(self, path, contents):
        svg = f'<svg viewBox="0 0 {self.layercfg.width} {self.layercfg.height}" xmlns="http://www.w3.org/2000/svg">\n'
        svg += contents
        svg += '</svg>'
        with open(path, 'w') as output:
            output.write(svg)

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, self.select(), frame_convert=self.index)

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)


class PopulationHistogram(Graph):

    def __init__(self, cfg):
        self.layercfg = cfg.layers.population_histogram
        super().__init__(cfg)

    def index(self, variant):
        return variant[self.order_key]

    def select(self):
        cursor = self.database.cursor()
        sql = f'SELECT population_counts_match_variant_id FROM variant ORDER BY {self.order_key}'
        return cursor

    def svg(self, variant):

        svg = ''

        cursor = self.database.cursor()
        cursor.execute('''
            SELECT
                COUNT(*)
            FROM
                variant_population
            WHERE
                variant_id = ?
        ''', (variant['population_counts_match_variant_id'],))

        count = cursor.fetchone()[0]
        if len(self.window) == self.layercfg.deque_length:
            popped_count = self.window.popleft()
            self.frequencies[popped_count] -= 1
        self.frequencies[count] += 1
        self.window.append(count)

        for count, frequency in self.frequencies.items():
            x = self.layercfg.bar_width * count
            height = self.layercfg.bar_height * frequency
            y = self.layercfg.height - height
            svg += f'<rect x="{x}" y="{y}" width="{self.layercfg.bar_width}" height="{height}" style="{self.layercfg.style}"/>\n'

        return svg

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        for variant in self.select():
            self.write_svg_file(self, self.svg_path(variant), self.svg(variant))


class VariantHistogram(Graph):

    def __init__(self, cfg):
        self.layercfg = cfg.layers.variant_histogram
        super().__init__(cfg)

    def index(self, variant):
        return variant[self.order_key]

    def select(self):
        cursor = self.database.cursor()
        sql = f'SELECT ancestral_state, derived_state FROM variant ORDER BY {self.order_key}'
        return cursor

    def svg(self, variant):

        svg = ''

        if len(self.window) == self.layercfg.deque_length:
            popped_state = self.window.popleft()
            self.frequencies[popped_state] -= 1
        state = (variant['ancestral_state'], variant['derived_state'])
        self.frequencies[state] += 1
        self.window.append(state)

        for state, frequency in self.frequencies.items():
            width = self.layercfg.bar_width * (frequency / self.layercfg.deque_length)
            x = self.layercfg.width - width
            y = self.layercfg.bar_height * self.cfg.audio_notes[state]['index']
            svg += f'<rect x="{x}" y="{y}" width="{width}" height="{self.layercfg.bar_height}" style="{self.layercfg.style}"/>\n'

        return svg

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        for variant in self.select():
            self.write_svg_file(self, self.svg_path(variant), self.svg(variant))

