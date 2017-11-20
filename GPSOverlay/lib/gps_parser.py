#!/usr/bin/python

#From https://github.com/mapillary/mapillary_tools
#Commit aa122c9671ab26f1fc9026267e069a1a5234dd67

#print is a function now
from __future__ import print_function

import sys
import os
import datetime
import time
from .geo import gpgga_to_dms, utc_to_localtime

try:
    import gpxpy
    import pynmea2
except ImportError as error:
    print (error)

'''
Methods for parsing gps data from various file format e.g. GPX, NMEA, SRT.
'''

#Function now returns also speed and heart rate
def get_lat_lon_time_from_gpx(gpx_file, local_time=True):
    '''
    Read location and time stamps from a track in a GPX file.

    Returns a list of tuples (time, lat, lon, elevation, speed, hr).

    GPX stores time in UTC, by default we assume your camera used the local time
    and convert accordingly.
    So times are in local time converted from UTC based on current date
    difference. Times can be wrong if DST happened between recording of track
    and now.
    '''
    with open(gpx_file, 'r') as f:
        gpx = gpxpy.parse(f, None, '1.1')

    points = []
    prev_point = None
    if len(gpx.tracks)>0:
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    t = utc_to_localtime(point.time) if local_time else point.time
                    speed = 0
                    hr = 0
                    try:
                        hr = int(point.extensions['hr'])
                    except KeyError as k:
                        pass
                    if prev_point is not None:
                        speed = prev_point.speed_between(point)
                    points.append( (t, point.latitude, point.longitude,
                        point.elevation, speed, hr) )
                    prev_point = point
    if len(gpx.waypoints) > 0:
        for point in gpx.waypoints:
            t = utc_to_localtime(point.time) if local_time else point.time
            points.append( (t, point.latitude, point.longitude,
                point.elevation, 0, 0) )

    # sort by time just in case
    points.sort()

    return points


def get_lat_lon_time_from_nmea(nmea_file, local_time=True):
    '''
    Read location and time stamps from a track in a NMEA file.

    Returns a list of tuples (time, lat, lon).

    GPX stores time in UTC, by default we assume your camera used the local time
    and convert accordingly.
    '''
    with open(nmea_file, "r") as f:
        lines = f.readlines()
        lines = [l.rstrip("\n\r") for l in lines]

    # Get initial date
    for l in lines:
        if "GPRMC" in l:
            data = pynmea2.parse(l)
            date = data.datetime.date()
            break

    # Parse GPS trace
    points = []
    for l in lines:
        if "GPRMC" in l:
            data = pynmea2.parse(l)
            date = data.datetime.date()

        if "$GPGGA" in l:
            data = pynmea2.parse(l)
            timestamp = datetime.datetime.combine(date, data.timestamp)
            lat, lon, alt = data.latitude, data.longitude, data.altitude
            points.append((timestamp, lat, lon, alt))

    points.sort()
    return points
