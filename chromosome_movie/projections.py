import math

def natural_earth_2(rotation=0):
    def projection(longitude, latitude):
        '''
        Scaled to (0, 90) degrees = (0, 1.0).  I.e. scaled to a map height of one.

        Based on:
        https://github.com/d3/d3-geo-projection/blob/master/src/naturalEarth2.js
        '''

        longitude += rotation
        if longitude < -180:
            longitude += 360
        elif longitude > 180:
            longitude -= 360

        lon = math.radians(longitude)
        lat = math.radians(latitude)

        x = lon * (0.84719 - 0.13063 * lat**2+ lat**12 * (-0.04515 + 0.05494 * lat**2 - 0.02326 * lat**4 + 0.00331 * lat**6)) / 1.424229168755983

        y = lat * (1.01183 + lat**8 * (-0.02625 + 0.01926 * lat**2 - 0.00396 * lat**4)) / 1.424229168755983

        return x, -y
    return projection


def get_projection(name, rotation=0):
    if name == 'natural_earth_2':
        return natural_earth_2(rotation=rotation)

    raise Exception('Unrecognized projection')
