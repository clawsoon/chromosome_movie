#!/usr/bin/env python3

'''
Nearest-neighbour and 2-opt travelling salesman heuristics.

In this module, oordinates/locations are always (longitude, latitude).

This gets dramatically slower as the number of locations to visit gets larger.
Not unexpected, but I still bet that someone could make this much faster, and
probably fix bugs in my algorithms.
'''

# Great circle based on:
# https://python.plainenglish.io/calculating-great-circle-distances-in-python-cf98f64c1ea0

# 2-opt initially based on:
# https://github.com/pdrm83/py2opt/
# ...but improved.


import sys
from math import radians, degrees, sin, cos, acos
import random
#import itertools
import numpy


def build_distance_matrix(average_locations, jaccard_offset=-1, all_locations=None):
    '''
    Each entry in average_locations should be a (longitude, latitude) average
    location for a variant.

    Each entry in all_locations should be a set() of all (longitude, latitude)
    locations for a variant.

    The two lists should have the same variant order.
    '''
    #sys.stderr.write('Start distance matrix build\n')
    lon0 = numpy.radians(numpy.array([l[0] for l in average_locations], dtype=numpy.float16).reshape(1, len(average_locations)))
    lon1 = numpy.radians(numpy.array([l[0] for l in average_locations], dtype=numpy.float16).reshape(len(average_locations), 1))
    lat0 = numpy.radians(numpy.array([l[1] for l in average_locations], dtype=numpy.float16).reshape(1, len(average_locations)))
    lat1 = numpy.radians(numpy.array([l[1] for l in average_locations], dtype=numpy.float16).reshape(len(average_locations), 1))

    #value = numpy.sin(lat0) * numpy.sin(lat1) + numpy.cos(lat0) * numpy.cos(lat1) * numpy.cos(numpy.absolute(lon1-lon0))
    #clamped = numpy.clip(value, -1, 1)
    #distance_matrix = numpy.arccos(clamped)

    distance_matrix = numpy.degrees(
        numpy.arccos(
            numpy.clip(
                numpy.sin(lat0) * numpy.sin(lat1) + numpy.cos(lat0) * numpy.cos(lat1) * numpy.cos(numpy.absolute(lon1-lon0)), -1, 1)
        ))

    if jaccard_offset >= 0:
        distance_matrix += jaccard_offset
        for i in range(len(average_locations)):
            for j in range(len(average_locations)):
                intersection = all_locations[i] & all_locations[j]
                union = all_locations[i] | all_locations[j]
                if len(union) == 0:
                    jaccard_similarity = 0
                else:
                    jaccard_similarity = len(intersection) / len(union)
                distance_matrix[i,j] *= (1 - jaccard_similarity)
    #distance_matrix = numpy.sin(lat0) * numpy.sin(lat1)

    #sys.stderr.write(f'Distance matrix shape: {distance_matrix.shape}\n')
    return distance_matrix
    #return numpy.degrees(distance_matrix)


def great_circle_angle(longitude0, latitude0, longitude1, latitude1):
    if longitude0 == longitude1 and latitude0 == latitude1:
        return 0
    lon0, lat0 = radians(longitude0), radians(latitude0)
    lon1, lat1 = radians(longitude1), radians(latitude1)

    value = sin(lat0)*sin(lat1) + cos(lat0)*cos(lat1)*cos(abs(lon1-lon0))
    # Let's see if clamping stops acos from occasionally giving a math
    # domain error.
    clamped = min(max(-1, value), 1)
    angle = acos(clamped)

    return degrees(angle)


def build_old_distance_matrix(locations):
    print('start build')
    length = len(locations)
    ####distance_matrix = [[0]*length for _ in range(length)]
    distance_matrix = numpy.zeros((length, length), dtype=numpy.float16)
    for i, from_location in enumerate(locations):
        for j, to_location in enumerate(locations):
            ####distance_matrix[i][j] = great_circle_angle(
            distance_matrix[i,j] = great_circle_angle(
                    from_location[0],
                    from_location[1],
                    to_location[0],
                    to_location[1],
            )
    print('done build')
    return distance_matrix


def swap(route, swap_start, swap_end):
    return route[:swap_start] + route[swap_end:swap_start-1:-1] + route[swap_end+1:]


def route_distance(distance_matrix, route):
    ####return sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
    return sum(distance_matrix[route[i],route[i+1]] for i in range(len(route)-1))


