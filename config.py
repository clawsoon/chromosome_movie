#!/usr/bin/env python3

import pathlib
import shutil


chromosome = '22'

# Path to source treeseq file.
#treeseq = 'sgdp_chr22.trees'
treeseq = 'hgdp_tgp_sgdp_chr22_q.dated.trees'
#treeseq = 'hgdp_1kg_sgdp_high_cov_ancients_chr22.dated.trees'

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
weighted_average_locations = False

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
    'populations',
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
    #'legend_frequency',
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
    'populations',
    'caption',
    'citation',
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
    'populations',
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
font_tiny = h(32)
font_tinier = h(24)
font_miniscule = h(16)

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
layers.local_frequencies.fixed_radius = True
# We need stroke width separated out from the style for calculations.
layers.local_frequencies.stroke_width = 4
#layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.6;'
#layers.local_frequencies.style = 'stroke:orange;stroke-opacity:1.0;fill:orange;fill-opacity:0.7;'
layers.local_frequencies.style = 'stroke:red;stroke-opacity:1.0;fill:red;fill-opacity:0.5;'
#layers.local_frequencies.color = '#ff0000ff'

layers.traces.style = 'stroke:orange;stroke-width:5;stroke-linecap:round;fill:none;'
# How long to keep a trace around before removing it.
layers.traces.deque_length = 480
layers.traces.start_time = 3
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
layers.clef.center = (w(2204), h(624))
#layers.clef.scale = h(280/18000)
layers.clef.width = h(360)
layers.clef.height = h(360)

layers.variant.center = (w(1980), h(932))
layers.variant.font_size = font_small
layers.variant.width = font_small * 24
layers.variant.height = font_small * 4
layers.variant.style = 'font-family:sans-serif;'

