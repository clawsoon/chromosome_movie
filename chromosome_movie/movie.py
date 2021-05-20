#!/usr/bin/env python3

import sys
import subprocess

import sqlite3

from . import chromosome_map, chromosome_position, world_map, locations, worldwide_frequency, clef, text, audio

class Movie():

    def __init__(self, cfg):
        self.cfg = cfg

        self.classes = {
            'chromosome_map': chromosome_map.ChromosomeMap,
            'chromosome_position': chromosome_position.ChromosomePosition,
            'world_map': world_map.WorldMap,
            'max_local': locations.MaxLocal,
            'average_location': locations.AverageLocation,
            'local_frequencies': locations.LocalFrequencies,
            'worldwide_frequency': worldwide_frequency.WorldwideFrequency,
            'clef': clef.Clef,
            'date': text.Date,
            'caption': text.Caption,
        }

        self.layers = {}
        for name in self.cfg.movie_layers:
            self.layers[name] = getattr(self.cfg.layers, name)
            self.layers[name].obj = self.classes[name](self.cfg)

    def write_concat(self):
        database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        database.row_factory = sqlite3.Row
        cursor = database.cursor()
        # Breathing calmly because we are not, in fact, opening ourselves
        # to SQL injection attacks by failing to properly parameterize
        # our query.  But don't let me see you doing this again!
        select = f'SELECT * FROM variant'
        if self.cfg.movie_time:
            select += f' WHERE time={self.cfg.movie_time}'
        select += f' ORDER BY {self.cfg.order}'
        if self.cfg.movie_limit:
            select += f' LIMIT {self.cfg.movie_limit}'
        cursor.execute(select)
        timestep = 1 / self.cfg.video_framerate
        for layer in self.layers.values():
            layer.concat_file = open(layer.concat, 'w')
        for frame, variant in enumerate(cursor):
            if frame % 1000 == 0:
                sys.stderr.write(f'Concatting... {frame}\n')
                sys.stderr.flush()
            for name in self.cfg.movie_layers:
                layer = self.layers[name]
                png = layer.obj.png_path(variant, frame).replace('\\', '/')
                # Apparently the "duration" field is buggy if you try to
                # use it fancy.
                #
                # It is certainly dumb to write a 10MB file to record that
                # a single world map will be used for the whole movie.
                layer.concat_file.write(f"file '{png}'\n")
                layer.concat_file.write(f"duration {timestep}\n")
        for layer in self.layers.values():
            layer.concat_file.close()
        cursor.close()
        database.close()


    def write_mp4(self):

        timidity_command = [
            self.cfg.timidity,
            str(self.cfg.audio_midi),
            '-s', str(self.cfg.audio_samplerate),
            #'-OwS', # WAV, stereo
            '-Or1slS', # 16-bit signed linear PCM stereo
            '-o', '-', # Pipe to stdout.
        ]

        ffmpeg_command = [
            self.cfg.ffmpeg,
            '-y',
            '-threads', '0',

            '-f', 'lavfi',
            '-r', str(self.cfg.video_framerate),
            #'-i', f'color=white:{self.cfg.width}x{self.cfg.height}:d=3,format=rgb24',
            '-i', f'color=c=white:s={self.cfg.width}x{self.cfg.height}:r={self.cfg.video_framerate}:d=1',
        ]

        previous = 0
        current = 0
        overlays = []

        for num, name in enumerate(self.cfg.movie_layers):
            layer = self.layers[name]
            ffmpeg_command.extend([
                '-f', 'concat',
                #'-safe', '0',
                '-r', str(self.cfg.video_framerate),
                '-i', str(layer.concat),
            ])
            #if num == 0:
            #    continue
            #current = num
            current = num + 1
            if hasattr(layer, 'center'):
                if hasattr(layer, 'width'):
                    left = layer.center[0] - layer.width / 2
                else:
                    left = layer.center[0] - self.cfg.width / 2
                if hasattr(layer, 'height'):
                    top = layer.center[1] - layer.height / 2
                else:
                    top = layer.center[1] - self.cfg.height / 2
            else:
                left = 0
                top = 0
            overlay = f'[{previous}][{current}]overlay=x={left}:y={top}[out{current}]'
            overlays.append(overlay)
            previous = f'out{current}'

        if self.cfg.audio_pipe:
            ffmpeg_command.extend([
                '-f', 's16le', # PCM signed 16-bit little-endian
                '-ar', str(self.cfg.audio_samplerate),
                '-ac', '2', # Stereo
                '-i', '-', # Pull audio from stdin.
            ])
        else:
            ffmpeg_command.extend([
                '-i', str(self.cfg.audio_wav),
            ])
        #ffmpeg_command.extend([
        #    '-vsync', '0',
        #])

        ffmpeg_command.extend([
            '-filter_complex', ';'.join(overlays),
            '-map', f'[out{current}]',
            '-map', f'{current + 1}:a',
            #'-shortest',
            #'-async', '0',
            #'-vsync', '0',
        ])

        #if self.cfg.movie_limit:
        #    ffmpeg_command.extend([
        #        '-vframes', f'{self.cfg.movie_limit}'
        #    ])

        ffmpeg_command.extend([
            '-c:a', 'aac',
            '-c:v', 'libx264',
            '-r', str(self.cfg.video_framerate),
            '-movflags', '+faststart',
            str(self.cfg.movie_mp4)
        ])

        print('"' + '" "'.join(timidity_command) + '"')
        print('"' + '" "'.join(ffmpeg_command) + '"')
        if self.cfg.audio_pipe:
            timidity = subprocess.Popen(timidity_command, stdout=subprocess.PIPE)
            ffmpeg = subprocess.Popen(ffmpeg_command, stdin=timidity.stdout)
            ffmpeg.wait()
        else:
            subprocess.call(ffmpeg_command)

