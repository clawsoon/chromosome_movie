#!/usr/bin/env python3

# Check environment to make sure we've got everything we need.
import pathlib
import tskit
import sqlite3
import numpy
import midiutil
import srt
import config
assert pathlib.Path(config.treeseq).exists()
assert pathlib.Path(config.ffmpeg).exists()
assert pathlib.Path(config.inkscape).exists()
assert pathlib.Path(config.timidity).exists()


# And now the stuff we need for this script.
import sys
import chromosome_movie

# Should we use argparse?  No.  I'm only doing this because Python doesn't
# allow the obvious and straightforward and widely-desired ability to have
# imports work the same way if a module in a package is imported or is run
# as a script.
# https://stackoverflow.com/questions/14132789/relative-imports-for-the-billionth-time
commands = sys.argv[1:]
if not commands:
    print('Usage: run.py [command]')
    print('''Command can be any combination of:
    all  (Skips layers not in config.movie_layers)
    reorder (Does caption, order, audio, movie)
    database
    chromosome_map
    chromosome_position
    world_map
    max_local
    average_location
    local_frequencies
    worldwide_frequency
    clef
    date
    caption
    order
    audio
    movie
    ''')

for folder in config.folders:
    folder.mkdir(parents=True, exist_ok=True)

# Make database from tskit info: Variants, locations.  DB.
# I've tried to make it so that running this twice doesn't result in
# any changes if the data stays the same.  If the data changes between
# runs, however - in particular if some variants are removed or
# some local frequencies go from non-zero to zero - the result will
# not be accurate.  Perhaps that's a sign that I should've instead
# looked into adding extra data fields and arbitrary ordering to treeseq.
if 'database' in commands or 'all' in commands:
    obj = chromosome_movie.database.Database(config)
    obj.write_db()

# Chromosome gilbert map lines.  DB, SVG, PNG.
# Add chromosome map table to DB. (map_index -> x,y)
if 'chromosome_map' in commands or ('all' in commands and 'chromosome_map' in config.movie_layers):
    obj = chromosome_movie.chromosome_map.ChromosomeMap(config)
    obj.write_db()
    obj.write_svg()
    obj.write_png()


# Chromosome gilbert map dots.  SVG, PNG.
# Number by index on gilbert map, one per index.
if 'chromosome_position' in commands or ('all' in commands and 'chromosome_position' in config.movie_layers):
    obj = chromosome_movie.chromosome_position.ChromosomePosition(config)
    obj.write_svg()
    obj.write_png()


# World map: Created via G.Projector.  PNG.
# Can we automate creation of this?  Probably, but not going to bother.
# For now this will just copy the default world map matching the
# config.layers.world_map defaults to the world map first frame path.
if 'world_map' in commands or ('all' in commands and 'world_map' in config.movie_layers):
    obj = chromosome_movie.world_map.WorldMap(config)
    obj.write_png()

# Dim grey circles at each location showing 100% for contrast with the
# local frequency red dots.
if 'max_local' in commands or ('all' in commands and 'max_local' in config.movie_layers):
    obj = chromosome_movie.locations.MaxLocal(config)
    obj.write_svg()
    obj.write_png()

# World map average location blue dots.  SVG, PNG.
# One per unique average location.
# Indexed by ID of first variant it appears in.
if 'average_location' in commands or ('all' in commands and 'average_location' in config.movie_layers):
    obj = chromosome_movie.locations.AverageLocation(config)
    obj.write_svg()
    obj.write_png()

# Convenience class to see all spots covered by average locations.  PNG.
# Not run by 'all'.
# Has an additional requirement of PIL.
if 'all_average_locations' in commands:
    obj = chromosome_movie.locations.AllAverageLocations(config)
    obj.write_png()

# World map local frequency red dots.  SVG, PNG.
# One per unique local frequency set.
# Indexed by ID of first variant it appears in.
if 'local_frequencies' in commands or ('all' in commands and 'local_frequencies' in config.movie_layers):
    obj = chromosome_movie.locations.LocalFrequencies(config)
    obj.write_svg()
    obj.write_png()

# Worldwide frequency circle and percentage text.  SVG, PNG.
# One per 0.1%, indexed 0...1000.
# TODO: Shadows option.
if 'worldwide_frequency' in commands or ('all' in commands and 'worldwide_frequency' in config.movie_layers):
    obj = chromosome_movie.worldwide_frequency.WorldwideFrequency(config)
    obj.write_svg()
    obj.write_png()

# Variant type clef.  SVG, PNG.
# Manually design in Inkscape, use SVG visibility to export PNGs.
# One per unique variant, indexed by FromTo.
if 'clef' in commands or ('all' in commands and 'clef' in config.movie_layers):
    obj = chromosome_movie.clef.Clef(config)
    obj.write_svg()
    obj.write_png()

# Date text.  SVG, PNG.
# One per unique date, indexed by date.
if 'date' in commands or ('all' in commands and 'date' in config.movie_layers):
    obj = chromosome_movie.text.Date(config)
    obj.write_svg()
    obj.write_png()

# Caption text.  SVG, PNG.
# Let's do this with SRT so that we can upload the captions to Youtube.
if 'caption' in commands or ('all' in commands and 'caption' in config.movie_layers):
    obj = chromosome_movie.text.Caption(config)
    obj.write_svg()
    obj.write_png()

# Variant traversal order.  DB.
# Travelling salesman, east to west, chunked.
# One variant table column per traversal order.
# TODO: Implement.
if 'order' in commands or 'all' in commands or 'reorder' in commands:
    obj = chromosome_movie.order.Order(config)
    obj.write_db()

# Variant type audio.  MIDI, WAV.
# TODO: Use specified order.
if 'audio' in commands or 'all' in commands or 'reorder' in commands:
    obj = chromosome_movie.audio.Audio(config)
    obj.write_midi()
    # If config.audio_pipe is specified, write_wav() does nothing
    # and instead the output of timidity is piped directly into ffmpeg
    # in the movie step, saving having to create a giant intermediate WAV file.
    obj.write_wav()

# Make movie.  PNG, WAV, MP4.
# TODO: Implement.
if 'movie' in commands or 'all' in commands or 'reorder' in commands:
    obj = chromosome_movie.movie.Movie(config)
    obj.write_concat()
    obj.write_mp4()


