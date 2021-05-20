#!/usr/bin/env python3

import sys
import os
import subprocess

def run_inkscape(cfg, actions):
    command = [
        os.fspath(cfg.inkscape),
        '--shell',
    ]
    inkscape = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    out, err = inkscape.communicate('\n'.join(actions) + '\n')
    #if out or err:
    #    sys.stderr.write(out)
    #    sys.stderr.write(err)
    return out, err

def svg2png(cfg, svg_template, png_template, frames, frame_convert=int):
    # Chunk size is an arbitrary number chosen in hope that we don't
    # hang by filling up stdin/stdout/stderr pipes and don't cause some
    # kind of Inkscape memory leak.
    chunk_size = 500
    index = 0
    actions = []
    for frame in frames:
        svg = svg_template % frame_convert(frame)
        png = png_template % frame_convert(frame)
        #actions.append(f'file-open:{svg};export-filename:{png};export-do;file-close:{svg};')
        # Let's live dangerously and try it without closing the files.
        actions.append(f'file-open:{svg};export-filename:{png};export-do;')
        if index >= chunk_size:
            sys.stderr.write(f'Converting... {svg} -> {png}\n')
            sys.stderr.flush()
            run_inkscape(cfg, actions)
            index = 0
            actions.clear()
        index += 1
    # Take care of any leftovers.
    if actions:
        sys.stderr.write(f'Finishing... {svg} -> {png}\n')
        sys.stderr.flush()
        run_inkscape(cfg, actions)
    run_inkscape(cfg, ['quit'])

# TODO: Add a way to be able to run this from the command line for a single SVG.