'''
def create_ffmpeg_concat(limit=None, folder=None):
    database = sqlite3.connect(config.database_readonly_uri, uri=True)
    database.row_factory = sqlite3.Row
    cursor = database.cursor()

    query = 'SELECT id FROM variant ORDER BY %s' % config.order_column
    if limit:
        # Should this be a parameter instead of a string substitution?
        # Probably.
        query += ' LIMIT %s' % limit
    cursor.execute(query)

    ffmpeg_overlay_concat = config.ffmpeg_overlay_concat
    ffmpeg_chromosome_map_concat = config.ffmpeg_chromosome_map_concat
    if folder:
        ffmpeg_overlay_concat = os.path.join(folder, ffmpeg_overlay_concat)
        ffmpeg_chromosome_map_concat = os.path.join(folder, ffmpeg_chromosome_map_concat)


    with open(ffmpeg_overlay_concat, 'w') as overlay_concat, open(ffmpeg_chromosome_map_concat, 'w') as chromosome_map_concat:
        for row in cursor:

            path = config.overlay_png % row['id']
            text = "file '%s'\n" % path.replace('\\', '/')
            overlay_concat.write(text)

            path = config.chromosome_map_png % row['id']
            text = "file '%s'\n" % path.replace('\\', '/')
            chromosome_map_concat.write(text)


def run_ffmpeg(limit=None, folder=None):

    map_top = config.world_map_center[1] - config.world_map_height / 2

    movie_path = config.final_movie
    if folder:
        movie_path = os.path.join(folder, movie_path)

    temp = 'curved-radius8-stroke3-dropshadow-stripped'

    # FIXME: We are getting DTS/PTS errors from ffmpeg with this.
    command = [
        config.ffmpeg,
        '-y',
        '-threads', '0',

        '-f', 'lavfi',
        '-i', f'color=white:{config.width}x{config.height}:d=3,format=rgb24',

        #'-f', 'concat',
        #'-r', str(config.video_framerate),
        #'-i', config.ffmpeg_chromosome_map_concat,
        '-loop', '1',
        '-f', 'image2',
        '-r', str(config.video_framerate),
        #'-i', os.path.join(config.images, 'gilbert_frame.png'),
        '-i', os.path.join(config.images, f'{temp}.png'),

        '-loop', '1',
        '-f', 'image2',
        '-r', str(config.video_framerate),
        '-i', config.world_map,

        #'-f', 'concat',
        #'-r', str(config.video_framerate),
        #'-i', config.ffmpeg_overlay_concat,

        #'-filter_complex', '[0][1]overlay[v0];[v0][2]overlay=main_w/2-overlay_w/2:%s[v1];[v1][3]overlay=shortest=1[out]' % map_top,
        '-filter_complex', '[0][1]overlay[v0];[v0][2]overlay=x=main_w/2-overlay_w/2:y=%s[out]' % map_top,
        '-map', '[out]',
    ]

    if limit:
        command.extend(['-vframes', f'{limit}'])

    command.extend([
        '-c:v', 'libx264',
        '-r', str(config.video_framerate),
        '-movflags', '+faststart',
        #movie_path,
        os.path.join('minus_150', 'movie', f'{temp}.mp4')
    ])

    print('"' + '" "'.join(command) + '"')
    subprocess.call(command)


def main():
    create_ffmpeg_concat()
    run_ffmpeg()
'''
