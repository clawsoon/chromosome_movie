import math

'''
Mostly based on:
https://github.com/d3/d3-geo-projection/blob/master/src/
'''

def rotate_longitude(longitude, rotation):
    longitude += rotation
    if longitude < -math.pi:
        longitude += 2*math.pi
    elif longitude > math.pi:
        longitude -= 2*math.pi
    return longitude

def rotate_latitude(longitude, latitude, rotation):
    x = math.cos(longitude) * math.cos(latitude)
    y = math.sin(longitude) * math.cos(latitude)
    z = math.sin(latitude)
    k = z * math.cos(rotation) + x * math.sin(rotation)
    longitude = math.atan2(y, x * math.cos(rotation) - z * math.sin(rotation))
    latitude = math.asin(k)
    return longitude, latitude

def projection(raw, rotation, *args):
    parent = raw(*args)
    def project(longitude, latitude):
        longitude = math.radians(longitude)
        latitude = math.radians(latitude)
        if len(rotation) > 0 and rotation[0]:
            longitude = rotate_longitude(longitude, math.radians(rotation[0]))
        if len(rotation) > 1 and rotation[1]:
            longitude, latitude = rotate_latitude(longitude, latitude, math.radians(rotation[1]))
        x, y = parent(longitude, latitude)
        return x, y
    return project


def natural_earth_2_raw():
    def projection(longitude, latitude):

        scale = 1.424229168755983
        x = longitude * (0.84719 - 0.13063 * latitude**2 + latitude**12 * (-0.04515 + 0.05494 * latitude**2 - 0.02326 * latitude**4 + 0.00331 * latitude**6))

        y = latitude * (1.01183 + latitude**8 * (-0.02625 + 0.01926 * latitude**2 - 0.00396 * latitude**4))

        return x/scale, y/scale
    return projection

def natural_earth_2(rotation):
    return projection(natural_earth_2_raw, rotation)


#def azimuthal(scale_function):
#    def projection(x, y): # Why is this x, y and not longitude, latitude?
#        cosx = math.cos(x)
#        cosy = math.cos(y)
#        k = scale_function(cosx * cosy)
#        if k == float('inf'):
#            return 2, 0
#        return k * cosy * math.sin(x), k * math.sin(y)
#    return projection
#
#def azimuthal_equal_area_raw():
#    def scale_function(cosxcosy):
#        if cosxcosy == -1:
#            return float('inf')
#        return (2 / (1 + cosxcosy))**.5
#    parent = azimuthal(scale_function)
#    scale = 2**.5
#    def projection(longitude, latitude):
#        x, y = parent(longitude, latitude)
#        return x/scale, y/scale
#    return projection
#
#def azimuthal_equal_area(rotation):
#    return projection(azimuthal_equal_area_raw, rotation)
#
#def hammer_raw(A, B):
#    parent = azimuthal_equal_area_raw()
#    if B == 1:
#        return parent
#    def projection(longitude, latitude):
#        x, y = parent(longitude / B, latitude)
#        return x*A, y
#    return projection
#
#def hammer(rotation, A, B):
#    return projection(hammer_raw, rotation, A, B)
#
#
#def bertin_raw():
#
#    # For some reason the curves just aren't quite right.
#    # Had to use pyproj instead.
#    parent = hammer_raw(1.68, 2)
#    fu = 1.4
#    k = 12
#    def projection(longitude, latitude):
#        # Assume we have rotated radians here.
#        if longitude + latitude < -fu:
#            u = (longitude - latitude + 1.6) * (longitude + latitude + fu) / 8
#            longitude += u
#            latitude -= 0.8 * u * math.sin(latitude + math.pi / 2)
#
#        x, y = parent(longitude, latitude)
#
#        d = (1 - math.cos(longitude * latitude)) / k
#
#        if y < 0:
#            x *= 1 + d
#
#        if y > 0:
#            y *= 1 + d / 1.5 * x * x
#
#        return x, y
#    return projection
#
#
#def bertin(rotation):
#    return projection(bertin_raw, rotation)

