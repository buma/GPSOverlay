import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import ImageClip

class ChartMaker(object):
#TODO: This should actually create VideoClip or DataVideoClip and instead of
#make_chart_at we should use make_frame_at?

    def __init__(self, gpx_data, wanted_value, figure_size, dpi=96):
        #TODO: transparency
        width, height = figure_size
        elevations = [getattr(gps_point, wanted_value) for gps_point in gpx_data]
        self.fig, ax = plt.subplots()
        self.fig.set_size_inches(width/dpi, height/dpi)
        self.fig.set_dpi(dpi)
        self.p = ax.plot(elevations, '-go')
        plt.axis("off")

    def make_chart_at(self, index):
        self.p[0].set_markevery([index])
        return ImageClip(mplfig_to_npimage(self.fig))

