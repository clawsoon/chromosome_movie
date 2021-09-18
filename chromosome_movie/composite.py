#!/usr/bin/env python3

import os
import pathlib
import sqlite3

from . import chromosome_map, chromosome_position, world_map, locations, worldwide_frequency, clef, text, legend, drop_shadow, svg2png, order

class Composite():

    def __init__(self, cfg, default_layer_names, layer_names=None):
        self.cfg = cfg

        self.layer_names = layer_names or default_layer_names

        self.classes = {
            'chromosome_map': chromosome_map.ChromosomeMap,
            'chromosome_position': chromosome_position.ChromosomePosition,
            'world_map': world_map.WorldMap,
            'max_local': locations.MaxLocal,
            'graticule_vertices': locations.GraticuleVertices,
            'average_location': locations.AverageLocation,
            'local_frequencies': locations.LocalFrequencies,
            'traces': locations.Traces,
            'worldwide_frequency': worldwide_frequency.WorldwideFrequency,
            'clef': clef.Clef,
            'variant': text.Variant,
            'populations': text.Populations,
            'legend_frequency': legend.Frequency,
            'legend_position': legend.Position,
            'date': text.Date,
            'caption': text.Caption,
            'citation': text.Citation,
        }

        self.layers = {}
        for name in self.layer_names:
            self.layers[name] = getattr(self.cfg.layers, name)
            self.layers[name].obj = self.classes[name](self.cfg)

    def translate(self, layer):
        transforms = []
        if hasattr(layer, 'center'):
            #print(f' center: {layer.center}')
            left = 0
            top = 0
            if hasattr(layer, 'width'):
                #print(f' width: {layer.width}')
                left = layer.center[0] - layer.width / 2
                #width = layer.width
            else:
                raise Exception('.center without .width')
            #    left = layer.center[0] - self.cfg.width / 2
            #    width = self.cfg.width
            #print(f' left: {left}')
            if hasattr(layer, 'height'):
                #print(f' height: {layer.height}')
                top = layer.center[1] - layer.height / 2
                #height = layer.height
            else:
                raise Exception('.center without .height')
            #    top = layer.center[1] - self.cfg.height / 2
            #    height = self.cfg.height
            #print(f' top: {top}')
            # Here we end up not using width and height, unlike the ffmpeg
            # layering.  Interesting.
            if left != 0 or top != 0:
                transforms.append(f'translate({left} {top})')
        if hasattr(layer, 'scale') and layer.scale != 1:
            transforms.append(f'scale({layer.scale} {layer.scale})')
        if transforms:
            text = ' '.join(transforms)
            svg = (f'<g transform="{text}">\n', '</g>\n')
        else:
            svg = None
        return svg


class Foreground(Composite):

    def __init__(self, cfg, layer_names=None):
        super().__init__(cfg, cfg.foreground_layers, layer_names=layer_names)
        self.layercfg = self.cfg.layers.foreground

        self.order_key = f'order_{self.cfg.order}'

        self.order = order.Order(cfg)

    #def select(self):
    #    database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
    #    database.row_factory = sqlite3.Row
    #    cursor = database.cursor()
    #    select = f'SELECT * FROM variant'
    #    if self.cfg.movie_time:
    #        select += f' WHERE time={self.cfg.movie_time}'
    #    select += f' ORDER BY {self.order_key}'
    #    if self.cfg.movie_limit:
    #        select += f' LIMIT {self.cfg.movie_limit}'
    #    cursor.execute(select)
    #    return cursor

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        #background_path = os.path.relpath(self.cfg.layers.background.svg, self.cfg.layers.composite.svg.parent).replace('\\', '/')
        #for variant in self.select():
        for variant in self.order.select():
            # In theory we could unify the contents of this loop with the
            # almost-identical background function.  Let's wait on that,
            # though, in case they diverge.
            svg = f'<svg viewBox="0 0 {self.cfg.width} {self.cfg.height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            if self.cfg.shadows:
                svg += drop_shadow.filter
            #svg += f' <image xlink:href="{background_path}" x="0" y="0" width="{self.cfg.width}" height="{self.cfg.height}"/>\n'
            for name in self.layer_names:
                #print(f'layer: {name}')
                layer = self.layers[name]
                contents = layer.obj.svg(variant)
                if not contents:
                    continue
                translate = self.translate(layer)
                if translate:
                    svg += translate[0]
                svg += contents
                if translate:
                    svg += translate[1]
            svg += '</svg>\n'
            with open(self.svg_path(variant), 'w', encoding='utf-8') as output:
                output.write(svg)

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        #svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, self.select(), frame_convert=self.index)
        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, self.order.select(), frame_convert=self.index)

    def index(self, variant):
        #return variant[self.order_key]
        return variant['frame_number']

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)


class Background(Composite):

    def __init__(self, cfg, layer_names=None):
        super().__init__(cfg, cfg.background_layers, layer_names=layer_names)
        self.layercfg = self.cfg.layers.background

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        svg = f'<svg viewBox="0 0 {self.cfg.width} {self.cfg.height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        if self.cfg.shadows:
            svg += drop_shadow.filter
        for name in self.layer_names:
            layer = self.layers[name]
            translate = self.translate(layer)
            if translate:
                svg += translate[0]
            svg += layer.obj.svg()
            if translate:
                svg += translate[1]
        svg += '</svg>\n'
        with open(self.layercfg.svg, 'w') as output:
            output.write(svg)

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg2png.svg2png(self.cfg, self.layercfg.svg, self.layercfg.png, inkscape_actions='export-background:white;export-png-color-mode:RGB_8;')

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)

