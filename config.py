#!/usr/bin/env python3

import pathlib
import shutil


chromosome = '22'

# Path to source treeseq file.
#treeseq = 'sgdp_chr22.trees'
treeseq = 'hgdp_1kg_sgdp_high_cov_ancients_chr22.dated.trees'

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
#order = 'two_world_jaccard20_30w_30s_169w_65n_max120'


# Video parameters.
width = 2560
height = 1440
resolution = (width, height)
# 8 fps gives a Youtube viewer a range of 2fps to 16fps, which seems to be
# a reasonable range for this particular movie.
video_framerate = 8
#video_framerate = 2
audio_samplerate = 48000

def w(value):
    'Scale 2560-based x values to whatever the actual width is.'
    return value * width / 2560

def h(value):
    'Scale 1440-based y values to whatever the actual height is.'
    return value * height / 1440

# Required executables.
#ffmpeg = '/usr/bin/ffmpeg'
ffmpeg = shutil.which('ffmpeg') or r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
#ffmpeg = r'C:\Program Files\ffmpeg\bin\ffmpeg.exe'
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

# Adds some shadows to text and lines to make lines a little cleaner when
# movies are resized to arbitrary sizes by the viewer, or when high-resolution
# movies are viewed on low-resolution screens.  It's a hack, but it seems to
# kinda work.
shadows = True

#map_image = 'blue_marble'
#map_projection = 'natural_earth_2'
#map_rotation = (-150, 0)  # I like either -11 or -150.
#map_format = 'png'
#map_center = (w(1280), h(720-36))
#map_width = w(2048)
#map_height = h(1024)
#map_scale = 1

map_image = 'visionscarto_lightblue'
#map_image = 'visionscarto_graticules'
map_projection = 'bertin'
map_rotation = (-16.5, -42)
map_format = 'svg'
map_center = (w(1280), h(720-36))
map_height = h(1024)
# These are the specific visionscarto dimensions - 700x475.
map_scale = map_height/475
map_width = map_scale*700


# Map images have to be manually created for now.
# I've been using G.Projector and GIMP.
default_world_map = code/'maps'/f'{map_image}_{map_projection}_{map_rotation[0]}_{map_rotation[1]}.{map_format}'

layer_names = [
    'world_map',
    'chromosome_map',
    'chromosome_position',
    'worldwide_frequency',
    'clef',
    #'note',
    'max_local',
    'graticule_vertices',
    'traces',
    'average_location',
    'all_average_locations',
    'local_frequencies',
    'legend_frequency',
    'legend_position',
    'variant',
    'caption',
    'citation',
    'date',
    'background',
    'foreground',
]

background_layers = [
    # For Natural Earth 2 PNG we put world map here to avoid large file sizes.
    #'world_map',
    #'graticule_vertices',
    'chromosome_map',
    #'max_local',
    #'clef',
    'legend_frequency',
    'legend_position',
]

foreground_layers = [
    # For Bertin SVG we put world map here to get cleaner traces overlays.
    'world_map',
    #'graticule_vertices',
    'chromosome_position',
    #'note',
    'clef',
    'traces',
    'average_location',
    'local_frequencies',
    'variant',
    #'caption',
    #'citation',
    'date',
]

movie_layers = [
    #'world_map',
    #'chromosome_map',
    #'chromosome_position',
    #'clef',
    #'note',
    #'traces',
    #'average_location',
    #'local_frequencies',
    #'legend_frequency',
    #'legend_position',
    #'variant',
    #'caption',
    #'date',
    'background',
    'foreground',
]


map_layers = set([
    'average_location',
    'local_frequencies',
    'world_map',
    'max_local',
    'graticule_vertices',
    'all_average_locations',
    'background',
    'traces',
    'background',
    'foreground',
])
shadow_layers = set([
    'note',
    'variant',
    'caption',
    'citation',
    'date',
    'worldwide_frequency',
    'chromosome_map',
    'legend_frequency',
    'legend_position',
    'clef',
    'background',
    'foreground',
])
order_layers = set([
    'count',
    'traces',
    'background',
    'foreground',
])

class Stub():
    pass

layers = Stub()

mapfolder = f'{map_projection}_{map_rotation[0]}_{map_rotation[1]}'
shadowfolder = ('shadows' if shadows else 'noshadows')
orderfolder = order

for name in layer_names:
    layer = Stub()
    setattr(layers, name, layer)

    basefolder = images
    if name in map_layers:
        basefolder /= mapfolder
        if name not in ['foreground', 'background']:
            layer.center = map_center
            layer.height = map_height
            layer.width = map_width
    if name in shadow_layers:
        basefolder /= shadowfolder
    if name in order_layers:
        basefolder /= orderfolder

    if name in background_layers or name in ['background', 'world_map']:
        frame_suffix = ''
    #elif name == 'note':
    elif name == 'clef':
        frame_suffix = '.%s'
    else:
        frame_suffix = '.%08d'

    layer.svg = basefolder/name/'svg'/f'{name}{frame_suffix}.svg'
    layer.png = basefolder/name/'png'/f'{name}{frame_suffix}.png'
    layer.concat = movie/order/f'{name}.concat'

    folders.append(layer.svg.parent)
    folders.append(layer.png.parent)
    folders.append(layer.concat.parent)

