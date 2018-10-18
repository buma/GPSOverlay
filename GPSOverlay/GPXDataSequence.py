import os
import datetime
import sys
import collections
import time
import math
import itertools
from operator import itemgetter

#from moviepy.video.VideoClip import VideoClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip, VideoClip

from gpxpy import geo
from .gpxdata import GPXData
from .util import make_func, BreakType, GPSData
from .ImageSequenceClipDelay import ImageSequenceClipDelay

def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    # unique_justseen('AAAABBBCCDAABBB') --> A B C D A B
    # unique_justseen('ABBCcAD', str.lower) --> A B C A D
    return map(next, map(itemgetter(1), itertools.groupby(iterable, key)))

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
    
    max_image_delay
      Maximal delay between images.

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
            interval=0, speedup_factor=24, config=None, max_image_delay=None):

        if fps is not None:
            #It needs to be wanted FPS*image taken interval?
            speedup_factor=fps*3

        clip = ImageSequenceClipDelay(sequence, durations, with_mask, ismask,
                load_images, speedup_factor, max_image_delay=max_image_delay)
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
                    gpx_file=gpx_file,time_offset=time_offset)
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


    def get_index(self, t):
        index = self.find_image_index(t)
        time_start = t*self.speedup_factor

        gps_info, gpx_index = self.gpx_data.get_geo_at(index, time_start)
        return gpx_index

    def make_gpx(self, t, index=None):
        """New way of adding GPX data to images

        Now index is found to see which images are we showing and then time to
        next image and real time difference to next image is found.
        Then ratio of time from current time to first showing of image is
        multiplied with real time to get GPX time between images.

        This is then simplified so that we get ~ 5 different gpx data for 10
        different points in one image

        I'm not sure how that works with breaks

        Also ImageSequenceClipDelay needs to be updates so that max time
        distance between images is 10 or interval between images.


        """
        if index is None:
            index = self.find_image_index(t)
        time_cur = self.images_starts[index]
        try:
            time_next = self.images_starts[index+1]
            dt_diff = self.gpx_data.gpx_data[index+1].datetime-self.gpx_data.gpx_data[index].datetime
        except IndexError as iex:
            print ("Index error make_gpx")
            time_next = time_cur+(time_cur-self.images_starts[index-1])
            dt_diff = self.gpx_data.gpx_data[index].datetime - \
                    self.gpx_data.gpx_data[index-1].datetime

        time_diff = time_next-time_cur
        from_start = t-self.images_starts[index]

        #This reduces number of maps from 1032 to 571 in 45 seconds of video
        #aka 1132 frames
        simplify = lambda x: round(round(x*10)+0.5)/10

        gps_info, gpx_index = self.gpx_data.get_geo_at(index,
                simplify(from_start/time_diff)*dt_diff.seconds,
                from_index=True)
        #print ("FROM_START:{} td:{} dt:{} rat:{} rat1:{} add:{}".format(from_start, time_diff,
            #dt_diff.seconds, from_start/time_diff,
            #simplify(from_start/time_diff),
            #simplify(from_start/time_diff)*dt_diff.seconds))
        return gps_info, gpx_index

    def make_frame(self, t):
        #start = time.time()
        f = self.clip.make_frame(t)
        index = self.find_image_index(t)
        time_start = t*self.speedup_factor
        break_video, end_break_time = self.find_break(index, t,
                self.config.effect_length)
        #kinda hackishly change image at break end so that end picture is shown
        #not picture before the break
        if break_video == BreakType.END:
            f = self.clip.make_frame(self.clip.images_starts[index+1])


        #Prev
        #gps_info, gpx_index = self.gpx_data.get_geo_at(index, time_start)
        gps_info, gpx_index = self.make_gpx(t, index)
        #print ("GPS INFO, index:", gps_info, gpx_index, t, from_start,
                #from_start/time_diff)
        #print ("FROM START",from_start)
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

    def __str__(self):
        ret_string = ["<GPXDataSequence>"]
        if self.gpx_file is not None:
            ret_string.append("gpx_file:{}".format(self.gpx_file))
        ret_string.append("speedup_factor:{}".format(self.speedup_factor))
        ret_string.append("Duration:{}".format(datetime.timedelta(seconds=self.duration)))
        ret_string.append("{}-{}".format(self.gpx_data.gpx_data[0].datetime,self.gpx_data.gpx_data[-1].datetime))
        def get_breaks():
            """Gets type of break for all the times in the clip
            
            Iterator returns time in seconds and break type"""
            for t in range(math.floor(self.duration)):
                index = self.find_image_index(t)
                break_video, _ = self.find_break(index, t,
                    self.config.effect_length)
                yield (t, break_video)

        #Show just brake changes
        just_seen_breaks = unique_justseen(get_breaks(), itemgetter(1))

        #Gets list of break durations and types
        prev_break = None
        for break_ in just_seen_breaks:
            if prev_break is None:
                prev_break = break_
            else:
                diff = break_[0]-prev_break[0]
                ret_string.append("{}s {}".format(datetime.timedelta(seconds=diff), prev_break[1]))
                prev_break = break_

        #If at last time break wasn't changed we also need to return it
        if prev_break[0] != math.floor(self.duration):
            diff = math.floor(self.duration)-prev_break[0]
            ret_string.append("{}s {}".format(datetime.timedelta(seconds=diff), prev_break[1]))

        ret_string.append("</GPXDataSequence>")
        return "\n".join(ret_string)



