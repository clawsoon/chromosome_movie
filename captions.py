#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import time
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--force-gap', action='store_true')
    parser.add_argument('source')

    args = parser.parse_args()

    seconds = args.offset
    count = 1
    length = 3
    gap = 1
    print_header = True

    with open(args.source) as captions:

        for line in captions:
            stripped = line.strip()
            if print_header:
                start = time.strftime('%H:%M:%S,000', time.gmtime(seconds))
                end = time.strftime('%H:%M:%S,000', time.gmtime(seconds + length))

                print(count * 10)
                print(f'{start} --> {end}')

                seconds += length
                count += 1

            if stripped.endswith('.') and not args.force_gap:
                seconds += gap

            print(stripped)

            print_header = not bool(stripped)

            if print_header and args.force_gap:
                seconds += gap


