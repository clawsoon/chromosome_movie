#!/usr/bin/env python3

import sqlite3

import tskit

from . import curved_gilbert, svg2png

class ChromosomeMap():

    def __init__(self, cfg):
        self.cfg = cfg
        self.layercfg = cfg.layers.chromosome_map

        self.map = None

    def initialize(self):

        self.map = curved_gilbert.CurvedGilbert(sections=self.layercfg.sections, radius=self.layercfg.radius, width=self.cfg.width, height=self.cfg.height, shadows=self.cfg.shadows)


    def write_db(self):

        # Should the table creation go into database.py?  Probably.

        if not self.map:
            self.initialize()

        database = sqlite3.connect(self.cfg.database_path)
        cursor = database.cursor()
        cursor.execute('SELECT first_site, last_site FROM chromosome WHERE name=?', (self.cfg.chromosome,))
        first_site, last_site = cursor.fetchone()

        mapped_length = last_site - first_site + 1
        map_length = len(self.map.points)

        rate = map_length / mapped_length
        offset = first_site

        cursor.execute('''
            UPDATE
                chromosome
            SET
                map_rate=?,
                map_offset=?
            WHERE
                name=?
            ''', (rate, offset, self.cfg.chromosome))

        # Using "INT PRIMARY KEY" trick so that we don't get stomped by rowid.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chromosome_map (
                map_index INT PRIMARY KEY,
                x INTEGER,
                y INTEGER
            );
        ''')

        for index, (x, y) in enumerate(self.map.points):
            cursor.execute('''
                INSERT INTO chromosome_map
                    (
                        map_index,
                        x,
                        y
                    )
                VALUES
                    (?, ?, ?)
                ON CONFLICT
                    (map_index)
                DO UPDATE SET
                    x=?,
                    y=?
                ''', (index, x, y, x, y))

        database.commit()
        database.close()


    def write_svg(self):

        if not self.map:
            self.initialize()

        path = str(self.layercfg.svg) % 0
        with open(path, 'w') as svg:
            for line in self.map.generate_svg():
                svg.write(f'{line}\n')

    def write_png(self):
        svg = str(self.layercfg.svg)
        png = str(self.layercfg.png)
        frames = [0]
        svg2png.svg2png(self.cfg, svg, png, frames)


    def svg_path(self, variant, frame):
        return str(self.layercfg.svg) % 0

    def png_path(self, variant, frame):
        return str(self.layercfg.png) % 0


