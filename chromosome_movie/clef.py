#!/usr/bin/env python3

import pathlib
from xml.etree import ElementTree

from . import svg2png

class Clef():

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = self.cfg.layers.clef

    def write_svg(self):
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
            tree.write(self.svg_path(variant, None), encoding='utf8', xml_declaration=True)
            node.set('style', 'display:none')
            if note == 'C4':
                line.set('style', 'display:none')

    def write_png(self):
        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = self.cfg.audio_notes.values()
        svg2png.svg2png(self.cfg, svg, png, frames, frame_convert=str)

    def index(self, variant, frame):
        key = (variant['ancestral_state'], variant['derived_state'])
        return self.cfg.audio_notes[key]

    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % self.index(variant, frame)

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % self.index(variant, frame)


