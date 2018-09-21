import io
import functools

import svgutils
import cairosvg
from imageio import imread
import numpy as np

from moviepy.video.VideoClip import ImageClip

def surface_to_npim(surface):
    """ Transforms a Cairo surface into a numpy array. """
    im = +np.frombuffer(surface.get_data(), np.uint8)
    H,W = surface.get_height(), surface.get_width()
    im.shape = (H,W, 4) # for RGBA
    return im[:,:,:3]

def svg_to_npim(svg_bytestring, dpi):
    """ Renders a svg bytestring as a RGB image in a numpy array """
    tree = cairosvg.parser.Tree(bytestring=svg_bytestring)
    surf = cairosvg.surface.PNGSurface(tree,None, dpi).cairo
    return surface_to_npim(surf)


class SVGImageClip(ImageClip):

    def __init__(self, img, ismask=False, transparent=True,
            fromalpha=False, duration=None, dpi=96, width=None, height=None):
        self.svg = svgutils.transform.fromfile(img)
        svg_bytestring = self.svg.to_str()
        png_file = io.BytesIO()
        if width is not None and height is not None:
            current_width = float(self.svg.width.replace("px", ""))
            current_height = float(self.svg.height.replace("px", ""))
            scale = max(height/current_height, width/current_width)
            cairosvg.svg2png(bytestring=svg_bytestring,write_to=png_file,
                    parent_width=width, parent_height=height, scale=scale)
        else:
#Converts to png and saves to bytestring
            cairosvg.svg2png(bytestring=svg_bytestring,write_to=png_file)

        #np_img = svg_to_npim(svg_bytestring, dpi)
        np_img = imread(png_file.getvalue())
        ImageClip.__init__(self, np_img, ismask=ismask,
                transparent=transparent,
                fromalpha=fromalpha, duration=duration)
