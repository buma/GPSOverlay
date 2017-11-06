import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import ImageClip
from moviepy.editor import vfx

class ChartMaker(object):
#TODO: This should actually create VideoClip or DataVideoClip and instead of
#make_chart_at we should use make_frame_at?

    def __init__(self, gpx_data, wanted_value, figure_size, opacity=0.8, dpi=96):
        width, height = figure_size
        elevations = [getattr(gps_point, wanted_value) for gps_point in gpx_data]
        self.fig, ax = plt.subplots()
        self.fig.set_size_inches(width/dpi, height/dpi)
        self.fig.set_dpi(dpi)
        self.opacity = opacity
        self.p = ax.plot(elevations, '-go', alpha=self.opacity)
        plt.axis("off")

    def make_chart_at(self, index):
        self.p[0].set_markevery([index])
        numpy_ar = mplfig_to_npimage(self.fig)
        #Makes white color transparent
        #FIXME: it looks very bad
        return ImageClip(numpy_ar).fx(vfx.mask_color, [255,255,255]) \
                .set_opacity(self.opacity)

