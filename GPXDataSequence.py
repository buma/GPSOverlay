import os
import datetime
import sys
import collections
import time

GPSData = collections.namedtuple('GPSData', ['lat', 'lon', 'bearing',
'elevation', 'speed', 'heart', 'datetime', 'map', 'slope'])

#from moviepy.video.VideoClip import VideoClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip, VideoClip

from ChartMaker import ChartMaker
from gpxpy import geo
from gpxdata import GPXData
from util import make_func, BreakType
from ImageSequenceClipDelay import ImageSequenceClipDelay

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
            interval=0, speedup_factor=24, data_clips=None, clip_configs=None):

        clip = ImageSequenceClipDelay(sequence, durations, with_mask, ismask,
                load_images, speedup_factor)
        return cls(clip, gpx_file, time_offset, interval,
                speedup_factor, data_clips, clip_configs)

    def __init__(self, clip, gpx_file=None, time_offset=0,
            interval=0, speedup_factor=1, data_clips=None, clip_configs=None):

#How long in seconds is zoom out/in of map in long breaks
        self.effect_length = 3
        self.clip = clip
#Finds breaks in image sequences (Break is when we have GPS information but no
        #images at that time
#FIXME: find breaks with GPS and images not just durations
        if isinstance(clip, ImageSequenceClip):
            self.have_any_breaks = any((duration > (self.effect_length*2+2) for duration in
                self.clip.durations))
            self.gpx_data = GPXData(sequence=self.clip.sequence, gpx_file=gpx_file)
            self.durations = self.clip.durations
            self.images_starts = self.clip.images_starts
            self.find_image_index = lambda t: max([i for i in range(len(self.clip.sequence))
                    if self.clip.images_starts[i]<=t])
        else:
            self.have_any_breaks = False
            self.gpx_data = GPXData(gpx_file=gpx_file)
            self.find_image_index = lambda t: None
        VideoClip.__init__(self, ismask=clip.ismask, duration=clip.duration)

        self.size = clip.size
        self.clip_configs = clip_configs

        #TODO: check if both this exists in clips
        self.fps = clip.fps
        self.maps_cache = "./.map_cacheParenzana"
        self.chart_data = {}
        self.speedup_factor = speedup_factor

        """Clip argument is anything not starting with _
        and not class"""
        def is_argument(argument):
            if argument.startswith("_"):
                return False
            if argument == "class":
                return False
            return True

        if data_clips is not None:
            self.data_pos = {}
            self.data_clips = {}
            #print ("Keys:", data_clips.keys())
# Save in self._data_clips only keys that are in GPSData._fields and have _pos
# Save in self._data_pos only keys with pos that are in GPSData._fields
#FIXME: make map first key so when clip is composed it doesn't overwrite the
            #others
            for key in reversed(GPSData._fields):
                if key in data_clips:
                    keypos = key+"_pos"
                    if keypos in data_clips:
                        self.data_pos[keypos] = data_clips[keypos]
                        self.data_clips[key] = data_clips[key]
                        print ("Added key:", key)
                        if key in clip_configs:
                            clip_config = clip_configs[key]
                            args = {k:v for k,v in clip_config.items() if \
                                   is_argument(k) }
                            if "_gpx_file" in clip_config:
                               if clip_config.get("_gpx_file", False):
                                   args["gpx_file"] = gpx_file
#FIXME: this needs to be map of clips with some kind of API
                            self.mapnik_renderer = clip_config["class"](**args) 
                    else:
                        print(keypos+" is missing in data clips, but "+key+
                                " does exist!")
                    if key in self.chart_clips:
                        key_chart = key+"_chart"
                        if key_chart in data_clips:
                            key_chart_pos = key_chart+"_pos"
                            if key_chart_pos in data_clips:
                                self.data_pos[key_chart_pos] = data_clips[key_chart_pos]
                                self.data_clips[key_chart] = data_clips[key_chart]
                                print ("Added key:", key_chart)
                            else:
                                print (key_chart_pos+" is missing in data clips, but " + key_chart + " does exists!")
            print(self.data_clips)
            #break
                #"Size of input sequence and GPS is not the same")

    #@profile
    def make_frame(self, t):
        start = time.time()
        f = self.clip.make_frame(t)
        index = self.find_image_index(t)
        time_start = t*self.speedup_factor
        break_video, end_break_time = self.find_break(index, t)
        gps_info, gpx_index = self.gpx_data.get_geo_at(index, time_start)
        gps_info = gps_info._asdict()
        #print (gps_info, self.data_clips)
# For each wanted datafield make clip and set position
        for key, clip in self.data_clips.items():
            start_key = time.time()
            if key.endswith("_chart"):
                nkey = key.replace("_chart", "")
                value = gps_info[nkey]
                if nkey not in self.chart_data:
                    self.chart_data[nkey] = ChartMaker(self.gpx_data, nkey,
                            (self.size[0], 100))
                data = self.chart_data[nkey].make_chart_at(gpx_index)
            elif key == 'map':
