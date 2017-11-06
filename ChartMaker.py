import io

import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import ImageClip
from moviepy.editor import vfx
from imageio import imread

class ChartMaker(object):
#TODO: This should actually create VideoClip or DataVideoClip and instead of
#make_chart_at we should use make_frame_at?

    def __init__(self, gpx_data, wanted_value, figure_size, opacity=0.8,
            transparent=True, dpi=96):
        width, height = figure_size
        self.opacity = opacity
        self.transparent = transparent
        elevations = [getattr(gps_point, wanted_value) for gps_point in gpx_data]
        self.fig, ax = plt.subplots()
        self.fig.set_size_inches(width/dpi, height/dpi)
        self.fig.set_dpi(dpi)
        self.p = ax.plot(elevations, '-go', alpha=self.opacity)
        plt.axis("off")

    def make_chart_at(self, index):
        self.p[0].set_markevery([index])
        png_file = io.BytesIO()
        self.fig.savefig(png_file, transparent=True)
        return ImageClip(imread(png_file.getvalue()),
                transparent=self.transparent)


