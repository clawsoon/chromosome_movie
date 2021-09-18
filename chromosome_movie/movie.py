#!/usr/bin/env python3

import sys
import subprocess

import sqlite3

from . import chromosome_map, chromosome_position, world_map, locations, worldwide_frequency, clef, text, audio, legend, composite

class Movie():

    def __init__(self, cfg, layer_names=None):
        self.cfg = cfg
        self.layer_names = layer_names or self.cfg.movie_layers

        self.order_key = f'order_{self.cfg.order}'

        self.classes = {
            'chromosome_map': chromosome_map.ChromosomeMap,
            'chromosome_position': chromosome_position.ChromosomePosition,
            'world_map': world_map.WorldMap,
            'max_local': locations.MaxLocal,
            'average_location': locations.AverageLocation,
            'local_frequencies': locations.LocalFrequencies,
            'traces': locations.Traces,
            'worldwide_frequency': worldwide_frequency.WorldwideFrequency,
            'clef': clef.Clef,
            'variant': text.Variant,
            'legend_frequency': legend.Frequency,
            'legend_position': legend.Position,
            'date': text.Date,
            'caption': text.Caption,
            'foreground': composite.Foreground,
            'background': composite.Background,
        }

        self.layers = {}
        for name in self.layer_names:
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
        select += f' ORDER BY {self.order_key}'
        if self.cfg.movie_limit:
            select += f' LIMIT {self.cfg.movie_limit}'
        cursor.execute(select)
        timestep = 1 / self.cfg.video_framerate
        #durations = {}
        for name, layer in self.layers.items():
            layer.concat_file.parent.mkdir(parents=True, exist_ok=True)
            #durations[name] = {'frame': None, 'count': 0}
            layer.concat_file = open(layer.concat, 'w')
        for frame, variant in enumerate(cursor):
            if frame % 1000 == 0:
                sys.stderr.write(f'Concatting... {frame}\n')
                sys.stderr.flush()
            for name in self.layer_names:
                layer = self.layers[name]
                png = layer.obj.png_path(variant, frame).replace('\\', '/')
                ## Unfortunately, the duration field for the concat filter
                ## doesn't pay attention if you specify different
                ## durations for the images in the concat file.
                ## This means we have to dumbly write out 10MB concat files
                ## for all the layers.
                #if durations[name]['frame'] == png:
                #    durations[name]['count'] += 1
                #else:
                #    if frame > 0:
                #        layer.concat_file.write(f"duration {timestep*durations[name]['count']}\n")
                #    layer.concat_file.write(f"file '{png}'\n")
                #    durations[name]['frame'] = png
                #    durations[name]['count'] = 1
                layer.concat_file.write(f"file '{png}'\n")
                layer.concat_file.write(f"duration {timestep}\n")
        for name, layer in self.layers.items():
            #if durations[name]['count']:
            #    layer.concat_file.write(f"duration {timestep*durations[name]['count']}\n")
            layer.concat_file.close()
        cursor.close()
        database.close()


    def write_mp4_old(self):

        self.cfg.movie_mp4.parent.mkdir(parents=True, exist_ok=True)

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

        for num, name in enumerate(self.layer_names):
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
            #'-crf', '0',
            #'-pix_fmt', 'yuv444p',
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

    #####

    def write_mp4(self):

        self.cfg.movie_mp4.parent.mkdir(parents=True, exist_ok=True)

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

        previous = '[0]'
        current = 0
        overlays = []

        for num, name in enumerate(self.layer_names):
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
                    width = layer.width
                else:
                    left = layer.center[0] - self.cfg.width / 2
                    width = self.cfg.width
                if hasattr(layer, 'height'):
                    top = layer.center[1] - layer.height / 2
                    height = layer.height
                else:
                    top = layer.center[1] - self.cfg.height / 2
                    height = self.cfg.height
            else:
                left = 0
                top = 0

            if hasattr(layer, 'color'):
                over = f'[bnd{current}]'
                overlay = f'color=c={layer.color}:s={width}x{height}:r={self.cfg.video_framerate}:d=1,format=rgba[clr{current}];[clr{current}][{current}]blend=all_mode=and,format=rgba{over};'
            else:
                over = f'[{current}]'
                overlay = ''

            out = f'[out{current}]'
            overlay += f'{previous}{over}overlay=x={left}:y={top},format=rgba{out}'
            overlays.append(overlay)
            previous = out

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
            '-map', out,
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


    def write_preview(self):

        self.cfg.movie_mp4.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg_command = [
            self.cfg.ffmpeg,
            '-y',
            #'-threads', '0',

            '-init_hw_device', 'qsv=hw',
            '-filter_hw_device', 'hw',

            '-i', str(self.cfg.layers.world_map.png) % 0,

            '-f', 'concat',
            '-r', str(self.cfg.video_framerate),
            '-i', str(self.cfg.layers.average_location.concat),

            '-f', 'concat',
            '-r', str(self.cfg.video_framerate),
            '-i', str(self.cfg.layers.local_frequencies.concat),

            # Two overlay_qsv filters fails.
            #'-filter_complex', '[0][1]overlay_qsv[out0];[out0][2]overlay_qsv[out1]',
            #'-filter_complex', '[0][2]overlay_qsv[out1]',
            #'-filter_complex', '[0][2]overlay[out1]',
            '-filter_complex', '[0][1]overlay[out0];[out0][2]overlay_qsv[out1]',
            #'-filter_complex', '[0][1]overlay_qsv[out0];[out0][2]overlay[out1]',
            #'-filter_complex', '[0][1]overlay[out0];[out0][2]overlay[out1]',

            '-map', '[out1]',

            '-an',

            '-c:v', 'h264_qsv',
            '-preset:v', 'veryfast',
            #'-c:v', 'libx264',
            #'-preset:v', 'ultrafast',
            '-r', str(self.cfg.video_framerate),

            str(self.cfg.movie_mp4.parent/('qsv.' + self.cfg.movie_mp4.name))
        ]

        print('"' + '" "'.join(ffmpeg_command) + '"')
        subprocess.call(ffmpeg_command)


    def write_bg_fg_mp4(self):

        self.cfg.movie_mp4.parent.mkdir(parents=True, exist_ok=True)

        #start_number = 0
        #if self.cfg.movie_time:
        #    database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        #    database.row_factory = sqlite3.Row
        #    cursor = database.cursor()
        #    cursor.execute(f'SELECT MIN({self.order_key}) FROM variant WHERE time=? ORDER BY {self.order_key}', (self.cfg.movie_time,))
        #    start_number = cursor.fetchone()[0]

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
            '-f', 'image2',
            #'-r', str(self.cfg.video_framerate),
            #'-loop', '1',
            '-i', str(self.cfg.layers.background.png),
            '-f', 'image2',
            '-r', str(self.cfg.video_framerate),
            #'-start_number', str(start_number),
            '-i', str(self.cfg.layers.foreground.png),
        ]

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

        ffmpeg_command.extend([
            '-filter_complex', '[0][1]overlay[out]',
            '-map', '[out]',
            '-map', '2:a',
            #'-shortest',
        ])

        #if self.cfg.movie_limit:
        #    ffmpeg_command.extend([
        #        '-vframes', f'{self.cfg.movie_limit}',
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