## This is getting messy.  Clean up once final decisions are made.
#shadowfolder = images/('shadows' if shadows else 'noshadows')
#shadoworderfolder = images/('shadows' if shadows else 'noshadows')/order
#mapfolder = images/f'{map_projection}_{map_rotation[0]}_{map_rotation[1]}'
#maporderfolder = images/f'{map_projection}_{map_rotation[0]}_{map_rotation[1]}'/order
#finalfolder = images/f'{map_projection}_{map_rotation[0]}_{map_rotation[1]}'/('shadows' if shadows else 'noshadows')/order
#
#layers = Stub()
#for name in layer_names:
#    layer = Stub()
#    setattr(layers, name, layer)
#    if name in ['average_location', 'local_frequencies']:
#        layer.svg = images/mapfolder/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/mapfolder/name/'png'/f'{name}.%08d.png'
#        layer.center = map_center
#        layer.height = map_height
#        layer.width = map_width
#    elif name in ['world_map', 'max_local', 'graticule_vertices', 'all_average_locations', 'background']:
#        layer.svg = images/mapfolder/name/'svg'/f'{name}.svg'
#        layer.png = images/mapfolder/name/'png'/f'{name}.png'
#        layer.center = map_center
#        layer.height = map_height
#        layer.width = map_width
#    elif name in ['note']:
#        # Clef indexing on note name.
#        layer.svg = images/shadowfolder/name/'svg'/f'{name}.%s.svg'
#        layer.png = images/shadowfolder/name/'png'/f'{name}.%s.png'
#    elif name in ['variant', 'caption', 'date', 'worldwide_frequency']:
#        # Only use shadows for black lines/text.
#        layer.svg = images/shadowfolder/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/shadowfolder/name/'png'/f'{name}.%08d.png'
#    elif name in ['chromosome_map', 'legend_frequency', 'legend_position', 'clef']:
#        # Only use shadows for black lines/text.
#        layer.svg = images/shadowfolder/name/'svg'/f'{name}.svg'
#        layer.png = images/shadowfolder/name/'png'/f'{name}.png'
#    elif name in ['traces']:
#        layer.svg = images/mapfolder/orderfolder/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/mapfolder/orderfolder/name/'png'/f'{name}.%08d.png'
#        layer.center = map_center
#        layer.height = map_height
#        layer.width = map_width
#    elif name in ['final']:
#        layer.svg = images/mapfolder/orderfolder/shadowfolder/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/mapfolder/orderfolder/shadowfolder/name/'png'/f'{name}.%08d.png'
#    elif name in ['count']:
#        layer.svg = images/shadowfolder/orderfolder/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/shadowfolder/orderfolder/name/'png'/f'{name}.%08d.png'
#    else:
#        layer.svg = images/name/'svg'/f'{name}.%08d.svg'
#        layer.png = images/name/'png'/f'{name}.%08d.png'
#    # ffmpeg concat files, used so that we only have to generate the frames
#    # once and can assemble them in arbitrary order to make the movie.
#    layer.concat = movie/order/f'{name}.concat'
#    folders.append(layer.svg.parent)
#    folders.append(layer.png.parent)
#    folders.append(layer.concat.parent)

font_large = h(72)
font_medium = h(54)
font_small = h(54)
font_tiny = h(30)

layers.world_map.scale = map_scale

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

layers.max_local.max_radius = h(16)
layers.max_local.stroke_width = 0
layers.max_local.style = 'stroke:none;fill:pink;fill-opacity:1.0;'

layers.graticule_vertices.max_radius = 1
layers.graticule_vertices.stroke_width = 0
layers.graticule_vertices.style = 'stroke:none;fill:pink;fill-opacity:1.0;'
layers.graticule_vertices.spacing = 10 # degrees

layers.average_location.max_radius = h(12)
layers.average_location.stroke_width = 0
layers.average_location.style = 'stroke:none;fill:blue;fill-opacity:1.0;'

layers.local_frequencies.max_radius = h(16)
# We need stroke width separated out from the style for calculations.
layers.local_frequencies.stroke_width = 4
#layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'
#layers.local_frequencies.style = 'stroke:orange;stroke-opacity:1.0;fill:orange;fill-opacity:0.7;'
layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.5;'
#layers.local_frequencies.color = '#ff0000ff'