def hammer(rotation, w=1):

    scale = math.sqrt(2) + 4e-3

    def projection(longitude, latitude):

        # Convert to radians.
        longitude = math.radians(longitude)
        latitude = math.radians(latitude)
        longitude_rotation = math.radians(rotation[0])
        latitude_rotation = math.radians(rotation[1])

        # Save multiple calculations.
        cos_latitude = math.cos(latitude)
        cos_latitude_rotation = math.cos(latitude_rotation)
        sin_latitude_rotation = math.sin(latitude_rotation)

        # Rotate.
        longitude += longitude_rotation
        x = math.cos(longitude) * cos_latitude
        y = math.sin(longitude) * cos_latitude
        z = math.sin(latitude)
        z0 = z * cos_latitude_rotation + x * sin_latitude_rotation
        longitude = math.atan2(y, x * cos_latitude_rotation - z * sin_latitude_rotation)
        latitude = math.asin(z0)
        if abs(longitude) > math.pi + 1e-12:
            longitude += math.pi
            longitude -= 2 * math.pi * math.floor(longitude / (2 * math.pi))
            longitude -= math.pi

        # Project with Hammer (w, 2).
        cos_latitude = math.cos(latitude)
        d = math.sqrt(2/(1 + cos_latitude * math.cos(longitude / 2)))
        x = w * d * cos_latitude * math.sin(longitude / 2)
        y = d * math.sin(latitude)

        return x/scale, y/scale

    return projection


def briesemeister(rotation=(-10, -45)):
    return hammer(rotation, w=1.75)


def bertin(rotation=(-16.5, -42)):
    # Based on:
    # https://github.com/OSGeo/PROJ/blob/master/src/projections/bertin1953.cpp

    # This scale makes it line up perfectly-ish with the G.Projector graticules.
    # Maybe the extra bit is because of the border?
    scale = math.sqrt(2) + 4e-3
    def projection(longitude, latitude):

        # Bertin constants.
        fu = 1.4
        k = 12
        w = 1.68

        # Convert to radians.
        longitude = math.radians(longitude)
        latitude = math.radians(latitude)
        longitude_rotation = math.radians(rotation[0])
        latitude_rotation = math.radians(rotation[1])

        # Save multiple calculations.
        cos_latitude = math.cos(latitude)
        cos_latitude_rotation = math.cos(latitude_rotation)
        sin_latitude_rotation = math.sin(latitude_rotation)

        # Rotate.
        longitude += longitude_rotation
        x = math.cos(longitude) * cos_latitude
        y = math.sin(longitude) * cos_latitude
        z = math.sin(latitude)
        z0 = z * cos_latitude_rotation + x * sin_latitude_rotation
        longitude = math.atan2(y, x * cos_latitude_rotation - z * sin_latitude_rotation)
        latitude = math.asin(z0)
        if abs(longitude) > math.pi + 1e-12:
            longitude += math.pi
            longitude -= 2 * math.pi * math.floor(longitude / (2 * math.pi))
            longitude -= math.pi

        # Bertin pre-adjustment.
        if longitude + latitude < -fu:
            d = (longitude - latitude + 1.6) * (longitude + latitude + fu) / 8
            longitude += d
            latitude -= 0.8 * d * math.sin(latitude + math.pi / 2)

        # Project with Hammer (1.68, 2).
        cos_latitude = math.cos(latitude)
        d = math.sqrt(2/(1 + cos_latitude * math.cos(longitude / 2)))
        x = w * d * cos_latitude * math.sin(longitude / 2)
        y = d * math.sin(latitude)

        # Bertin post-projection.
        d = (1 - math.cos(longitude * latitude)) / k
        if y < 0:
            x *= 1 + d
        if y > 0:
            y *= 1 + d / 1.5 * x * x

        return x/scale, y/scale

    return projection


def get_projection(name, rotation):
    # There has got to be a better way to get the scale from pyproj.
    if name == 'natural_earth_2':
        return natural_earth_2(rotation)
        #import pyproj
        #transformer = pyproj.Transformer.from_crs('epsg:4326', f'+proj=natearth2 +lon_0={-rotation}')
        #scale = 9083928.757721778
        #def projection(longitude, latitude):
        #    x, y = transformer.transform(latitude, longitude)
        #    return x/scale, y/scale
        #return projection

    if name == 'bertin':
        return bertin(rotation)
        #import pyproj
        #transformer = pyproj.Transformer.from_crs('epsg:4326', '+proj=bertin1953')
        #scale = 9047962.994145015
        #def projection(longitude, latitude):
        #    x, y = transformer.transform(latitude, longitude)
        #    return x/scale, y/scale
        #return projection

    raise Exception('Unrecognized projection')

