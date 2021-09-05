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
#order = 'average_longitude'
#order = 'traveller_45e_30s_105w_40s'
#order = 'traveller_19e_39s_99w_19n'
#order = 'traveller_roundtrip_19e_39s_max480'
#order = 'traveller_19e_39s_99w_19n_max1000'
#order = 'traveller_roundtrip_19e_39s_max1000_byspread'
#order = 'traveller_roundtrip_19e_39s_max480_byspread'
#order = 'total_distance_to_average_location'
#order = 'two_world_30w_65s_169w_65n_max480'
#order = 'two_world_30w_0s_169w_65n_max480'
#order = 'two_world_jaccard5_30w_30s_169w_65n_max480'
order = 'two_world_jaccard20_30w_30s_169w_65n_max480'


# Video parameters.
width = 1440
height = 1440
resolution = (width, height)
# 8 fps gives a Youtube viewer a range of 2fps to 16fps, which seems to be
# a reasonable range for this particular movie.
video_framerate = 8
#video_framerate = 2
audio_samplerate = 48000

# Required executables.
#ffmpeg = '/usr/bin/ffmpeg'
ffmpeg = shutil.which('ffmpeg') or r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
#inkscape = '/usr/bin/inkscape'
inkscape = shutil.which('inkscape') or r'C:\Program Files\Inkscape\bin\inkscape.exe'
timidity = shutil.which('timidity') or r'C:\Program Files (x86)\TiMidity\timidity.exe'

treeseq_path = pathlib.Path(treeseq)

# We have to look for a couple of things in the code directory.
code = pathlib.Path(__file__).parent

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
    'graticule_vertices',
    'average_location',
    'all_average_locations',
    'local_frequencies',
    'legend_frequency',
    'legend_position',
    'variant',
    'caption',
    'date',
]

movie_layers = [
    'world_map',
    'chromosome_map',
    'chromosome_position',
    'clef',
    'average_location',
    'local_frequencies',
    'legend_frequency',
    'legend_position',
    #'variant',
    'caption',
    'date',
]

# Adds some shadows to text and lines to make lines a little cleaner when
# movies are resized to arbitrary sizes by the viewer, or when high-resolution
# movies are viewed on low-resolution screens.  It's a hack, but it seems to
# kinda work.
shadows = True

#map_image = 'blue_marble'
#map_projection = 'natural_earth_2'
#map_rotation = (-150, 0)  # I like either -11 or -150.
map_image = 'visionscarto_lightblue'
map_projection = 'bertin' # Bertin doesn't pay attention to rotation.
map_rotation = (-16.5, -42)

# Map images have to be manually created for now.
# I've been using G.Projector and GIMP.
default_world_map = code/'maps'/f'{map_image}_{map_projection}_{map_rotation[0]}_{map_rotation[1]}.png'

map_center = (int(0.5*width), int((1440/2-36)/1440*height))
map_height = int(1024/1440*height)
map_width = int(2048/1440*height)

shadowfolder = images/('shadows' if shadows else 'noshadows')
mapfolder = images/f'{map_projection}_{map_rotation[0]}_{map_rotation[1]}'

layers = Stub()
for name in layer_names:
    layer = Stub()
    setattr(layers, name, layer)
    if name in ['world_map', 'max_local', 'graticule_vertices', 'average_location', 'all_average_locations', 'local_frequencies']:
        layer.svg = mapfolder/name/'svg'/f'{name}.%08d.svg'
        layer.png = mapfolder/name/'png'/f'{name}.%08d.png'
        layer.center = map_center
        layer.height = map_height
        layer.width = map_width
    elif name == 'clef':
        # Clef indexing on note name.
        layer.svg = shadowfolder/name/'svg'/f'{name}.%s.svg'
        layer.png = shadowfolder/name/'png'/f'{name}.%s.png'
    elif name in ['chromosome_map', 'variant', 'legend_frequency', 'legend_position', 'caption', 'date', 'worldwide_frequency']:
        # Only use shadows for black lines/text.
        layer.svg = shadowfolder/name/'svg'/f'{name}.%08d.svg'
        layer.png = shadowfolder/name/'png'/f'{name}.%08d.png'
    else:
        layer.svg = images/name/'svg'/f'{name}.%08d.svg'
        layer.png = images/name/'png'/f'{name}.%08d.png'
    # ffmpeg concat files, used so that we only have to generate the frames
    # once and can assemble them in arbitrary order to make the movie.
    layer.concat = movie/order/f'{name}.concat'
    folders.append(layer.svg.parent)
    folders.append(layer.png.parent)
    folders.append(layer.concat.parent)

