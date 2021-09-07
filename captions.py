#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import time

lines = '''Welcome.

This is part five of
a series of five videos

showing the current
geographic locations of

1,086,919 genetic variants
from chromosome 22.

This video covers variants
from the last two centuries.

The red dots show where
a genetic variant

has been found in
a modern population.

The music indicates what
the DNA change was.

The squiggly line
around the outside

is the chromosome.

The orange dot shows
the variant's location

on the chromosome.

"Site" is the exact
location of the variant

on the chromosome.

"Count" shows where you
are in the video series.

Each population where a
genetic variant was found

is listed in
the small print.

These genetic variants
were collected by

the Simons Genome
Diversity Project

the Human Genome
Diversity Project

and the 1000
Genomes Project.

Dates were estimated by
Wohns et al. in

"A unified genealogy of
modern and ancient genomes."

The world map is
Philippe Rivière's re-creation

of Bertin's 1953 projection.

The chromsome map
uses Jakub Červený's

generalized Hilbert
space-filling curve.

Enjoy.
'''

if __name__ == '__main__':

    count = 1
    seconds = 0
    length = 3
    gap = 1
    print_header = True

    with open(sys.argv[1]) as captions:

        for line in captions:
            stripped = line.strip()
            if print_header:
                start = time.strftime('%H:%M:%S,000', time.gmtime(seconds))
                end = time.strftime('%H:%M:%S,000', time.gmtime(seconds + length))

                print(count * 10)
                print(f'{start} --> {end}')

                seconds += length
                count += 1

            if stripped.endswith('.'):
                seconds += gap

            print(stripped)

            print_header = not bool(stripped)


