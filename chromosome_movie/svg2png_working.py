#!/usr/bin/env python3

import sys
import os
import subprocess

# Chunk size is an arbitrary number chosen in hope that we don't
# hang by filling up stdin/stdout/stderr pipes and don't cause some
# kind of Inkscape memory leak.
chunk_size = 300
timeout = 3 * chunk_size

def divide_actions(svg_template, png_template, frames, frame_convert, inkscape_actions):
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
    # We have to chdir to the SVG directory or Inkscape will fail to
    # find relative-href-to-relative-href links.
    exit = -1
    while exit != 0:
        #inkscape = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory, encoding='utf-8')
        inkscape = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=working_directory, encoding='utf-8')
        sys.stderr.write('Started...\n')
        sys.stderr.flush()
        try:
            out, err = inkscape.communicate('\n'.join(actions) + '\n', timeout=timeout)
        except subprocess.TimeoutExpired:
            sys.stderr.write('Inkscape timed out...\n')
            sys.stderr.flush()
            # Sometimes inkscape gets stuck.
            # This is how the manual says to kill it and clean it up.
            # Hopefully this gives us a non-zero exit code.
            inkscape.kill()
            sys.stderr.write('Inkscape killed...\n')
            sys.stderr.flush()
            # This hangs on Windows:
            # https://bugs.python.org/issue43346
            #out, err = inkscape.communicate()
            #sys.stderr.write('Inkscape cleaned up...\n')
            #sys.stderr.flush()
        sys.stderr.write('Done inkscape.\n')
        sys.stderr.flush()
        if False:
            if out or err:
                sys.stderr.write(out)
                sys.stderr.write(err)
        exit = inkscape.returncode
        if exit != 0:
            sys.stderr.write('Restarting inkscape.\n')
            sys.stderr.flush()

def queue_inkscape(inkscape_exe, working_directory, chunks):
    cumulative = 0
    for chunk in chunks:
        cumulative += len(chunk)
        sys.stderr.write(f'Converting... {cumulative}\n')
        run_inkscape(inkscape_exe, working_directory, chunk)


def svg2png(cfg, svg_template, png_template, frames=None, frame_convert=int, inkscape_actions=''):

    inkscape_exe = os.fspath(cfg.inkscape)

    working_directory = os.path.dirname(svg_template)

    svg_relative = os.path.relpath(svg_template, working_directory)
    png_relative = os.path.relpath(png_template, working_directory)

    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    if not frames:
        actions = [f'file-open:{svg_relative};export-filename:{png_relative};{inkscape_actions}export-do;quit-inkscape;']
        run_inkscape(inkscape_exe, working_directory, actions)
        sys.stderr.write(f'Converted... 1\n')
    else:
        chunks = divide_actions(svg_relative, png_relative, frames, frame_convert, inkscape_actions)
        queue_inkscape(inkscape_exe, working_directory, chunks)


