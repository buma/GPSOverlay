from enum import Enum
import collections
import string

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

def find_font(fontconfig):
    """Finds font with font config pattern:

    It only works if matplotlib is installed. Otherwise it returns None

    Fontconfig pattern looks like that:
    <families>-<point sizes>:<name1>=<values1>:<name2>=<values2>
    For example:
        Roboto:medium:italic

    Familiy: Roboto, Weight medium style italic
    Returns path to ttf file or None if not found

    """
    try:
        import matplotlib.font_manager
        font = matplotlib.font_manager.FontProperties(fontconfig)
        return matplotlib.font_manager.findfont(font)
    except Exception as e:
        pass
    return None


class BreakType(Enum):
    NO = 0
    START = 1
    MIDDLE = 2
    END = 3

def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.

    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_') # I don't like spaces in filenames.
    return filename
