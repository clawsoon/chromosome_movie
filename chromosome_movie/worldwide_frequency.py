from . import svg2png

class WorldwideFrequency():

    steps = 1000

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = self.cfg.layers.worldwide_frequency

    def make_svg(self, i):
        svg = f'<svg viewBox="0 0 {self.cfg.width} {self.cfg.height}" xmlns="http://www.w3.org/2000/svg">\n'

        # Backing circle.
        svg += f'<circle cx="{self.layercfg.center[0]}" cy="{self.layercfg.center[1]}" r="{self.layercfg.max_radius}" style="{self.layercfg.backing_style}"/>\n'

        # Scale by area.
        radius = self.layercfg.max_radius * (i/self.steps)**0.5 - self.layercfg.stroke_width / 2
        svg += f'<circle cx="{self.layercfg.center[0]}" cy="{self.layercfg.center[1]}" r="{radius}" stroke-width="{self.layercfg.stroke_width}" style="{self.layercfg.style}"/>\n'

        percentage = round(100 * i / self.steps, 1)
        x = self.layercfg.center[0] + self.layercfg.font_size * 2
        y = self.layercfg.center[1] + self.layercfg.max_radius + self.layercfg.font_size
        svg += f'<text text-anchor="end" x="{x}" y="{y}" font-size="{self.layercfg.font_size}" style="{self.layercfg.text_style}">{percentage}%</text>\n'

        svg += '</svg>\n'

        return svg

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        for i in range(self.steps + 1):
            path = str(self.layercfg.svg) % i
            with open(path, 'w') as svg:
                svg.write(self.make_svg(i))

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = range(self.steps+1)
        svg2png.svg2png(self.cfg, svg, png, frames)

    def normalize(self, amount):
        return int(amount*self.steps)

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % self.normalize(variant['worldwide_frequency'])

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % self.normalize(variant['worldwide_frequency'])

