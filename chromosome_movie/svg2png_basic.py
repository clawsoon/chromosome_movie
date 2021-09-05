#!/usr/bin/env python3

import sys
import os
import subprocess
import time
#import asyncio
#import multiprocessing

def divide_actions(chunk_size, svg_template, png_template, frames, frame_convert, inkscape_actions):
    actions = []
    for num, frame in enumerate(frames):
        svg = svg_template % frame_convert(frame)
        png = png_template % frame_convert(frame)
        actions.append(f'file-open:{svg};export-filename:{png};{inkscape_actions}export-do;file-close;')
        if (num + 1) % chunk_size == 0:
            yield actions
            actions = []
    if actions:
        yield actions

def run_inkscape(inkscape_exe, working_directory, actions):
    sys.stderr.write('Starting inkscape...\n')
    sys.stderr.flush()
    actions.append('quit-inkscape;')
    command = [
        inkscape_exe,
        '--shell',
    ]
    inkscape = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory)
    sys.stderr.write('Started...\n')
    sys.stderr.flush()
    action_bytes = ('\n'.join(actions) + '\n').encode(encoding='UTF-8')
    out, err = inkscape.communicate(action_bytes)
    sys.stderr.write('Done inkscape.\n')
    sys.stderr.flush()
    #if out or err:
    #    sys.stderr.write(out)
    #    sys.stderr.write(err)
    #return out, err

def queue_inkscape(inkscape_exe, working_directory, chunks):
    cumulative = 0
    for chunk in chunks:
        cumulative += len(chunk)
        sys.stderr.write(f'Converting... {cumulative}\n')
        run_inkscape(inkscape_exe, working_directory, chunk)


def svg2png(cfg, svg_template, png_template, frames=None, frame_convert=int, inkscape_actions=''):

    inkscape_exe = os.fspath(cfg.inkscape)

    # We have to convert to absolute paths and chdir to the SVG directory
    # or Inkscape will fail to find relative-href-to-relative-href links.
    svg_absolute = str(svg_template.absolute())
    png_absolute = str(png_template.absolute())
    #os.chdir(svg_template.parent)


    # Chunk size is an arbitrary number chosen in hope that we don't
    # hang by filling up stdin/stdout/stderr pipes and don't cause some
    # kind of Inkscape memory leak.
    chunk_size = 300
    #index = 0
    #actions = []
    #frames = frames or []
    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    if not frames:
        actions = [f'file-open:{svg_absolute};export-filename:{png_absolute};export-do;quit-inkscape;']
        run_inkscape(inkscape_exe, svg_template.parent, actions)
        sys.stderr.write(f'Converted... 1\n')
    else:
        chunks = divide_actions(chunk_size, svg_absolute, png_absolute, frames, frame_convert, inkscape_actions)
        queue_inkscape(inkscape_exe, svg_template.parent, chunks)

