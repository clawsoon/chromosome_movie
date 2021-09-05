#!/usr/bin/env python3

import sys
import os
import subprocess
import asyncio
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

async def run_inkscape(inkscape_exe, working_directory, queue):
    while True:
        actions = await queue.get()
        sys.stderr.write('Starting inkscape...\n')
        sys.stderr.flush()
        actions.append('quit-inkscape;')
        command = [
            inkscape_exe,
            '--shell',
        ]
        inkscape = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=working_directory)
        action_bytes = ('\n'.join(actions) + '\n').encode(encoding='UTF-8')
        out, err = await inkscape.communicate(action_bytes)
        queue.task_done()
        sys.stderr.write('Done inkscape.\n')
        sys.stderr.flush()
        if out or err:
            sys.stderr.write(out)
            sys.stderr.write(err)
        #return out, err

async def async_inkscape(inkscape_exe, svg_template, chunks):
    queue = asyncio.Queue(1)
    workers = []
    for i in range(os.cpu_count()):
        worker = asyncio.create_task(run_inkscape(inkscape_exe, svg_template.parent, queue))
        workers.append(worker)

    cumulative = 0
    for chunk in chunks:
        cumulative += len(chunk)
        await queue.put(chunk)
        sys.stderr.write(f'Queuing... {cumulative}\n')
        sys.stderr.flush()

    await queue.join()

    for worker in workers:
        worker.cancel()

    await asyncio.gather(*workers, return_exceptions=True)

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
    chunk_size = 50
    #index = 0
    #actions = []
    #frames = frames or []
    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    if not frames:
        actions = [f'file-open:{svg_absolute};export-filename:{png_absolute};export-do;quit-inkscape;']
        run_inkscape(actions)
        sys.stderr.write(f'Converted... 1\n')
    else:
        chunks = divide_actions(chunk_size, svg_absolute, png_absolute, frames, frame_convert, inkscape_actions)
        asyncio.run(async_inkscape(inkscape_exe, svg_template, chunks))

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

