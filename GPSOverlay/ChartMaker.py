import io

import numpy as np
import matplotlib.pyplot as plt
from moviepy.video.io.bindings import mplfig_to_npimage
from moviepy.video.VideoClip import ImageClip
from moviepy.video.tools.drawing import blit
from moviepy.editor import vfx
from imageio import imread

from .DefaultConfig import DefaultConfig

class ChartMaker(object):
#TODO: This should actually create VideoClip or DataVideoClip and instead of
#make_chart_at we should use make_frame_at?


    def __init__(self, gpx_data, wanted_value, figure_size, opacity=0.8,
            transparent=True, dpi=96):
        self.circle, self.radius = DefaultConfig._make_circle(6, (255,0,0))
        #self.circle = self.circle.set_opacity(opacity)
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
        self.p = ax.plot(elevations, '-g', alpha=self.opacity,
                color="#3ca5c5AA")

        png_file = io.BytesIO()
        self.fig.savefig(png_file, transparent=True, bbox_inches="tight",
                pad_inches=0)
        #self.fig.savefig(open("/tmp/png.png", "wb"), transparent=True,
                #dpi='figure', bbox_inches="tight", pad_inches=0)
        #THIS hack is needed to actually remove white space on the left and the
        #bottom
        imreaded = imread(png_file.getvalue()) 
        imreaded = imreaded[:self.height,imreaded.shape[1]-self.width:,:]
        self.imread_orig = imreaded
        #Just the mask
        self.im_mask = imreaded[:,:,3]
        #the rest
        imreaded = imreaded[:,:,:3]
        self.im = imreaded
        #Gets pixel coordinates of points
        x,y = self.p[0].get_data()
        xy_pixels = ax.transData.transform(np.vstack([x,y]).T)
        xpix, ypix = xy_pixels.T

        # In matplotlib, 0,0 is the lower left corner, whereas it's usually the upper
        # right for most image software, so we'll flip the y-coords...
        width, height = self.fig.canvas.get_width_height()
        ypix = height - ypix
        self.ypix = ypix
        self.xpix = xpix
        self.ele = elevations

    def make_chart_at(self, index):
        #self.p[0].set_markevery([index])
        xcor = int(self.xpix[index])
        ycor = int(self.ypix[index])+4
        #print (self.ele[index], xcor, ycor)

        #print ("PREV:", self.im_mask[xcor:(self.radius+xcor),
            #ycor:(self.radius+ycor)])

        #print ("CIRCLE:", self.circle.img.shape, "Chart:", self.im.shape)
        #print (self.circle.img[:,:,0])
        #print (self.circle.img[:,:,1])
        #print (self.circle.img[:,:,2])
        #print (self.circle.mask.img)
        #Positions current point where it should be on a graph
        cur_circle = self.circle.set_pos((xcor-self.radius,
            ycor-self.radius))
        #print (self.circle.mask.img)
        #Adds point on chart image
        out = cur_circle.blit_on(self.im,0)
        #print (self.im_mask)
        #This doesn't work for some reason
        #Adds transparency together
        #out_mask = blit(
                #cur_circle.mask.img,
                #self.im_mask,
                #map(int, [xcor-self.radius,
            #ycor-self.radius]),
                #mask=cur_circle.mask.img,
                #ismask=True)

        #print (out.shape)
        #print (out_mask)
        out1 = np.empty_like(self.imread_orig)
        out1[:,:,:3]=out
        out1[:,:,3]= self.im_mask #Here out_mask should be but it doesn't work
        #for some reason
        return ImageClip(out1,
                transparent=self.transparent) #.set_mask(ImageClip(self.im_mask,
                    #transparent=self.transparent, ismask=True))


