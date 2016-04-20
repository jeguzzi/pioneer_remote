#!/usr/bin/env python

import os
import itertools
import pyproj
import requests
import rospy


def get_name(i, j, z):
    return "x{x}_y{y}_z{z}.jpg".format(x=i, y=j, z=z)


def get_path(i, j, z, directory):
    return os.path.join(directory, get_name(i, j, z))


def get_image(i, j, z, url_format):
    url = url_format.format(x=i, y=j, z=z)
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        return None


def tile(x, y, z, mx, Mx, my, My):
    s = 2 ** z
    i = (x - mx) / (Mx - mx) * s
    j = (1 - (y - my) / (My - my)) * s
    return (int(i), int(j))


def get_tiles_in_bb(bb, z):
    p1 = pyproj.Proj(init='epsg:4326')
    p2 = pyproj.Proj(init='epsg:3857')
    mx, my = pyproj.transform(p1, p2, -180, -85.051129)
    Mx, My = pyproj.transform(p1, p2, 180, 85.051129)
    l, L = bb
    x1, y1 = pyproj.transform(p1, p2, *l)
    x2, y2 = pyproj.transform(p1, p2, *L)
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 < y2:
        y1, y2 = y2, y1
    i1, j1 = tile(x1, y1, z, mx, Mx, my, My)
    i2, j2 = tile(x2, y2, z, mx, Mx, my, My)
    return itertools.product(xrange(i1, i2 + 1), xrange(j1, j2 + 1))


def main():
    rospy.init_node('get_map')
    directory = rospy.get_param("~directory")
    # directory = os.getcwd()
    bb = rospy.get_param("~bounding_box")
    z = rospy.get_param("~z")
    url_format = rospy.get_param("~url")
    rospy.loginfo(
        "We are going to save all tile of zoom {z} "
        "that cover the bounding box with vertices"
        "{bb[0]} and {bb[1]} "
        "inside {directory}".format(**locals())
    )
    tiles = get_tiles_in_bb(bb, z)
    for i, j in tiles:
        path = get_path(i, j, z, directory)
        if not os.path.exists(path):
            rospy.loginfo('Fetch tile ({i},{j})'.format(**locals()))
            img = get_image(i, j, z, url_format)
            with open(path, 'w') as f:
                f.write(img)

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
