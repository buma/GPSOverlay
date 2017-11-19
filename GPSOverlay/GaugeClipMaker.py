import io
import functools

import svgutils
import cairosvg
from imageio import imread

from moviepy.video.VideoClip import ImageClip

class GaugeClipMaker(object):
    """

    This makes ImageClip from svg Gauge and value.

    For example if we have svg image of speedometer and value 100km/h
    This will create ImageClip of spedometer showing 100 km/h

    Currently only gauge where cursor has x and y is supported and has empty
    transform SVG attribute.

    Parameters
    ----------
    img
      SVG gauge filename. For now cursor needs to turn around its top left
      corner
    min_value
      Minimal value that can be shown in gauge
    max_value
      Max value that can be shown in gauge
    min_angle
      At which angle of rotation of cursor is min value shown
    max_angle
      At which angle of rotation of cursor is max value shown
    transparent
      Set this parameter to `True` (default) if you want the alpha layer
      of the picture (if it exists) to be used as a mask.
    cursor_id
      id of cursor element in SVG. Default is "cursor". Element that will rotate based on value. (Use Inkscape to find out)
    """
    def __init__(self, img, min_value, max_value, min_angle, max_angle,
            transparent=True, cursor_id="cursor"):
#Cursor is the thing that moves
        self.svg = svgutils.transform.fromfile(img)
        print ("Search for #{} in {}".format(cursor_id, img))
        self.cursor = self.svg.find_id(cursor_id)
        self.cursor_x = float(self.cursor.root.get("x"))
        self.cursor_y = float(self.cursor.root.get("y"))
        self.map_speed = functools.partial(self.map_range, in_min=min_value,
                in_max=max_value, out_min=min_angle, out_max=max_angle)
        self.transparent = transparent



    def make_clip(self, value, width=None, height=None):
        """ value to show on gauge

        Width and height can also be changed since it's SVG
        """
        #calculates to which angle we need to turn cursor based on speed
        angle = self.map_speed(value)
#Turns the cursor. We need to use this instead of rotate function since we need
        #to forget previous transformations
        self.cursor.root.set("transform", "rotate(%f %f %f)" % (angle,
            self.cursor_x, self.cursor_y))
        svg_bytestring = self.svg.to_str()
        png_file = io.BytesIO()
        if width is not None and height is not None:
            current_width = float(self.svg.width)
            current_height = float(self.svg.height)
            scale = max(height/current_height, width/current_width)
            cairosvg.svg2png(bytestring=svg_bytestring,write_to=png_file,
                    parent_width=width, parent_height=height, scale=scale)
        else:
#Converts to png and saves to bytestring
            cairosvg.svg2png(bytestring=svg_bytestring,write_to=png_file)
#Reads as numpy image
#TODO: does transparency work?
        return ImageClip(imread(png_file.getvalue()), transparent=self.transparent)

    @staticmethod
    def map_range(x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