def two_opt(distance_matrix, initial_route, improvement_threshold=0.01):
    #sys.stderr.write(f'2-opt initial route length: {len(initial_route)}\n')
    route = initial_route
    distance = route_distance(distance_matrix, route)
    #sys.stderr.write(f'2-opt initial route distance: {distance}\n')
    improvement_factor = 1
    length = len(initial_route)

    #swap_indices = list(range(1, length-1))

    while improvement_factor > improvement_threshold:
        previous_best = distance
        # I think this is supposed to be random.
        for swap_start in range(1, length - 2):
            for swap_end in range(swap_start + 1, length - 1):
                prestart = route[swap_start - 1]
                start = route[swap_start]
                end = route[swap_end]
                postend = route[swap_end + 1]
                ####before = distance_matrix[prestart][start] + distance_matrix[end][postend]
                ####after = distance_matrix[prestart][end] + distance_matrix[start][postend]
                before = distance_matrix[prestart,start] + distance_matrix[end,postend]
                after = distance_matrix[prestart,end] + distance_matrix[start,postend]
                if after < before:
                    route = swap(route, swap_start, swap_end)
                    distance = route_distance(distance_matrix, route)

        #random.shuffle(swap_indices)
        #for swap_foo in itertools.combinations(swap_indices, 2):
        #    swap_start, swap_end = sorted(swap_foo)
        #    #print(swap_start, swap_end)
        #    prestart = route[swap_start - 1]
        #    start = route[swap_start]
        #    end = route[swap_end]
        #    postend = route[swap_end + 1]
        #    before = distance_matrix[prestart][start] + distance_matrix[end][postend]
        #    after = distance_matrix[prestart][end] + distance_matrix[start][postend]
        #    if after < before:
        #        route = swap(route, swap_start, swap_end)
        #        distance = route_distance(distance_matrix, route)
        #        # Having it break here makes it much less accurate.
        #        #break


        improvement_factor = 1 - distance / previous_best

    #sys.stderr.write(f'2-opt final route distance: {distance}\n')
    #sys.stderr.write(f'2-opt final route length: {len(route)}\n')
    return route


def nearest_neighbour(distance_matrix):
    # There's probably a better way to do nearest neighbour.
    #sys.stderr.write(f'Nearest neighbour matrix: {distance_matrix.shape}\n')
    first = 0
    last = len(distance_matrix) - 1
    visited = set()
    route = [first]
    visited.add(first)
    while len(route) < last:
        current = route[-1]
        distances = distance_matrix[current] # Will this work with numpy?
        best = float('inf')
        best_index = None
        for i, distance in enumerate(distances):
            if i == current or i == last or i == first or i in visited:
                continue
            if distance < best:
                best = distance
                best_index = i
        route.append(best_index)
        visited.add(best_index)
    route.append(last)
    #sys.stderr.write(f'Nearest neighbour route length: {len(route)}\n')
    return route

def nearest_neighbour_only(locations):
    # When calling this function, put desired start and end at start and
    # end and it should keep them there.
    distance_matrix = build_distance_matrix(locations)
    initial_route = nearest_neighbour(distance_matrix)
    return initial_route

def main(average_locations, jaccard_offset=-1, all_locations=None):
    # When calling this function, put desired start and end at start and
    # end and it should keep them there.
    distance_matrix = build_distance_matrix(average_locations, jaccard_offset, all_locations)
    initial_route = nearest_neighbour(distance_matrix)
    good_route = two_opt(distance_matrix, initial_route)
    return good_route


def test():
    import random
    locations = [
        (-30, -30),
        (-20, -20),
        (-10, -10),
        (0, 0),
        (10, 10),
        (20, 20),
        (30, 30),
    ]

    locations = [
        (-155, -30),
        (-165, -20),
        (-175, -10),
        (175, 0),
        (165, 10),
        (155, 20),
        (145, 30),
        (35, 40),
        (-155, -30),
    ]

    #locations = [(random.randint(-180, 180), random.randint(-90, 90)) for _ in range(37553)]
    #locations = [(random.randint(-180, 180), random.randint(-90, 90)) for _ in range(8000)]

    for i in range(2):
        shuffled = locations[:1] + random.sample(locations[1:-1], len(locations)-2) + locations[-1:]

        #distance_matrix = build_distance_matrix(shuffled)
        #numpy_distance_matrix = build_distance_matrix(shuffled)
        #continue

        #distance_matrix = build_distance_matrix(shuffled)
        distance_matrix = build_distance_matrix(shuffled)
        initial_route = nearest_neighbour(distance_matrix)
        #initial_route = [0] + random.sample(list(range(1, len(locations)-1)), len(locations)-2) + [len(locations)-1]
        two_opt_route = two_opt(distance_matrix, initial_route)

        print(initial_route)
        for line in shuffled:
            print(line)
        print()
        for index in initial_route:
            print(shuffled[index])
        print()
        for index in two_opt_route:
            print(shuffled[index])
        print()
        print()


if __name__ == '__main__':

    #import sys
    #print(great_circle_angle(*map(float, sys.argv[1:])))

    test()


