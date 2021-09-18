#!/usr/bin/env python3

import sys
import os
import subprocess
import sqlite3
import math

import midiutil

from . import order

class Audio():

    # Pan is 0-127 left-right.
    # However... I kind of like it better with no panning.
    # Vibraphone: program 12, duration 12
    # Marimba: program 13, duration 12
    # Dulcimer: program 16, duration 1
    # Harp: program 46, duration 12
    notes = {
        'G5': {'pitch': 79, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'F5': {'pitch': 77, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'E5': {'pitch': 76, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'D5': {'pitch': 74, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'C5': {'pitch': 72, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'B4': {'pitch': 71, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'A4': {'pitch': 69, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'G4': {'pitch': 67, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'F4': {'pitch': 65, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'E4': {'pitch': 64, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'D4': {'pitch': 62, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
        'C4': {'pitch': 60, 'program': 46, 'duration': 12, 'channel': 0, 'pan': 64},
    }

    def __init__(self, cfg):
        self.cfg = cfg

    def write_midi(self):
        self.cfg.audio_midi.parent.mkdir(parents=True, exist_ok=True)
        track_count = 12
        track = 0
        channel = 0
        channel_count = 1
        time = 0
        duration = 12
        tempo = self.cfg.video_framerate * 60
        base_volume = 48
        volume_cycle = 48
        volume_cycle_max = 0

        midi = midiutil.MIDIFile(track_count*channel_count)
        midi.addTempo(0, time, tempo)

        for info in self.notes.values():
            midi.addProgramChange(track, info['channel'], time, info['program'])
            midi.addControllerEvent(track, info['channel'], time, midiutil.MidiFile.controllerEventTypes['pan'], info['pan'])

        #database = sqlite3.connect(self.cfg.database_readonly_uri, uri=True)
        #cursor = database.cursor()
        #select = f'SELECT ancestral_state, derived_state FROM variant'
        #if self.cfg.movie_time:
        #    select += f' WHERE time={self.cfg.movie_time}'
        #select += f' ORDER BY order_{self.cfg.order}'
        #if self.cfg.movie_limit:
        #    select += f' LIMIT {self.cfg.movie_limit}'
        #cursor.execute(select)
        #for num, (ancestral_state, derived_state) in enumerate(cursor):
        self.order = order.Order(self.cfg)
        for num, variant in enumerate(self.order.select()):
            ancestral_state = variant['ancestral_state']
            derived_state = variant['derived_state']
            if num % 1000 == 0:
                sys.stderr.write(f'{num}\n')
            volume = int(base_volume + volume_cycle_max * math.sin(num/volume_cycle*math.pi))
            note_name = self.cfg.audio_notes[(ancestral_state, derived_state)]
            note = self.notes[note_name]
            midi_note = note['pitch']
            track = time % track_count
            duration = note['duration']
            midi.addNote(track, channel, midi_note, time, duration, volume)
            time += 1
        with open(self.cfg.audio_midi, 'wb') as output:
            midi.writeFile(output)

    def write_wav(self):
        if self.cfg.audio_pipe:
            print('config.audio_pipe is set.  Not creating WAV.')
            return
        self.cfg.audio_wav.parent.mkdir(parents=True, exist_ok=True)
        command = [
            os.fspath(self.cfg.timidity),
            '-OwS', # Output WAV format, stereo.
            '-o', os.fspath(self.cfg.audio_wav),
            #'-OFS', # Output FLAC format, stereo.
            #'-o', os.fspath(self.cfg.audio_wav) + '.flac',
            '-s', str(self.cfg.audio_samplerate),
            os.fspath(self.cfg.audio_midi),
        ]
        print('"' + '" "'.join(command) + '"')
        subprocess.call(command)

