#!/usr/bin/env python3

import sys
import os
import subprocess
import multiprocessing

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


def svg2png(cfg, svg_template, png_template, frames=None, frame_convert=int, inkscape_actions=''):

    inkscape_exe = os.fspath(cfg.inkscape)

    # We have to convert to absolute paths and chdir to the SVG directory
    # or Inkscape will fail to find relative-href-to-relative-href links.
    svg_absolute = str(svg_template.absolute())
    png_absolute = str(png_template.absolute())
    #os.chdir(svg_template.parent)

    def run_inkscape(actions):
        actions.append('quit-inkscape;')
        command = [
            inkscape_exe,
            '--shell',
        ]
        inkscape = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', cwd=svg_template.parent)
        out, err = inkscape.communicate('\n'.join(actions) + '\n')
        #if out or err:
        #    sys.stderr.write(out)
        #    sys.stderr.write(err)
        #return out, err

    # Chunk size is an arbitrary number chosen in hope that we don't
    # hang by filling up stdin/stdout/stderr pipes and don't cause some
    # kind of Inkscape memory leak.
    chunk_size = 300
    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    if not frames:
        actions = [f'file-open:{svg_absolute};export-filename:{png_absolute};export-do;quit-inkscape;']
        run_inkscape(actions)
        sys.stderr.write(f'Converted... 1\n')
    else:
        pool = multiprocessing.Pool()
        for i, result in enumerate(pool.imap_unordered(run_inkscape, chunks), 1):
            sys.stderr.write(f'Converted {i*chunk_size}\n')
            sys.stderr.flush()

