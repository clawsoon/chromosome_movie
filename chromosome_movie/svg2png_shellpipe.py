#!/usr/bin/env python3

import sys
import os
import subprocess
import time
import random
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
    action_bytes = ('\n'.join(actions) + '\n').encode(encoding='UTF-8')
    filename = f'actions-{random.random()}'
    filepath = working_directory/filename
    with open(filepath, 'wb') as output:
        output.write(action_bytes)

    # Do I like doing it this way?  No... no, I do not.
    #command = f'"{inkscape_exe}" --shell < "{filename}"'
    command = f'inkscape.com --shell < "{filename}"'
    inkscape = subprocess.Popen(command, shell=True, cwd=working_directory)
    sys.stderr.write('Started...\n')
    sys.stderr.flush()
    #inkscape.stdin.write(action_bytes)
    #inkscape.stdin.close()
    #sys.stderr.write('stdin written...\n')
    #sys.stderr.flush()
    return inkscape

    #out, err = inkscape.communicate(action_bytes)
    #sys.stderr.write('Done inkscape.\n')
    #sys.stderr.flush()
    #if out or err:
    #    sys.stderr.write(out)
    #    sys.stderr.write(err)
    #return out, err

def queue_inkscape(inkscape_exe, working_directory, chunks):
    workers = []
    num_workers = os.cpu_count()
    cumulative = 0
    for chunk in chunks:
        if len(workers) < num_workers:
            cumulative += len(chunk)
            sys.stderr.write(f'Converting... {cumulative}\n')
            worker = run_inkscape(inkscape_exe, working_directory, chunk)
            workers.append(worker)
        while len(workers) == num_workers:
            for worker in workers:
                if worker.poll() != None:
                    sys.stderr.write('Done inkscape.\n')
                    workers.remove(worker)
                    break
                time.sleep(1)


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

        #pool = multiprocessing.Pool()
        #result = pool.imap(run_inkscape, divide_actions(chunk_size, svg_absolute, png_absolute, frames, frame_convert, inkscape_actions))
        #cumulative = 0
        #for chunk in chunks:
        #    # Have to accumulate before run_inkscape adds the quit command
        #    # or else the total will be wrong.
        #    cumulative += len(chunk)
        #    run_inkscape(chunk)
        #    sys.stderr.write(f'Converted... {cumulative}\n')
        #    sys.stderr.flush()

        #result = pool.map(run_inkscape, chunks)
        #for i, result in enumerate(pool.imap_unordered(run_inkscape, chunks), 1):
        #    sys.stderr.write(f'Converted {i*chunk_size}\n')
        #    sys.stderr.flush()


    #for num, frame in enumerate(frames):
    #    svg = svg_absolute % frame_convert(frame)
    #    png = png_absolute % frame_convert(frame)
    #    #actions.append(f'file-open:{svg};export-filename:{png};export-do;file-close:{svg};')
    #    # Let's live dangerously and try it without closing the files.
    #    actions.append(f'file-open:{svg};export-filename:{png};{inkscape_actions}export-do;')
    #    if index >= chunk_size:
    #        sys.stderr.write(f'Converting... {num}\n')
    #        actions.append('quit-inkscape;')
    #        run_inkscape(cfg, actions)
    #        index = 0
    #        actions.clear()
    #    index += 1
    ## Take care of any leftovers.
    #if not frames:
    #    actions.append(f'file-open:{svg_template};export-filename:{png_template};export-do;')
    #    num = 0
    #if actions:
    #    sys.stderr.write(f'Finishing... {num}\n')
    #    sys.stderr.flush()
    #    actions.append('quit-inkscape;')
    #    run_inkscape(cfg, actions)
    #run_inkscape(cfg, ['quit'])

# TODO: Add a way to be able to run this from the command line for a single SVG.

