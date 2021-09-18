#!/usr/bin/env python3

import os
import pathlib
from xml.etree import ElementTree

from . import svg2png

class Clef():

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = self.cfg.layers.clef

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        folder = pathlib.Path(__file__).parent
        template = open(folder/'clef.svg').read()
        tree = ElementTree.parse(folder/'clef.svg')
        root = tree.getroot()
        root.set('width', str(self.layercfg.width))
        root.set('height', str(self.layercfg.height))
        notes = {}
        if self.cfg.shadows:
            defs = root.find('{http://www.w3.org/2000/svg}defs')
            style = ElementTree.SubElement(defs, '{http://www.w3.org/2000/svg}style')
            style.text = '.shadow {filter:url(#dropshadow);}'
        for (In, Out), note in self.cfg.audio_notes.items():
            node = root.find(f".//*[@id='{note}']")
            content = f'{In}\u2192{Out}'
            node.text = content
            node.set('style', 'display:inline')
            if note == 'C4':
                line = root.find(f".//*[@id='line{note}']")
                line.set('style', 'display:inline')
            variant = {'ancestral_state': In, 'derived_state': Out}
            tree.write(self.svg_path(variant), encoding='utf8', xml_declaration=True)
            node.set('style', 'display:none')
            if note == 'C4':
                line.set('style', 'display:none')

    def write_png(self):

        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)

        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = self.cfg.audio_notes.values()
        svg2png.svg2png(self.cfg, svg, png, frames, frame_convert=str)

    def index(self, variant):
        key = (variant['ancestral_state'], variant['derived_state'])
        return self.cfg.audio_notes[key]

    def svg(self, variant):
        path = os.path.relpath(self.svg_path(variant), self.cfg.layers.foreground.svg.parent).replace('\\', '/')
        # Using <image> for the map gives horrible resolution, but for
        # the clef it's fine.  I guess because we're scaling down here
        # instead of scaling up like we are with the map?
        #return f' <use xlink:href="{path}#clef"/>\n'
        return f' <image width="{self.layercfg.width}" height="{self.layercfg.height}" xlink:href="{path}"/>\n'

    def svg_path(self, variant):
        return str(self.layercfg.svg) % self.index(variant)

    def png_path(self, variant):
        return str(self.layercfg.png) % self.index(variant)