# Do we need width and height here?  Hopefully not?
layers.populations.font_size = font_miniscule
layers.populations.style = 'font-family:Raleway;font-weight:800;'
layers.populations.line_spacing = 1.25
layers.populations.source = {
    'SGDP': {
        'title': 'Simons Genome Diversity Project',
        'top': h(196),
        'left': w(180),
        'column': {
            0: w(0),
            1: w(125),
            2: w(275),
            3: w(405),
        },
    },
    'HGDP': {
        'title': 'Human Genome Diversity Project',
        'top': h(1008),
        'left': w(180),
        'column': {
            0: w(0),
            1: w(160),
            2: w(260),
            3: w(380),
            4: w(530),
        },
    },
    '1KG': {
        'title': '1000 Genomes Project',
        'top': h(1048),
        'left': w(1860),
        'column': {
            0: w(0),
            1: w(180),
            2: w(340),
        },
    },
}
# I'm sure there's a less manual way to do this, but in the interest of
# getting it done...
# Ideally with an automatic method we wouldn't want to be tied to population
# IDs, which can change between treesequence DBs.  Source and name should,
# in theory, be more reliable.
layers.populations.position = {
    ('SGDP', 'Abkhasian'): (0, 0, 'Abkhasian'),
    ('SGDP', 'Adygei'): (0, 1, 'Adygei'),
    ('SGDP', 'Albanian'): (0, 2, 'Albanian'),
    ('SGDP', 'Aleut'): (0, 3, 'Aleut'),
    ('SGDP', 'Altaian'): (0, 4, 'Altaian'),
    ('SGDP', 'Ami'): (0, 5, 'Ami'),
    ('SGDP', 'Armenian'): (0, 6, 'Armenian'),
    ('SGDP', 'Atayal'): (0, 7, 'Atayal'),
    ('SGDP', 'Australian'): (0, 8, 'Australian'),
    ('SGDP', 'Balochi'): (0, 9, 'Balochi'),
    ('SGDP', 'BantuHerero'): (0, 10, 'Bantu Herero'),
    ('SGDP', 'BantuKenya'): (0, 11, 'Bantu Kenya'),
    ('SGDP', 'BantuTswana'): (0, 12, 'Bantu Tswana'),
    ('SGDP', 'Basque'): (0, 13, 'Basque'),
    ('SGDP', 'BedouinB'): (0, 14, 'Bedouin'),
    ('SGDP', 'Bengali'): (0, 15, 'Bengali'),
    ('SGDP', 'Bergamo'): (0, 16, 'Bergamo'),
    ('SGDP', 'Biaka'): (0, 17, 'Biaka'),
    ('SGDP', 'Bougainville'): (0, 18, 'Bougainville'),
    ('SGDP', 'Brahmin'): (0, 19, 'Brahmin'),
    ('SGDP', 'Brahui'): (0, 20, 'Brahui'),
    ('SGDP', 'Bulgarian'): (0, 21, 'Bulgarian'),
    ('SGDP', 'Burmese'): (0, 22, 'Burmese'),
    ('SGDP', 'Burusho'): (0, 23, 'Burusho'),
    ('SGDP', 'Cambodian'): (0, 24, 'Cambodian'),
    ('SGDP', 'Chane'): (0, 25, 'Chane'),
    ('SGDP', 'Chechen'): (0, 26, 'Chechen'),
    ('SGDP', 'Chukchi'): (0, 27, 'Chukchi'),
    ('SGDP', 'Crete'): (0, 28, 'Crete'),
    ('SGDP', 'Czech'): (0, 29, 'Czech'),
    ('SGDP', 'Dai'): (0, 30, 'Dai'),
    ('SGDP', 'Daur'): (0, 31, 'Daur'),
    ('SGDP', 'Dinka'): (0, 32, 'Dinka'),
    ('SGDP', 'Druze'): (0, 33, 'Druze'),
    ('SGDP', 'Dusun'): (0, 34, 'Dusun'),
    ('SGDP', 'English'): (0, 35, 'English'),
    ('SGDP', 'Esan'): (0, 36, 'Esan'),
    ('SGDP', 'Eskimo_Chaplin'): (1, 0, 'Eskimo Chaplin'),
    ('SGDP', 'Eskimo_Naukan'): (1, 1, 'Eskimo Naukan'),
    ('SGDP', 'Eskimo_Sireniki'): (1, 2, 'Eskimo Sireniki'),
    ('SGDP', 'Estonian'): (1, 3, 'Estonian'),
    ('SGDP', 'Even'): (1, 4, 'Even'),
    ('SGDP', 'Finnish'): (1, 5, 'Finnish'),
    ('SGDP', 'French'): (1, 6, 'French'),
    ('SGDP', 'Gambian'): (1, 7, 'Gambian'),
    ('SGDP', 'Georgian'): (1, 8, 'Georgian'),
    ('SGDP', 'Greek'): (1, 9, 'Greek'),
    ('SGDP', 'Han'): (1, 10, 'Han'),
    ('SGDP', 'Hawaiian'): (1, 11, 'Hawaiian'),
    ('SGDP', 'Hazara'): (1, 12, 'Hazara'),
    ('SGDP', 'Hezhen'): (1, 13, 'Hezhen'),
    ('SGDP', 'Hungarian'): (1, 14, 'Hungarian'),
    ('SGDP', 'Icelandic'): (1, 15, 'Icelandic'),
    ('SGDP', 'Igorot'): (1, 16, 'Igorot'),
    ('SGDP', 'Iranian'): (1, 17, 'Iranian'),
    ('SGDP', 'Iraqi_Jew'): (1, 18, 'Iraqi Jew'),
    ('SGDP', 'Irula'): (1, 19, 'Irula'),
    ('SGDP', 'Itelman'): (1, 20, 'Itelman'),
    ('SGDP', 'Japanese'): (1, 21, 'Japanese'),
    ('SGDP', 'Jordanian'): (1, 22, 'Jordanian'),
    ('SGDP', 'Ju_hoan_North'): (1, 23, 'Ju hoan North'),
    ('SGDP', 'Kalash'): (1, 24, 'Kalash'),
    ('SGDP', 'Kapu'): (1, 25, 'Kapu'),
    ('SGDP', 'Karitiana'): (1, 26, 'Karitiana'),
    ('SGDP', 'Khomani_San'): (1, 27, 'Khomani San'),
    ('SGDP', 'Khonda_Dora'): (1, 28, 'Khonda Dora'),
    ('SGDP', 'Kinh'): (1, 29, 'Kinh'),
    ('SGDP', 'Korean'): (1, 30, 'Korean'),
    ('SGDP', 'Kusunda'): (1, 31, 'Kusunda'),
    ('SGDP', 'Kyrgyz'): (1, 32, 'Kyrgyz'),
    ('SGDP', 'Lahu'): (1, 33, 'Lahu'),
    ('SGDP', 'Lezgin'): (1, 34, 'Lezgin'),
    ('SGDP', 'Luhya'): (1, 35, 'Luhya'),
    ('SGDP', 'Luo'): (1, 36, 'Luo'),
    ('SGDP', 'Madiga'): (2, 0, 'Madiga'),
    ('SGDP', 'Makrani'): (2, 1, 'Makrani'),
    ('SGDP', 'Mala'): (2, 2, 'Mala'),
    ('SGDP', 'Mandenka'): (2, 3, 'Mandenka'),
    ('SGDP', 'Mansi'): (2, 4, 'Mansi'),
    ('SGDP', 'Maori'): (2, 5, 'Maori'),
    ('SGDP', 'Masai'): (2, 6, 'Masai'),
    ('SGDP', 'Mayan'): (2, 7, 'Mayan'),
    ('SGDP', 'Mbuti'): (2, 8, 'Mbuti'),
    ('SGDP', 'Mende'): (2, 9, 'Mende'),
    ('SGDP', 'Miao'): (2, 10, 'Miao'),
    ('SGDP', 'Mixe'): (2, 11, 'Mixe'),
    ('SGDP', 'Mixtec'): (2, 12, 'Mixtec'),
    ('SGDP', 'Mongola'): (2, 13, 'Mongola'),
    ('SGDP', 'Mozabite'): (2, 14, 'Mozabite'),
    ('SGDP', 'Naxi'): (2, 15, 'Naxi'),
    ('SGDP', 'North_Ossetian'): (2, 16, 'North Ossetian'),
    ('SGDP', 'Norwegian'): (2, 17, 'Norwegian'),
    ('SGDP', 'Orcadian'): (2, 18, 'Orcadian'),
    ('SGDP', 'Oroqen'): (2, 19, 'Oroqen'),
    ('SGDP', 'Palestinian'): (2, 20, 'Palestinian'),
    ('SGDP', 'Papuan'): (2, 21, 'Papuan'),
    ('SGDP', 'Pathan'): (2, 22, 'Pathan'),
    ('SGDP', 'Piapoco'): (2, 23, 'Piapoco'),
    ('SGDP', 'Pima'): (2, 24, 'Pima'),
    ('SGDP', 'Polish'): (2, 25, 'Polish'),
    ('SGDP', 'Punjabi'): (2, 26, 'Punjabi'),
    ('SGDP', 'Quechua'): (2, 27, 'Quechua'),
    ('SGDP', 'Relli'): (2, 28, 'Relli'),
    ('SGDP', 'Russian'): (2, 29, 'Russian'),
    ('SGDP', 'Saami'): (2, 30, 'Saami'),
    ('SGDP', 'Saharawi'): (2, 31, 'Saharawi'),
    ('SGDP', 'Samaritan'): (2, 32, 'Samaritan'),
    ('SGDP', 'Sardinian'): (2, 33, 'Sardinian'),
    ('SGDP', 'She'): (2, 34, 'She'),
    ('SGDP', 'Sindhi'): (2, 35, 'Sindhi'),
    ('SGDP', 'Somali'): (2, 36, 'Somali'),
    ('SGDP', 'Spanish'): (3, 0, 'Spanish'),
    ('SGDP', 'Surui'): (3, 1, 'Surui'),
    ('SGDP', 'Tajik'): (3, 2, 'Tajik'),
    ('SGDP', 'Thai'): (3, 3, 'Thai'),
    ('SGDP', 'Tlingit'): (3, 4, 'Tlingit'),
    ('SGDP', 'Tu'): (3, 5, 'Tu'),
    ('SGDP', 'Tubalar'): (3, 6, 'Tubalar'),
    ('SGDP', 'Tujia'): (3, 7, 'Tujia'),
    ('SGDP', 'Turkish'): (3, 8, 'Turkish'),
    ('SGDP', 'Tuscan'): (3, 9, 'Tuscan'),
    ('SGDP', 'Ulchi'): (3, 10, 'Ulchi'),
    ('SGDP', 'Uygur'): (3, 11, 'Uygur'),
    ('SGDP', 'Xibo'): (3, 12, 'Xibo'),
    ('SGDP', 'Yadava'): (3, 13, 'Yadava'),
    ('SGDP', 'Yakut'): (3, 14, 'Yakut'),
    ('SGDP', 'Yemenite_Jew'): (3, 15, 'Yemenite Jew'),
    ('SGDP', 'Yi'): (3, 16, 'Yi'),
    ('SGDP', 'Yoruba'): (3, 17, 'Yoruba'),
    ('SGDP', 'Zapotec'): (3, 18, 'Zapotec'),
    ('HGDP', 'Adygei'): (0, 0, 'Adygei'),
    ('HGDP', 'Balochi'): (0, 1, 'Balochi'),
    ('HGDP', 'BantuKenya'): (0, 2, 'Bantu Kenya'),
    ('HGDP', 'BantuSouthAfrica'): (0, 3, 'Bantu South Africa'),
    ('HGDP', 'Basque'): (0, 4, 'Basque'),
    ('HGDP', 'Bedouin'): (0, 5, 'Bedouin'),
    ('HGDP', 'BergamoItalian'): (0, 6, 'Bergamo Italian'),
    ('HGDP', 'Biaka'): (0, 7, 'Biaka'),
    ('HGDP', 'Bougainville'): (0, 8, 'Bougainville'),
    ('HGDP', 'Brahui'): (0, 9, 'Brahui'),
    ('HGDP', 'Burusho'): (0, 10, 'Burusho'),
    ('HGDP', 'Cambodian'): (1, 0, 'Cambodian'),
    ('HGDP', 'Colombian'): (1, 1, 'Colombian'),
    ('HGDP', 'Dai'): (1, 2, 'Dai'),
    ('HGDP', 'Daur'): (1, 3, 'Daur'),
    ('HGDP', 'Druze'): (1, 4, 'Druze'),
    ('HGDP', 'French'): (1, 5, 'French'),
    ('HGDP', 'Han'): (1, 6, 'Han'),
    ('HGDP', 'Hazara'): (1, 7, 'Hazara'),
    ('HGDP', 'Hezhen'): (1, 8, 'Hezhen'),
    ('HGDP', 'Japanese'): (1, 9, 'Japanese'),
    ('HGDP', 'Kalash'): (1, 10, 'Kalash'),
    ('HGDP', 'Karitiana'): (2, 0, 'Karitiana'),
    ('HGDP', 'Lahu'): (2, 1, 'Lahu'),
    ('HGDP', 'Makrani'): (2, 2, 'Makrani'),
    ('HGDP', 'Mandenka'): (2, 3, 'Mandenka'),
    ('HGDP', 'Maya'): (2, 4, 'Maya'),
    ('HGDP', 'Mbuti'): (2, 5, 'Mbuti'),
    ('HGDP', 'Miao'): (2, 6, 'Miao'),
    ('HGDP', 'Mongolian'): (2, 7, 'Mongolian'),
    ('HGDP', 'Mozabite'): (2, 8, 'Mozabite'),
    ('HGDP', 'Naxi'): (2, 9, 'Naxi'),
    ('HGDP', 'NorthernHan'): (2, 10, 'Northern Han'),
    ('HGDP', 'Orcadian'): (3, 0, 'Orcadian'),
    ('HGDP', 'Oroqen'): (3, 1, 'Oroqen'),
    ('HGDP', 'Palestinian'): (3, 2, 'Palestinian'),
    ('HGDP', 'PapuanHighlands'): (3, 3, 'Papuan Highlands'),
    ('HGDP', 'PapuanSepik'): (3, 4, 'Papuan Sepik'),
    ('HGDP', 'Pathan'): (3, 5, 'Pathan'),
    ('HGDP', 'Pima'): (3, 6, 'Pima'),
    ('HGDP', 'Russian'): (3, 7, 'Russian'),
    ('HGDP', 'San'): (3, 8, 'San'),
    ('HGDP', 'Sardinian'): (3, 9, 'Sardinian'),
    ('HGDP', 'She'): (3, 10, 'She'),
    ('HGDP', 'Sindhi'): (4, 0, 'Sindhi'),
    ('HGDP', 'Surui'): (4, 1, 'Surui'),
    ('HGDP', 'Tu'): (4, 2, 'Tu'),
    ('HGDP', 'Tujia'): (4, 3, 'Tujia'),
    ('HGDP', 'Tuscan'): (4, 4, 'Tuscan'),
    ('HGDP', 'Uygur'): (4, 5, 'Uygur'),
    ('HGDP', 'Xibo'): (4, 6, 'Xibo'),
    ('HGDP', 'Yakut'): (4, 7, 'Yakut'),
    ('HGDP', 'Yi'): (4, 8, 'Yi'),
    ('HGDP', 'Yoruba'): (4, 9, 'Yoruba'),
    ('1KG', 'ASW'): (0, 0, 'African American'),
    ('1KG', 'ACB'): (0, 1, 'African Caribbean'),
    ('1KG', 'BEB'): (0, 2, 'Bengali'),
    ('1KG', 'GBR'): (0, 3, 'British'),
    ('1KG', 'CLM'): (0, 4, 'Colombian'),
    ('1KG', 'CDX'): (0, 5, 'Dai Chinese'),
    ('1KG', 'ESN'): (0, 6, 'Esan'),
    ('1KG', 'FIN'): (0, 7, 'Finnish'),
    ('1KG', 'GWD'): (0, 8, 'Gambian Mandinka'),
    ('1KG', 'GIH'): (1, 0, 'Gujarati'),
    ('1KG', 'CHB'): (1, 1, 'Han Chinese'),
    ('1KG', 'IBS'): (1, 2, 'Iberian'),
    ('1KG', 'JPT'): (1, 3, 'Japanese'),
    ('1KG', 'KHV'): (1, 4, 'Kinh Vietnamese'),
    ('1KG', 'LWK'): (1, 5, 'Luhya'),
    ('1KG', 'MSL'): (1, 6, 'Mende'),
    ('1KG', 'MXL'): (1, 7, 'Mexican Ancestry'),
    ('1KG', 'PEL'): (1, 8, 'Peruvian'),
    ('1KG', 'PUR'): (2, 0, 'Puerto Rican'),
    ('1KG', 'PJL'): (2, 1, 'Punjabi'),
    ('1KG', 'CHS'): (2, 2, 'Southern Han Chinese'),
    ('1KG', 'STU'): (2, 3, 'Tamil'),
    ('1KG', 'ITU'): (2, 4, 'Telugu'),
    ('1KG', 'TSI'): (2, 5, 'Toscani'),
    ('1KG', 'CEU'): (2, 6, 'Utah European'),
    ('1KG', 'YRI'): (2, 7, 'Yoruba'),
}

