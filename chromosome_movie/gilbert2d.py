#!/usr/bin/env python3

# Generalized Hilbert ("gilbert") space-filling curves, from:
# https://github.com/jakubcerveny/gilbert/

# BSD 2-Clause License
# 
# Copyright (c) 2018, Jakub Červený
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# 
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

def sgn(x):
    return -1 if x < 0 else (1 if x > 0 else 0)


def generate(x, y, ax, ay, bx, by):
    """
    Generalized Hilbert ('gilbert') space-filling curve for arbitrary-sized
    2D rectangular grids.
    """

    w = abs(ax + ay)
    h = abs(bx + by)

    (dax, day) = (sgn(ax), sgn(ay)) # unit major direction
    (dbx, dby) = (sgn(bx), sgn(by)) # unit orthogonal direction

    if h == 1:
        # trivial row fill
        for i in range(0, w):
            yield(x, y)
            (x, y) = (x + dax, y + day)
        return

    if w == 1:
        # trivial column fill
        for i in range(0, h):
            yield(x, y)
            (x, y) = (x + dbx, y + dby)
        return

    (ax2, ay2) = (ax//2, ay//2)
    (bx2, by2) = (bx//2, by//2)

    w2 = abs(ax2 + ay2)
    h2 = abs(bx2 + by2)

    if 2*w > 3*h:
        if (w2 % 2) and (w > 2):
            # prefer even steps
            (ax2, ay2) = (ax2 + dax, ay2 + day)

        # long case: split in two parts only
        yield from generate(x, y, ax2, ay2, bx, by)
        yield from generate(x+ax2, y+ay2, ax-ax2, ay-ay2, bx, by)

    else:
        if (h2 % 2) and (h > 2):
            # prefer even steps
            (bx2, by2) = (bx2 + dbx, by2 + dby)

        # standard case: one step up, one long horizontal, one step down
        yield from generate(x, y, bx2, by2, ax2, ay2)
        yield from generate(x+bx2, y+by2, ax, ay, bx-bx2, by-by2)
        yield from generate(x+(ax-dax)+(bx2-dbx), y+(ay-day)+(by2-dby),
                 -bx2, -by2, -(ax-ax2), -(ay-ay2))


def gilbert2d(width, height):

    if width >= height:
        yield from generate(0, 0, width, 0, 0, height)
    else:
        yield from generate(0, 0, 0, height, width, 0)