#makes new image only every 3 indexes
                #k = index//3
                #calc_index = 3*k
                #print ("index, k, calc", index, k, calc_index)
                if break_video != BreakType.NO:
                    #Middle of break. Image always full screen
                    if break_video == BreakType.MIDDLE:
                        width = self.w
                        height = self.h
                    elif break_video == BreakType.START:
#Start of break. Zooms image from original size to full screen
                        xes = (0,self.effect_length)
                        f_width = make_func(xes, (self.clip_configs["map"]["map_w"],
                            self.w))
                        f_height = make_func(xes, (self.clip_configs["map"]["map_h"],
                            self.h))
                    elif break_video == BreakType.END:
#End of a break. Zooms out image from full screen to original size
                        xes = (end_break_time-self.effect_length,end_break_time)
                        f_width = make_func(xes, (self.w,
                            self.clip_configs["map"]["map_w"]))
                        f_height = make_func(xes, (self.h,
                            self.clip_configs["map"]["map_h"]))
                    if break_video == BreakType.START or break_video == \
                        BreakType.END:
                        width = \
                                int(round(f_width(t-self.images_starts[index])))
                        height = \
                                int(round(f_height(t-self.images_starts[index])))
                        #print ("WxH: {}x{}".format(width, height))

                    gpx_name = self.make_name(gps_info, width=width,
                            height=height)
                    data = self._get_map_image(gpx_name, gps_info['lat'],
                            gps_info['lon'], gps_info['bearing'],
                            width=width, height=height)
                else:
                    gpx_name = self.make_name(gps_info)
                    data = self._get_map_image(gpx_name, gps_info['lat'],
                            gps_info['lon'], gps_info['bearing'])
            else:
                data = gps_info[key]

            if data is None:
                continue
            created_clip = clip(data)
            if created_clip is None:
                continue
            if break_video == BreakType.MIDDLE and key == "map":
                c = created_clip
                c.set_pos(0,0)
            elif key == "map" and break_video == BreakType.START:
                c = self.data_pos[key+"_pos"](created_clip,
                        self.w, self.h)
                x_y_start = c.pos(t)
                #print ("Coords:", x_y_start)
#Start of break. Moves map from original position to top left
                xes = (0,self.effect_length)
                f_x = make_func(xes, (x_y_start[0], 0))
                f_y = make_func(xes, (x_y_start[1], 0))
                #print ("Should have pos:", (f_x(t-c.start), f_y(t-c.start)))
                c = c.set_pos(lambda z: (f_x(z), f_y(z)))
            elif key == "map" and break_video == BreakType.END:
                #End of a break. Moves map from top left to original
                #position
                c = self.data_pos[key+"_pos"](created_clip,
                        self.w, self.h)
                x_y_end = c.pos(t)
                #print ("Coords:", x_y_end)
                xes = (end_break_time-self.effect_length,end_break_time)
                #print ("Xes:", xes)
                f_x = make_func(xes, (0, x_y_end[0]))
                f_y = make_func(xes, (0, x_y_end[1]))
                #print ("Should have pos:", (f_x(t-c.start), f_y(t-c.start)))
                #print ("Left size:", (self.w-f_x(t-c.start), self.h-f_y(t-c.start)))
                c = c.set_pos(lambda z: (f_x(z), f_y(z)))
            else:
                c = self.data_pos[key+"_pos"](created_clip,
                        self.w, self.h)
            #if key == "map":
                #print (c.pos(t))
                #c.set_pos(lambda z: print("time:", z))
                #print ("Blit on:", t-c.start, c.end)
            #Replacing f with c if the sizes are the same doesn't speed up
            #the code
            print ("key %s %s, Rendering took %r s" % (key,
                break_video.name, time.time()-start_key,))
            f = c.blit_on(f, t)
        print ("%f, %s, Rendering took %r s" % (t, break_video.name, time.time()-start,))
        return f


    def find_break(self, index,  t):
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
                    next_image_start, self.effect_length,
                    self.speedup_factor)
            if is_break:
                is_start_break = t-self.images_starts[index] <= self.effect_length
                is_end_break = self.images_starts[index+1]-t <= self.effect_length
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

    @staticmethod
    def make_name(gps_info, width=None, height=None):
        lat = round(gps_info['lat']*10**5)
        lon = round(gps_info['lon']*10**5)
        latlon= "{}_{}".format(lat, lon)
        if width and height:
            return latlon + "_{}_{}".format(width,height)
        else:
            return latlon


    """ 
    Gets map clip. If it already exists it's just read, otherwise it's created
    """
    def _get_map_image(self, index, center_lat, center_lon, bearing,
            width=None, height=None):
        mapname = os.path.join(self.maps_cache, "{}.png".format(index))
        #print ("Map image: ", mapname)
        #print ("Render map")
        #start = time.process_time()
        self.mapnik_renderer.render_map(center_lat, center_lon, bearing,
                mapname, img_width=width, img_height=height)
        #print ("Rendering took %r s" % (time.process_time()-start,))

        return ImageClip(mapname)