layers.legend_frequency.center = (w(820), h(336))
layers.legend_frequency.font_size = font_small
layers.legend_frequency.frequencies = [1.0, 0.5, 0.25, 0.125, 0.0625, .01]
layers.legend_frequency.width = font_small * 24
layers.legend_frequency.height = font_small * (len(layers.legend_frequency.frequencies) + 3)
layers.legend_frequency.style = 'font-family:sans-serif;'

layers.legend_position.center = (w(2300), h(300))
layers.legend_position.font_size = font_small
layers.legend_position.width = font_small * 24
layers.legend_position.height = font_small * 4
layers.legend_position.style = 'font-family:sans-serif;'

layers.caption.center = (w(1280), h(1200))
layers.caption.font_size = font_large
layers.caption.width = width
layers.caption.height = font_large * 2
layers.caption.style = 'font-family:sans-serif;'
layers.caption.line_spacing = 1.125
layers.caption.srt = code/'captions.srt'
layers.caption.typing = None

layers.citation.center = (w(1280), h(1200))
layers.citation.font_size = font_tiny
layers.citation.width = width
layers.citation.height = font_tiny * 6
layers.citation.style = 'font-family:sans-serif;'
layers.citation.line_spacing = 1
layers.citation.srt = code/'citations.srt'
layers.citation.typing = None

