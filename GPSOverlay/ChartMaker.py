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
        self.width, self.height = figure_size
        self.opacity = opacity
        self.transparent = transparent
        #elevations = [getattr(gps_point, wanted_value) for gps_point in gpx_data]
        idx = gpx_data.index_for[wanted_value]
        elevations = [point[idx] for point in gpx_data.gpx]
        self.fig, ax = plt.subplots()
        plt.axis("off")
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0,
        hspace = 0, wspace = 0)
        plt.margins(0, 0)
        ax.fill_between(range(0,len(elevations)), 0, elevations,
                color="#163c6277")
        #dpi = self.fig.get_dpi()
        self.fig.set_size_inches(self.width/dpi, self.height/dpi)
        self.fig.set_dpi(dpi)
        self.p = ax.plot(elevations, '-go', alpha=self.opacity,
                color="#3ca5c5AA")

    def make_chart_at(self, index):
        self.p[0].set_markevery([index])
        png_file = io.BytesIO()
        self.fig.savefig(png_file, transparent=True, bbox_inches="tight",
                pad_inches=0)
        #self.fig.savefig(open("/tmp/png.png", "wb"), transparent=True,
                #dpi='figure', bbox_inches="tight", pad_inches=0)
        #THIS hack is needed to actually remove white space on the left and the
        #bottom
        imreaded = imread(png_file.getvalue()) 
        imreaded = imreaded[:self.height,imreaded.shape[1]-self.width:,:]
        return ImageClip(imreaded,
                transparent=self.transparent)


