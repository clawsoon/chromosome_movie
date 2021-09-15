#!/usr/bin/env python3

import sys
import os
import subprocess
import threading
import queue

'''
Start one thread to generate actionlists and put them on the queue.

For each core, generate two threads:
    Until queue is empty, controller thread consumes one actionlist from queue:
        Until success for this actionlist:
            Controller starts worker thread.
            Controller thread joins worker thread with timeout.
            Worker thread starts subprocess.
            Worker thread sends subprocess variable back to controller thread.
            Worker thread communicates actionlist to subprocess stdin.
            When subprocess finishes, worker thread finishes.
            If worker thread times out, controller kills subprocess.
            If timeout or non-zero exit code, mark not success to try again.

Why this complicated approach?  Because it's the only way I found on Windows
to not end up with Inkscape processes that spin forever doing nothing.
Multiprocessing didn't work, asyncio didn't work, and simple subprocess
didn't work.  Subprocess.communicate with timeout didn't work; Inkscape
somehow has the ability to hang it forever.  Only having the timeout in a
separate thread and killing from that thread worked.
'''

# Chunk size is an arbitrary number chosen in hope that we don't
# hang by filling up stdin/stdout/stderr pipes and don't cause some
# kind of Inkscape memory leak.
chunk_size = 200
# Per-frame timeout is an arbitrary number which is hopefully always larger
# than the average seconds to process a frame but not so large that we
# waste time needlessly.
per_frame_timeout = 2

def divide_actions(actions_queue, svg_template, png_template, frames, frame_convert, inkscape_actions):
    sys.stderr.write('Starting divide...\n')
    sys.stderr.flush()
    actions = []
    start = 0
    end = 0
    for num, frame in enumerate(frames):
        svg = svg_template % frame_convert(frame)
        png = png_template % frame_convert(frame)
        actions.append(f'file-open:{svg};export-filename:{png};{inkscape_actions}export-do;file-close;')
        if (num + 1) % chunk_size == 0:
            end = num
            sys.stderr.write(f'Queuing {start}-{end}...\n')
            sys.stderr.flush()
            actions_queue.put((start, end, actions))
            actions = []
            start = num + 1
    if actions:
        end = num
        sys.stderr.write(f'Queuing {start}-{end}...\n')
        sys.stderr.flush()
        actions_queue.put((start, end, actions))
    sys.stderr.write('Done divide.\n')
    sys.stderr.flush()

def run_inkscape(inkscape_exe, working_directory, start, end, actions, process_queue=None):
    sys.stderr.write(f'run_inkscape {start}-{end}\n')
    sys.stderr.flush()
    actions.append('quit-inkscape;')
    command = [
        inkscape_exe,
        '--shell',
    ]
    # We have to chdir to the SVG directory or Inkscape will fail to
    # find relative-href-to-relative-href links.
    #process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_directory, encoding='utf-8')
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=working_directory, encoding='utf-8')
    if process_queue:
        process_queue.put(process)
    sys.stderr.write(f'run_inkscape started {start}-{end}\n')
    sys.stderr.flush()
    out, err = process.communicate('\n'.join(actions) + '\n')
    sys.stderr.write(f'run_inkscape finished {start}-{end}\n')
    sys.stderr.flush()


def control_inkscape(actions_queue, inkscape_exe, working_directory):
    sys.stderr.write('Starting controller...\n')
    sys.stderr.flush()
    while True:
        start, end, actions = actions_queue.get()
        sys.stderr.write(f'control_inkscape popped {start}-{end}\n')
        sys.stderr.flush()
        success = False
        while not success:
            sys.stderr.write(f'control_inkscape trying {start}-{end}\n')
            process_queue = queue.Queue(1)
            worker = threading.Thread(target=run_inkscape, daemon=True, args=(inkscape_exe, working_directory, start, end, actions, process_queue))
            worker.start()
            worker.join(timeout=per_frame_timeout*chunk_size)
            process = process_queue.get()
            if process.returncode == None:
                msg = 'timed out'
                sys.stderr.write(f'control_inkscape killing {start}-{end}\n')
                sys.stderr.flush()
                process.kill()
                sys.stderr.write(f'control_inkscape killwait {start}-{end}\n')
                sys.stderr.flush()
                process.wait() # Will this hang needlessly?
                sys.stderr.write(f'control_inkscape killdone {start}-{end}\n')
                sys.stderr.flush()
            elif process.returncode == 0:
                msg = 'succeeded'
                success = True
            else:
                msg = 'failed'
            sys.stderr.write(f'Inkscape {msg} {start}-{end}.\n')
            sys.stderr.flush()
        actions_queue.task_done()
        sys.stderr.write(f'control_inkscape done {start}-{end}\n')
        sys.stderr.flush()
    sys.stderr.write('Finished controller...\n')
    sys.stderr.flush()




def svg2png(cfg, svg_template, png_template, frames=None, frame_convert=int, inkscape_actions=''):

    inkscape_exe = os.fspath(cfg.inkscape)

    working_directory = os.path.dirname(svg_template)

    svg_relative = os.path.relpath(svg_template, working_directory)
    png_relative = os.path.relpath(png_template, working_directory)

    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    if not frames:

        actions = [f'file-open:{svg_relative};export-filename:{png_relative};{inkscape_actions}export-do;quit-inkscape;']
        run_inkscape(inkscape_exe, working_directory, 1, 1, actions)

    else:

        thread_count = os.cpu_count() - 1
        #thread_count = 1
        threads = []
        actions_queue = queue.Queue(1)

        producer = threading.Thread(target=divide_actions, daemon=False, args=(actions_queue, svg_relative, png_relative, frames, frame_convert, inkscape_actions))
        producer.start()
        threads.append(producer)

        for num in range(thread_count):
            controller = threading.Thread(target=control_inkscape, daemon=True, args=(actions_queue, inkscape_exe, working_directory))
            controller.start()
            threads.append(controller)

        sys.stderr.write('Inkscape work started.\n')
        producer.join()
        actions_queue.join()
        sys.stderr.write('Inkscape work complete.\n')



