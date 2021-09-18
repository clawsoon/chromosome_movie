#!/usr/bin/env python3

'''
This version composites everything together into a single SVG image per
frame, converts each frame with inkscape, then uses ffmpeg to create the movie.
It uses less disk space than layers.py.
'''

# Check environment to make sure we've got everything we need.
import pathlib
import tskit
import sqlite3
import numpy
import midiutil
import srt
#import config_ne2 as config
import config
#import config_1kg_bertin_short as config
assert pathlib.Path(config.treeseq).exists()
assert pathlib.Path(config.ffmpeg).exists()
assert pathlib.Path(config.inkscape).exists()
assert pathlib.Path(config.timidity).exists()


# And now the stuff we need for this script.
import sys
import chromosome_movie

if __name__ == '__main__':

    commands = sys.argv[1:]
    if not commands:
        print('Usage: run.py [command]')
        print('''Command can be any combination of:
        all
        database
        chromosome_map
        clef
        background
        order
        foreground
        audio
        movie
        preview
        ''')

    #for folder in config.folders:
    #    folder.mkdir(parents=True, exist_ok=True)

    if 'database' in commands or 'all' in commands:
        obj = chromosome_movie.database.Database(config)
        obj.write_db()

    if 'chromosome_map' in commands or 'all' in commands:
        obj = chromosome_movie.chromosome_map.ChromosomeMap(config)
        obj.write_db()

    if 'clef' in commands or 'all' in commands:
        obj = chromosome_movie.clef.Clef(config)
        obj.write_svg()

    if 'world_map' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.world_map.WorldMap(config)
        obj.write()

    if 'background' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.composite.Background(config)
        obj.write_svg()
        obj.write_png()

    if 'order' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.order.Order(config)
        obj.write_db()

    if 'foreground' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.composite.Foreground(config)
        obj.write_svg()
        obj.write_png()

    if 'audio' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.audio.Audio(config)
        obj.write_midi()

    if 'movie' in commands or 'all' in commands or 'reorder' in commands:
        obj = chromosome_movie.movie.Movie(config)
        obj.write_bg_fg_mp4()

    if 'preview' in commands:
        obj = chromosome_movie.movie.Movie(config, layer_names=['average_location', 'local_frequencies'])
        obj.write_concat()
        obj.write_preview()


