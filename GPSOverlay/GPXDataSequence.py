import os
import datetime
import sys
import collections
import time

#from moviepy.video.VideoClip import VideoClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip, VideoClip

from gpxpy import geo
from .gpxdata import GPXData
from .util import make_func, BreakType, GPSData
from .ImageSequenceClipDelay import ImageSequenceClipDelay

class GPXDataSequence(VideoClip):
    """
    
    A VideoClip made from a series of images.
    
    Parameters
    -----------
    sequence
      Can be one of these:
      - The name of a folder (containing only pictures). The pictures
        will be considered in alphanumerical order.
      - A list of names of image files. In this case you can choose to
        load the pictures in memory pictures 
      - A list of Numpy arrays representing images. In this last case,
        masks are not supported currently.

    fps
      Number of picture frames to read per second. Instead, you can provide
      the duration of each image with durations (see below)

    durations
      List of the duration of each picture.

    with_mask
      Should the alpha layer of PNG images be considered as a mask ?

    ismask
      Will this sequence of pictures be used as an animated mask.

    gpx_file
      - path to GPX filename with route

    time_offset
      - offset in seconds between image times and GPX. (It is assumed that GPX
        is in UTC and images in local time)
        Time offset between GPX and photos. If your camera is ahead by one minute, time_offset is 60

    interval
      Time between shots. Used to set images times with sub-second precission

    data_clips
      Dictionary, where key can be one of ['lat', 'lon', 'bearing',
      'elevation', 'speed', 'heart', 'datetime', 'map'] and value is a function which gets
      wanted value and must output some kind of Clip or None if None clip isn't
      shown
      if key x exists x_pos must also exists which has value function with
      arguments, returned clip from x and width and height for image.
      this is for setting position of clip     
      function for 'map' gets image clip of map as argument and can add
      transparency for it


    Notes
    ------

    If your sequence is made of image files, the only image kept in 
    
    """

    chart_clips = set(["elevation", "speed", "heart"])
    FORMAT="%Y%m%d_%H%M%S.JPG"

    @classmethod
    def from_sequence_with_breaks(cls, sequence, fps=None, durations=None, with_mask=True,
            ismask=False, load_images=False, gpx_file=None, time_offset=0,
            interval=0, speedup_factor=24, config=None):

        clip = ImageSequenceClipDelay(sequence, durations, with_mask, ismask,
                load_images, speedup_factor)
        return cls(clip, gpx_file, time_offset, interval,
                speedup_factor, None, config)

    def __init__(self, clip, gpx_file=None, time_offset=0,
            interval=0, speedup_factor=1, clip_start_time=None, config=None):

        self.clip = clip
        duration = clip.duration
#Finds breaks in image sequences (Break is when we have GPS information but no
        #images at that time
#FIXME: find breaks with GPS and images not just durations
        if isinstance(clip, ImageSequenceClip):
            self.have_any_breaks = any((duration > (config.effect_length*2+2) for duration in
                self.clip.durations))
            self.gpx_data = GPXData(sequence=self.clip.sequence,
                    gpx_file=gpx_file)
            self.durations = self.clip.durations
            self.images_starts = self.clip.images_starts
            self.find_image_index = lambda t: max([i for i in range(len(self.clip.sequence))
                    if self.clip.images_starts[i]<=t])
        else:
            if speedup_factor != 1:
                self.clip.old_make_frame = self.clip.make_frame
                self.clip.make_frame = lambda t: \
                    self.clip.old_make_frame(t*self.speedup_factor)
                duration = duration/speedup_factor
            self.have_any_breaks = False
            self.gpx_data = GPXData(gpx_file=gpx_file,
                    gpx_start_time=clip_start_time,
                    time_offset=time_offset)
            self.find_image_index = lambda t: None
        VideoClip.__init__(self, ismask=clip.ismask,
                duration=duration)

        self.size = clip.size

        #TODO: check if both this exists in clips
        #self.fps = clip.fps
        self.chart_data = {}
        self.speedup_factor = speedup_factor
        self.gpx_file = gpx_file


        if config is not None:
            self.config = config

            for key, key_config in config.config_items(need_config=True):
                print (key, "needs config")
                key_config.init(vars(self))

    def make_frame(self, t):
        #start = time.time()
        f = self.clip.make_frame(t)
        index = self.find_image_index(t)
        time_start = t*self.speedup_factor
        break_video, end_break_time = self.find_break(index, t,
                self.config.effect_length)
        gps_info, gpx_index = self.gpx_data.get_geo_at(index, time_start)
        gps_info = gps_info._asdict()
        #print (gps_info, self.data_clips)
# For each wanted datafield make clip and set position
        for key, key_config in self.config.make_items():
            c = key_config.get_clip(key, gps_info, gpx_index, self.w,
                    self.h, break_video, end_break_time,
                    t-self.images_starts[index])
            if c is None:
                continue
            #print (key, "==", c.pos(t), c.w, c.h)
            #c.show(t, interactive=True)
            #print ("key %s %s, Rendering took %r s" % (key,
                #break_video.name, time.time()-start_key,))
            f = c.blit_on(f, t)
        #print ("%f, %s, Rendering took %r s" % (t, break_video.name, time.time()-start,))
        return f

    def find_break(self, index,  t, effect_length):
        """Checks if current image is in a break

        and which part of a break. Start, Middle or End
        """
        break_video = BreakType.NO
        if not self.have_any_breaks:
            return break_video, None
        if len(self.images_starts) > (index+1):
            next_image_start = self.images_starts[index+1]*self.speedup_factor
            is_break = self.gpx_data.is_break(index,
                self.images_starts[index]*self.speedup_factor,
                    next_image_start, effect_length,
                    self.speedup_factor)
            if is_break:
                is_start_break = t-self.images_starts[index] <= effect_length
                is_end_break = self.images_starts[index+1]-t <= effect_length
                if is_start_break:
                    #print ("BREAK: Start break")
                    break_video = BreakType.START
                elif is_end_break:
                    #print ("BREAK: end break")
                    break_video = BreakType.END
                else:
                    #print ("BREAK: middle break")
                    break_video = BreakType.MIDDLE
            #print (t, "idx", index,"duration", self.durations[index]*self.speedup_factor,
                    #self.images_starts[index+1]*self.speedup_factor-t,
                    #self.images_starts[index+1]*self.speedup_factor,
                    #self.images_starts[index]*self.speedup_factor,
                    #t-self.images_starts[index],
                    #self.images_starts[index+1]-t)
        return break_video, self.durations[index]



