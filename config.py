#!/usr/bin/env python3

import pathlib
import shutil


chromosome = '22'

# Path to source treeseq file.
treeseq = 'sgdp_chr22.trees'

# Different treeseqs store location data differently.
# Modify database.Database.get_location() to add more choices.
treeseq_type = 'sgdp'

# This needs to be a valid SQL table name, since that what it's going to become.
# See the order module to add choices.
#order = 'traveller_45e_30s_105w_40s'
order = 'traveller_19e_39s_99w_19n'
#order = 'traveller_19e_39s_99w_19n_max1000'
#order = 'average_longitude'


# Video parameters.
width = 2560
height = 1440
resolution = (width, height)
# 8 fps gives a Youtube viewer a range of 2fps to 16fps, which seems to be
# a reasonable range for this particular movie.
video_framerate = 8
#video_framerate = 2
audio_samplerate = 48000

# Required executables.
#ffmpeg = '/usr/bin/ffmpeg'
ffmpeg = shutil.which('ffmpeg') or r'C:\Program Files\ImageMagick-7.0.11-Q16-HDRI\ffmpeg.exe'
#inkscape = '/usr/bin/inkscape'
inkscape = shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.exe'
timidity = shutil.which('timidity') or r'C:\Program Files (x86)\TiMidity\timidity.exe'

treeseq_path = pathlib.Path(treeseq)

# Use the basename of the treeseq file as our working directory.
working = pathlib.Path('.')/treeseq_path.stem
data = working/'data'
images = working/'layers'
audio = working/'audio'
movie = working/'movie'

# Collect a list of folders to create at the end.
folders = [data, images, audio, movie]

database_path = data/f'{treeseq_path.stem}.sqlite'
database_readonly_uri = f'file:{database_path.as_posix()}?mode=ro'

class Stub():
    pass

layer_names = [
    'world_map',
    'chromosome_map',
    'chromosome_position',
    'worldwide_frequency',
    'clef',
    'max_local',
    'average_location',
    'local_frequencies',
    'caption',
    'date',
]

movie_layers = [
    'world_map',
    'chromosome_map',
    'chromosome_position',
    #'worldwide_frequency',
    'clef',
    #'max_local',
    'average_location',
    'local_frequencies',
    'caption',
    'date',
]

# Adds some shadows to text and lines to make lines a little cleaner when
# movies are resized to arbitrary sizes by the viewer, or when high-resolution
# movies are viewed on low-resolution screens.  It's a hack, but it seems to
# kinda work.
shadows = True

layers = Stub()
for name in layer_names:
    layer = Stub()
    setattr(layers, name, layer)
    shadowfolder = name + ('_shadows' if shadows else '')
    if name == 'average_location':
        # Average location indexing on longitude_latitude.
        layer.svg = images/name/'svg'/f'{name}.%s_%s.svg'
        layer.png = images/name/'png'/f'{name}.%s_%s.png'
    elif name == 'clef':
        # Clef indexing on note name.
        layer.svg = images/shadowfolder/'svg'/f'{name}.%s.svg'
        layer.png = images/shadowfolder/'png'/f'{name}.%s.png'
    elif name in ['chromosome_map', 'caption', 'date', 'worldwide_frequency']:
        # Only use shadows for black lines/text.
        layer.svg = images/shadowfolder/'svg'/f'{name}.%08d.svg'
        layer.png = images/shadowfolder/'png'/f'{name}.%08d.png'
    else:
        # Everything else has a more conventional index.
        layer.svg = images/name/'svg'/f'{name}.%08d.svg'
        layer.png = images/name/'png'/f'{name}.%08d.png'
    # ffmpeg concat files, used so that we only have to generate the frames
    # once and can assemble them in arbitrary order to make the movie.
    layer.concat = movie/order/f'{name}.concat'
    folders.append(layer.svg.parent)
    folders.append(layer.png.parent)
    folders.append(layer.concat.parent)

