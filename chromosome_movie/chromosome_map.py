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


    def svg(self, variant=None):
        if not self.map:
            self.initialize()
        return '\n'.join(self.map.generate_svg()) + '\n'

    def write_svg(self):

        self.layercfg.svg.parent.mkdir(parents=True, exist_ok=True)

        svg = f'<svg viewBox="0 0 {self.cfg.width} {self.cfg.height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        svg += self.svg()
        svg += '</svg>\n'

        with open(self.svg_path(), 'w') as svg:
            svg.write(self.svg())

    def write_png(self):
        self.layercfg.png.parent.mkdir(parents=True, exist_ok=True)
        svg2png.svg2png(self.cfg, self.svg_path(), self.png_path())

    def svg_path(self, variant=None):
        return str(self.layercfg.svg)

    def png_path(self, variant=None):
        return str(self.layercfg.png)