layers.date.center = (w(1280), h(1374))
layers.date.font_size = font_medium
layers.date.width = width
layers.date.height = font_medium * 3
layers.date.style = 'font-family:sans-serif;'
layers.date.line_spacing = 1
layers.date.multiplier = 25 # 25 years per generation in latest awohns code.

#movie_time = 0 # Select a specific time.  0 = all times.
#movie_limit = 120 # Limit the number of frames created.  0 = no limit.

#movie_times = ((551, 480), (550, 480), (549, 480), (300, 480), (100, 480), (50, 480), (40, 480), (30, 480), (20, 480), (10, 480), (3, 480), (1, 480))
#movie_time_name = '-'.join(f'{time}_{limit}' for time, limit in movie_times)
#movie_laps = [(time, 1) for time in range(551, 1, -13)]
#movie_laps.append((1, 4))
#movie_time_name = 'lapsAAB'

movie_times = {
    'name': 'cite1',
    'type': 'time_limit',
    'time_limits': [
        #(80_240, 480),
        #(80_140, 480),
        #(80_110, 480),
        #(80_080, 480),
        #(60_000, 480),
        #(40_000, 480),
        #(20_000, 480),
        #(10_000, 480),
        #(8_000, 480),
        #(6_000, 480),
        #(4_000, 480),
        #(2_000, 480),
        #(1_000, 480),
        #(800, 480),
        #(600, 480),
        #(400, 480),
        #(200, 480),
        #(100, 480),
        #(80, 480),
        #(60, 480),
        #(40, 480),
        #(20, 480),
        #(10, 480),
        (1, 960),
    ],
}

#movie_times = {
#    # FIXME: Would be nice if this was a list instead of having to
#    # change it manually for each part.
#    #'name': 'part1',
#    #'name': 'part2',
#    #'name': 'part3',
#    #'name': 'part4',
#    'name': 'part5',
#    'type': 'time_range',
#    'time_ranges': [
#        # These are in generations.  Inclusive on smaller number only.
#        #(999_999, 1_970),
#        #(1_970, 720),
#        #(720, 330),
#        #(330, 2),
#        (2, 0),
#    ],
#}

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


