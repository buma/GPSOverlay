from enum import Enum
import collections

from moviepy.video.VideoClip import TextClip

GPSData = collections.namedtuple('GPSData', ['lat', 'lon', 'bearing',
'elevation', 'speed', 'heart', 'datetime', 'map', 'slope', 'offset'])

def write_run(seq_name, file_name):
    mf = "\nmplayer mf://{} -mf fps=8 -vo xv\n"
    with open(file_name, "wt") as out_seq_file:
        out_seq_file.write("#!/bin/sh\n")
        out_seq_file.write(mf.format(seq_name))

def make_offsets(time_offset, max_diff=5):
    for x in range(max_diff+1):
        if x == 0:
            yield time_offset
        else:
            yield time_offset+x
            yield time_offset-x

def make_func(x_values, y_values):
    """Makes linear interpolating function

    that interpolates from given x_values to y_values
    from x values to y values"""
    x0, x1 = x_values
    y0, y1 = y_values
    k=(y1-y0)/(x1-x0)
    n=y1-k*x1
    return lambda x: k*x+n

class BreakType(Enum):
    NO = 0
    START = 1
    MIDDLE = 2
    END = 3

def make_speed_clip(speed):
    large_font=40
    font="Bitstream-Vera-Sans-Mono-Bold"
    if speed*3.6 < 1:
        txt = "STOPPED"
    else:
        txt = "%2.2f km/h" % (speed*3.6)
    return TextClip(txt,
        fontsize=large_font, font=font, color='white',
        stroke_color='black')