layers.chromosome_map.sections = [
    {'axis': 'width', 'start': (1248, 1280), 'end': (1120, 1320)},
    {'axis': 'width', 'start': (1120, 1280), 'end': (0, 1440)},
    {'axis': 'height', 'start': (0, 1280), 'end': (160, 160)},
    {'axis': 'width', 'start': (0, 160), 'end': (2560, 0)},
    {'axis': 'height', 'start': (2560, 160), 'end': (2400, 1280)},
    {'axis': 'width', 'start': (2560, 1280), 'end': (1440, 1440)},
    {'axis': 'width', 'start': (1440, 1280), 'end': (1312, 1320)},
]
layers.chromosome_map.radius = 8

default_world_map = images/'blue_marble_natural_earth_2_minus_150.png'
# We mostly use these world_map config items in the AverageLocationDots and
# LocalFrequencyDots classes, in order to place the dots correctly.
layers.world_map.rotation = -150
layers.world_map.projection = 'natural_earth_2'
layers.world_map.center = (int(0.5*width), int((1440/2-36)/1440*height))
layers.world_map.height = int(1024/1440*height)
layers.world_map.width = int(2048/1440*height)

layers.max_local.max_radius = 16/1440*height
layers.max_local.stroke_width = 0
layers.max_local.style = 'stroke:none;fill:black;fill-opacity:0.3;'

layers.average_location.max_radius = 12/1440*height
layers.average_location.stroke_width = 0
layers.average_location.style = 'stroke:none;fill:blue;fill-opacity:1.0;'

layers.local_frequencies.max_radius = 16/1440*height
# We need stroke width separated out from the style for calculations.
layers.local_frequencies.stroke_width = 4
layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'

layers.worldwide_frequency.center = (int(220/2560*width), int(220/1440*height))
layers.worldwide_frequency.max_radius = int(100/1440*height)
# We need stroke width separated out from the style for calculations.
layers.worldwide_frequency.stroke_width = 4
layers.worldwide_frequency.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'
layers.worldwide_frequency.backing_style = 'stroke:none;fill:grey;fill-opacity:0.4;'
layers.worldwide_frequency.font_size = int(54/height*1440)
layers.worldwide_frequency.text_style = 'font-family:sans-serif;'

# We're measuring clef from top left instead of centre.
# Maybe it would be easier for ffmpeg setup to use centre for all layers?
# In which case change this position to a center measurement.
layers.clef.center = (2264/2560*width, 296/1440*height)
layers.clef.width = 280/1440*height
layers.clef.height = 280/1440*height

layers.caption.center = (int(0.5*width), int(1240/1440*height))
layers.caption.font_size = int(height*72/1440)
layers.caption.height = layers.caption.font_size * 2
layers.caption.style = 'font-family:sans-serif;'
layers.caption.captions = pathlib.Path(__file__).parent/'captions.srt'

layers.date.center = (int(0.5*width), int(1380/1440*height))
layers.date.font_size = int(height*54/1440)
layers.date.height = layers.date.font_size * 3
layers.date.style = 'font-family:sans-serif;'
layers.date.multiplier = 10000

movie_limit = 0 # Limit the number of frames created.  0 = no limit.
movie_time = 20 # Select a specific time.  0 = all times.

audio_midi = audio/f'{order}_{movie_limit}.midi'
audio_wav = audio/f'{order}_{movie_limit}.wav'
audio_midi_program = 46
audio_pipe = True

audio_notes = {
    ('A', 'C'): 'G5',
    ('T', 'G'): 'F5',
    ('G', 'C'): 'E5',
    ('A', 'G'): 'D5',
    ('T', 'C'): 'C5',
    ('A', 'T'): 'B4',
    ('C', 'T'): 'A4',
    ('G', 'A'): 'G4',
    ('C', 'G'): 'F4',
    ('G', 'T'): 'E4',
    ('C', 'A'): 'D4',
    ('T', 'A'): 'C4',
}

movie_mp4 = movie/f'{order}_{"shadows" if shadows else "noshadows"}_{movie_time}_{movie_limit}.mp4'