layers.traces.style = 'stroke:orange;stroke-width:5;stroke-linecap:round;fill:none;'
# How long to keep a trace around before removing it.
layers.traces.deque_length = 480
layers.traces.prefer_pacific = False

layers.worldwide_frequency.center = (w(220), h(220))
layers.worldwide_frequency.max_radius = h(100)
# We need stroke width separated out from the style for calculations.
layers.worldwide_frequency.stroke_width = 4
layers.worldwide_frequency.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'
layers.worldwide_frequency.backing_style = 'stroke:none;fill:grey;fill-opacity:0.4;'
layers.worldwide_frequency.font_size = font_medium
layers.worldwide_frequency.text_style = 'font-family:sans-serif;'

# We're measuring clef from top left instead of centre.
# Maybe it would be easier for ffmpeg setup to use centre for all layers?
# In which case change this position to a center measurement.
layers.clef.center = (w(2204), h(346))
#layers.clef.scale = h(280/18000)
layers.clef.width = h(360)
layers.clef.height = h(360)

layers.variant.center = (w(1980), h(1132))
layers.variant.font_size = font_small
layers.variant.width = font_small * 24
layers.variant.height = font_small * 4
layers.variant.style = 'font-family:sans-serif;'

layers.legend_frequency.center = (w(820), h(336))
layers.legend_frequency.font_size = font_small
layers.legend_frequency.frequencies = [1.0, 0.5, 0.25, 0.125, 0.0625, .01]
layers.legend_frequency.width = font_small * 24
layers.legend_frequency.height = font_small * (len(layers.legend_frequency.frequencies) + 3)
layers.legend_frequency.style = 'font-family:sans-serif;'

layers.legend_position.center = (w(800), h(1132))
layers.legend_position.font_size = font_small
layers.legend_position.width = font_small * 24
layers.legend_position.height = font_small * 4
layers.legend_position.style = 'font-family:sans-serif;'

layers.caption.center = (w(1280), h(1240))
layers.caption.font_size = font_large
layers.caption.width = width
layers.caption.height = font_large * 2
layers.caption.style = 'font-family:sans-serif;'
layers.caption.srt = code/'captions.srt'
layers.caption.typing = None

layers.citation.center = (w(1880), h(960))
layers.citation.font_size = font_tiny
layers.citation.width = w(960)
layers.citation.height = h(216)
layers.citation.style = 'font-family:sans-serif;'
layers.citation.srt = code/'citations.srt'
layers.citation.typing = None

layers.date.center = (w(1280), h(1380))
layers.date.font_size = font_medium
layers.date.width = width
layers.date.height = font_medium * 3
layers.date.style = 'font-family:sans-serif;'
layers.date.multiplier = 1

#movie_time = 0 # Select a specific time.  0 = all times.
#movie_limit = 120 # Limit the number of frames created.  0 = no limit.

#movie_times = ((551, 480), (550, 480), (549, 480), (300, 480), (100, 480), (50, 480), (40, 480), (30, 480), (20, 480), (10, 480), (3, 480), (1, 480))
#movie_time_name = '-'.join(f'{time}_{limit}' for time, limit in movie_times)
#movie_laps = [(time, 1) for time in range(551, 1, -13)]
#movie_laps.append((1, 4))
#movie_time_name = 'lapsAAB'

movie_times = {
    'name': 'scatter01',
    'type': 'time_limit',
    'time_limits': [
        (80_000, 960),
        (60_000, 960),
        (40_000, 960),
        (20_000, 960),
        (10_000, 960),
        (8_000, 960),
        (6_000, 960),
        (4_000, 960),
        (2_000, 960),
        (1_000, 960),
        (800, 960),
        (600, 960),
        (400, 960),
        (200, 960),
        (100, 960),
        (80, 960),
        (60, 960),
        (40, 960),
        (20, 960),
        (10, 960),
        (8, 960),
        (6, 960),
        (4, 960),
        (2, 960),
        (1, 960),
    ],
}

#movie_times = {
#    'name': 'full',
#    'type': None,
#}

#audio_midi = audio/f'{order}_{movie_time}_{movie_limit}.midi'
#audio_wav = audio/f'{order}_{movie_time}_{movie_limit}.wav'
audio_midi = audio/f'{order}_{movie_times["name"]}.midi'
audio_wav = audio/f'{order}_{movie_times["name"]}.wav'
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

#movie_mp4 = movie/f'{map_image}_{map_projection}_{map_rotation[0]}_{map_rotation[1]}_{order}_{"shadows" if shadows else "noshadows"}_{movie_time}_{movie_limit}.mp4'
movie_mp4 = movie/f'{map_image}_{map_projection}_{map_rotation[0]}_{map_rotation[1]}_{order}_{"shadows" if shadows else "noshadows"}_{movie_times["name"]}.mp4'


