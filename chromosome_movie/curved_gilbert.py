#!/usr/bin/env python3

import sys

from . import gilbert2d

def gilbert2a(width, height, x=0, y=0, axis=None):
    '''
    Allow gilbert curves to cover an arbitrary rectangle.
    '''

    if not axis:
        axis = 'width' if abs(width) >= abs(height) else 'height'

    if axis == 'width':
        yield from gilbert2d.generate(x, y, width, 0, 0, height)
    elif axis == 'height':
        yield from gilbert2d.generate(x, y, 0, height, width, 0)
    else:
        raise Exception('Unrecognized axis')


class CurvedGilbert():

    def __init__(self, sections, radius=8, width=2560, height=1440, shadows=True):
        self.sections = sections
        self.radius = radius
        self.width = width
        self.height = height
        self.shadows = shadows

        self.step = 2 * self.radius

        self.gilbert = []
        self.points = []
        self.sweeps = []
        self.commands = []
        self.path = ''

        self.get_gilbert()
        self.set_points()


    def generate_path(self):
        for section in self.sections:
            width = (section['end'][0] - section['start'][0]) // self.step
            height = (section['end'][1] - section['start'][1]) // self.step

            x = section['start'][0] // self.step
            y = section['start'][1] // self.step

            # Sometimes this gets weird depending on step and dimensions.
            if width < 0:
                x -= 1
            if height < 0:
                y -= 1

            for x, y in gilbert2a(width, height, x, y, axis=section['axis']):
                yield x, y

    def get_gilbert(self):
        self.gilbert = [(p[0]*2*self.radius+self.radius, p[1]*2*self.radius+self.radius) for p in self.generate_path()]


    def set_points(self):
        '''
        We do this by dividing up the pattern into a sequence of 30 degree
        arcs with identical radius.

        Note that going in a straight line results in 4 arcs, while going
        around a corner results in 3 arcs, so the distances travelled are
        not proportional to those of the straight-line gilbert curve.
        '''

        cos30 = (3**.5)/2
        q = 1 - cos30

        corner_command = 'A'
        corner0 = [0, q, 0.5, 1]
        neg_corner0 = [-n for n in corner0]
        corner1 = [1, 0.5, q, 0]
        neg_corner1 = [-n for n in corner1]

        #straight_command = 'A'
        #straight0 = [0, q, 2*q, q, 0]
        # Straight straights look a little better than wiggly straights.
        straight_command = 'L'
        straight0 = [0, 0, 0, 0, 0]
        neg_straight0 = [-n for n in straight0]
        straight1 = [-1, -0.5, 0, 0.5, 1]
        neg_straight1 = [-n for n in straight1]

        # We assume that x increases as we go right and y increases as we
        # go down, i.e. typical computer graphics rather than typical Cartesian.

        # Somebody smarter than me can figure out the rules underlying these
        # patterns and simplify this.

        corner_patterns = {
            ('up', 'right'): (corner0, corner1),
            ('up', 'left'): (neg_corner0, corner1),
            ('down', 'right'): (corner0, neg_corner1),
            ('down', 'left'): (neg_corner0, neg_corner1),
            ('right', 'down'): (neg_corner1, corner0),
            ('left', 'down'): (corner1, corner0),
            ('right', 'up'): (neg_corner1, neg_corner0),
            ('left', 'up'): (corner1, neg_corner0),
        }

        straight_patterns = {
            ('down', 'east'): (straight0, straight1),
            ('down', 'west'): (neg_straight0, straight1),
            ('up', 'east'): (straight0, neg_straight1),
            ('up', 'west'): (neg_straight0, neg_straight1),
            ('right', 'south'): (straight1, straight0),
            ('right', 'north'): (straight1, neg_straight0),
            ('left', 'south'): (neg_straight1, straight0),
            ('left', 'north'): (neg_straight1, neg_straight0),
        }

        sides = {
            'down': 'north',
            'up': 'south',
            'right': 'west',
            'left': 'east',
        }

        all_sweeps = {
            # 1: clockwise
            # 0: counterclockwise

            ('up', 'right'):    (1, 1, 1),
            ('up', 'left'):     (0, 0, 0),
            ('down', 'right'):  (0, 0, 0),
            ('down', 'left'):   (1, 1, 1),
            ('right', 'down'):  (1, 1, 1),
            ('left', 'down'):   (0, 0, 0),
            ('right', 'up'):    (0, 0, 0),
            ('left', 'up'):     (1, 1, 1),
            ('down', 'west'):   (1, 0, 0, 1),
            ('down', 'east'):   (0, 1, 1, 0),
            ('up', 'west'):     (0, 1, 1, 0),
            ('up', 'east'):     (1, 0, 0, 1),
            ('right', 'south'): (1, 0, 0, 1),
            ('right', 'north'): (0, 1, 1, 0),
            ('left', 'south'):  (0, 1, 1, 0),
            ('left', 'north'):  (1, 0, 0, 1),
        }

        side = None

        for index in range(1, len(self.gilbert)-1):

            before = self.gilbert[index-1]
            current = self.gilbert[index]
            after = self.gilbert[index+1]

            if (before[0] != current[0] and before[1] != current[1]) or (after[0] != current[0] and after[1] != current[1]):
                raise Exception("Sorry, we don't do diagonals yet.")

            # I'm sure there is a cleverer way to do this, but this will do
            # for now.
            if before[0] > current[0]:
                incoming = 'left'
            elif before[0] < current[0]:
                incoming = 'right'
            elif before[1] > current[1]:
                incoming = 'up'
            elif before[1] < current[1]:
                incoming = 'down'

            if current[0] > after[0]:
                outgoing = 'left'
            elif current[0] < after[0]:
                outgoing = 'right'
            elif current[1] > after[1]:
                outgoing = 'up'
            elif current[1] < after[1]:
                outgoing = 'down'

            if incoming != outgoing:
                command = corner_command
                patterns = corner_patterns[(incoming, outgoing)]
                sweeps = all_sweeps[(incoming, outgoing)]
                #sys.stderr.write(f'{incoming} {outgoing} {patterns} {sweeps}\n')
                # A corner sets the side, and a straight uses it.
                side = sides[incoming]
            else:
                if not side:
                    # Making an arbitrary starting decision here.
                    if incoming in ['left', 'right']:
                        side = 'south'
                    else:
                        side = 'west'
                # Keep things on the same side.
                command = straight_command
                patterns = straight_patterns[(incoming, side)]
                sweeps = all_sweeps[(incoming, side)]
                #sys.stderr.write(f'{incoming} {side} {patterns} {sweeps}\n')

            if index == 1:
                x = patterns[0][0]
                y = patterns[1][0]
                point = (current[0] + x*self.radius, current[1] + y*self.radius)
                self.commands.append('M')
                self.points.append(point)
                self.sweeps.append(0)

            for x, y, sweep in zip(patterns[0][1:], patterns[1][1:], sweeps):
                point = (current[0] + x*self.radius, current[1] + y*self.radius)
                self.commands.append(command)
                self.points.append(point)
                self.sweeps.append(sweep)

    def generate_svg_path(self):
        x_axis_rotation = 0
        large_arc = 0 # All of our arcs are constructed of <180 degree segments.
        yield '<path id="gilbert" fill="none" d="'
        for command, point, sweep in zip(self.commands, self.points, self.sweeps):
            middle = f'{self.radius} {self.radius} {x_axis_rotation} {large_arc} {sweep}' if command == 'A' else ''
            yield f'{command} {middle} {point[0]:.1f} {point[1]:.1f}'
        yield '"/>'
        
        

    def generate_svg(self):

        #sys.stderr.write(f'length: {len(self.commands)}\n')

        #yield f'<svg width="{self.width}" height="{self.height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">'
        yield '''
 <defs>
  <filter style="color-interpolation-filters:sRGB;" id="gilbertshadow">
   <feGaussianBlur stdDeviation="2 2" result="blur"/>
  </filter>
        '''

        yield from self.generate_svg_path()
        yield ' </defs>'

        # TODO: Make stroke widths configurable.
        if self.shadows:
            yield ' <use xlink:href="#gilbert" stroke="rgb(160,160,160)" stroke-width="9" style="filter:url(#gilbertshadow);"/>'

        yield ' <use xlink:href="#gilbert" stroke="rgb(0,0,0)" stroke-width="3"/>'

        # Test circle.
        #yield f'<circle cx="{self.points[500][0]}" cy="{self.points[500][1]}" r="{2 * self.radius}" fill="orange" stroke="red" stroke-width="{self.radius/2}"/>'

        #yield '</svg>'