layers.chromosome_map.sections = [
    {'axis': 'width', 'start': (608, 1280), 'end': (480, 1320)},
    {'axis': 'width', 'start': (480, 1280), 'end': (0, 1440)},
    {'axis': 'height', 'start': (0, 1280), 'end': (160, 160)},
    {'axis': 'width', 'start': (0, 160), 'end': (1440, 0)},
    {'axis': 'height', 'start': (1440, 160), 'end': (1280, 1280)},
    {'axis': 'width', 'start': (1440, 1280), 'end': (960, 1440)},
    {'axis': 'width', 'start': (960, 1280), 'end': (832, 1320)},
]
layers.chromosome_map.radius = 8

layers.max_local.max_radius = 16/1440*height
layers.max_local.stroke_width = 0
layers.max_local.style = 'stroke:none;fill:pink;fill-opacity:1.0;'

layers.graticule_vertices.max_radius = 1/1440*height
layers.graticule_vertices.stroke_width = 0
layers.graticule_vertices.style = 'stroke:none;fill:pink;fill-opacity:1.0;'
layers.graticule_vertices.spacing = 10

layers.average_location.max_radius = 12/1440*height
layers.average_location.stroke_width = 0
layers.average_location.style = 'stroke:none;fill:blue;fill-opacity:1.0;'

layers.local_frequencies.max_radius = 16/1440*height
# We need stroke width separated out from the style for calculations.
layers.local_frequencies.stroke_width = 4
#layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'
#layers.local_frequencies.style = 'stroke:orange;stroke-opacity:1.0;fill:orange;fill-opacity:0.7;'
layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.7;'
#layers.local_frequencies.color = '#ff0000ff'

layers.worldwide_frequency.center = (int(220/1440*width), int(220/1440*height))
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
layers.clef.center = (2264/1440*width, 296/1440*height)
layers.clef.width = 280/1440*height
layers.clef.height = 280/1440*height

layers.variant.center = (2100/1440*width, 1132/1440*height)
layers.variant.font_size = int(height*36/1440)
layers.variant.height = layers.variant.font_size * 4
layers.variant.width = layers.variant.font_size * 24
layers.variant.style = 'font-family:sans-serif;'

layers.legend_frequency.center = (600/1440*width, 296/1440*height)
layers.legend_frequency.font_size = int(height*36/1440)
layers.legend_frequency.frequencies = [1.0, 0.5, 0.25, 0.125, 0.0625]
layers.legend_frequency.height = layers.legend_frequency.font_size * (len(layers.legend_frequency.frequencies) + 3)
layers.legend_frequency.width = layers.legend_frequency.font_size * 24
layers.legend_frequency.style = 'font-family:sans-serif;'

layers.legend_position.center = (585/1440*width, 1132/1440*height)
layers.legend_position.font_size = int(height*36/1440)
layers.legend_position.height = layers.legend_position.font_size * 4
layers.legend_position.width = layers.legend_position.font_size * 24
layers.legend_position.style = 'font-family:sans-serif;'

layers.caption.center = (int(0.5*width), int(1240/1440*height))
layers.caption.font_size = int(height*72/1440)
layers.caption.height = layers.caption.font_size * 2
layers.caption.style = 'font-family:sans-serif;'
layers.caption.captions = code/'captions.srt'

layers.date.center = (int(0.5*width), int(1380/1440*height))
layers.date.font_size = int(height*54/1440)
layers.date.height = layers.date.font_size * 3
layers.date.style = 'font-family:sans-serif;'
layers.date.multiplier = 10000

movie_limit = 0 # Limit the number of frames created.  0 = no limit.
movie_time = 0 # Select a specific time.  0 = all times.

audio_midi = audio/f'{order}_{movie_time}_{movie_limit}.midi'
audio_wav = audio/f'{order}_{movie_time}_{movie_limit}.wav'
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

movie_mp4 = movie/f'{map_image}_{map_projection}_{map_rotation[0]}_{map_rotation[1]}_{order}_{"shadows" if shadows else "noshadows"}_{movie_time}_{movie_limit}.mp4'


