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
'''

# Chunk size is an arbitrary number chosen in hope that we don't
# hang by filling up stdin/stdout/stderr pipes and don't cause some
# kind of Inkscape memory leak.
chunk_size = 300
# Per-frame timeout is an arbitrary number which is hopefully always larger
# than the average seconds to process a frame but not so large that we
# waste time needlessly.
per_frame_timeout = 3

def divide_actions(actions_queue, svg_template, png_template, frames, frame_convert, inkscape_actions):
    actions = []
    for num, frame in enumerate(frames):
        svg = svg_template % frame_convert(frame)
        png = png_template % frame_convert(frame)
        actions.append(f'file-open:{svg};export-filename:{png};{inkscape_actions}export-do;file-close;')
        if (num + 1) % chunk_size == 0:
            sys.stderr.write('Queuing {num}...\n')
            sys.stderr.flush()
            actions_queue.put(actions)
            actions = []
    if actions:
        sys.stderr.write('Queuing {num}...\n')
        sys.stderr.flush()
        actions_queue.put(actions)

def run_inkscape(process_queue, inkscape_exe, working_directory, actions):
    sys.stderr.write('Starting inkscape...\n')
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
    process_queue.put(process)
    sys.stderr.write('Started inkscape...\n')
    sys.stderr.flush()
    out, err = process.communicate('\n'.join(actions) + '\n')
    sys.stderr.write('Finished inkscape...\n')
    sys.stderr.flush()


def control_inkscape(actions_queue, inkscape_exe, working_directory):
    while True:
        actions = actions_queue.get()
        success = False
        while not success:
            process_queue = queue.Queue(1)
            worker = threading.Thread(target=run_inkscape, daemon=True, args=(process_queue, inkscape_exe, working_directory, actions))
            worker.start()
            worker.join(timeout=per_frame_timeout*chunk_size)
            process = process_queue.get()
            if process.returncode == None:
                msg = 'timed out'
                sys.stderr.write('killing...\n')
                sys.stderr.flush()
                process.kill()
                sys.stderr.write('waiting...\n')
                sys.stderr.flush()
                process.wait() # Will this hang needlessly?
                sys.stderr.write('done...\n')
                sys.stderr.flush()
            elif process.returncode == 0:
                msg = 'succeeded'
                success = True
            else:
                msg = 'failed'
            sys.stderr.write(f'Inkscape {msg}.\n')
            sys.stderr.flush()
        actions_queue.task_done()




def svg2png(cfg, svg_template, png_template, frames=None, frame_convert=int, inkscape_actions=''):

    inkscape_exe = os.fspath(cfg.inkscape)

    working_directory = os.path.dirname(svg_template)

    svg_relative = os.path.relpath(svg_template, working_directory)
    png_relative = os.path.relpath(png_template, working_directory)

    sys.stderr.write(f'Converting... {svg_template} -> {png_template}\n')

    threads = []
    actions_queue = queue.Queue(1)

    if not frames:
        actions_queue.put([f'file-open:{svg_relative};export-filename:{png_relative};{inkscape_actions}export-do;quit-inkscape;'])
        controller = threading.Thread(target=control_inkscape, daemon=True, args=(actions_queue, inkscape_exe, working_directory))
        controller.start()
        threads.append(controller)
    else:

        producer = threading.Thread(target=divide_actions, daemon=True, args=(actions_queue, svg_relative, png_relative, frames, frame_convert, inkscape_actions))
        producer.start()
        threads.append(producer)

        for num in range(os.cpu_count()):
            controller = threading.Thread(target=control_inkscape, daemon=True, args=(actions_queue, inkscape_exe, working_directory))
            controller.start()
            threads.append(controller)

    sys.stderr.write('Inkscape work started.\n')
    actions_queue.join()
    sys.stderr.write('Inkscape work complete.\n')



