import os
import datetime
import sys
import collections

GPSData = collections.namedtuple('GPSData', ['lat', 'lon', 'bearing',
'elevation', 'speed', 'heart', 'datetime', 'map'])

#from moviepy.video.VideoClip import VideoClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.VideoClip import ImageClip

from PIL import Image
import PIL.ExifTags


from lib.geo import interpolate_lat_lon, decimal_to_dms
from lib.gps_parser import get_lat_lon_time_from_gpx
from MapnikRenderer import MapnikRenderer

class GPXDataSequence(ImageSequenceClip):
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


    map_w
      width of map image

    map_h
      height of map image

    zoom
      zoom of map

    map_mapfile
      path to mapnik XML style

    Notes
    ------

    If your sequence is made of image files, the only image kept in 
    
    """

    def __init__(self, sequence, fps=None, durations=None, with_mask=True,
            ismask=False, load_images=False, gpx_file=None, time_offset=0,
            interval=0, data_clips=None, map_w=200, map_h=200, zoom=18,
            map_mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto.xml"):

        if (fps is None) and (durations is None):
            raise ValueError("Please provide either 'fps' or 'durations'.")

        #ImageSequenceClip.__init__(self,sequence, fps, durations, with_mask,
                #ismask, load_images)
        super(GPXDataSequence, self).__init__(sequence, fps, durations, with_mask,
                ismask, load_images)
        # Estimate capture time with sub-second precision
        image_creation_times = self._estimate_sub_second_time(sequence, interval)
        if not image_creation_times:
            sys.exit(1)
        # read gpx file to get track locations
        gpx = get_lat_lon_time_from_gpx(gpx_file)
        self.gpx_data = []
        self.map_zoom = zoom
        self.maps_cache = "./.map_cache6"
        self.mapnik_renderer = MapnikRenderer(map_w, map_h, gpx_file,
                map_mapfile)

        if data_clips is not None:
            self.data_pos = {}
            self.data_clips = {}
            #print ("Keys:", data_clips.keys())
# Save in self._data_clips only keys that are in GPSData._fields and have _pos
# Save in self._data_pos only keys with pos that are in GPSData._fields
            for key in GPSData._fields:
                if key in data_clips:
                    keypos = key+"_pos"
                    if keypos in data_clips:
                        self.data_pos[keypos] = data_clips[keypos]
                        self.data_clips[key] = data_clips[key]
                        print ("Added key:", key)
                    else:
                        print(keypos+" is missing in data clips, but "+key+
                                " does exist!")
            print(self.data_clips)

	#For each image in sequence based on imagecreation time and gpx file time offset
	# find closest saved track_point in gpx file and interpolate lat,lon, elevation, speed etc
	#So that self.gpx_data has same number of items as input self.sequence
	#And each item is GPSData with information at this point in time as image was creatd
        for filepath, file_creation_time in zip(sequence, image_creation_times):
            self._add_exif_using_timestamp(filepath, file_creation_time, gpx,
                    time_offset, 0)
            #break
        assert (len(self.sequence)==len(self.gpx_data)) 
                #"Size of input sequence and GPS is not the same")


        def make_frame(t):
            f = self.orig_make_frame(t)
            def find_image_index(t):
                return max([i for i in range(len(self.sequence))
                    if self.images_starts[i]<=t])
            index = find_image_index(t)
            gps_info = self.gpx_data[index]._asdict()
            #print (gps_info, self.data_clips)
# For each wanted datafield make clip and set position
            for key, clip in self.data_clips.items():
                #print (key, gps_info[key])

                data = gps_info[key]
                if key == 'map':
#makes new image only every 3 indexes
                    #k = index//3
                    #calc_index = 3*k
                    #print ("index, k, calc", index, k, calc_index)
                    data = self._get_map_image(index, gps_info['lat'],
                            gps_info['lon'], gps_info['bearing'])
                
                created_clip = clip(data)
                if created_clip is None:
                    continue
                c = self.data_pos[key+"_pos"](created_clip,
                        self.w, self.h)
                f = c.blit_on(f, t)
            return f

        self.orig_make_frame = self.make_frame
        self.make_frame = make_frame

    """ 
    Gets map clip. If it already exists it's just read, otherwise it's created
    """
    def _get_map_image(self, index, center_lat, center_lon, bearing):
        mapname = os.path.join(self.maps_cache, "{}.png".format(index))
        #print ("Map image: ", mapname)
        #print ("Render map")
        #start = time.process_time()
        self.mapnik_renderer.render_map(center_lat, center_lon, bearing,
                mapname, self.map_zoom)
        #print ("Rendering took %r s" % (time.process_time()-start,))

        return ImageClip(mapname)


    #Adds lat,lon, bearing, elevation,speed, heart, time to gpx_data list at time when gilename image was created
    #Those information are interpolated from points array and found based on offset_time 
    def _add_exif_using_timestamp(self, filename, file_creation_time, points, offset_time=0, offset_bearing=0):
        # subtract offset in s beween gpx time and exif time
        t = file_creation_time - datetime.timedelta(seconds=offset_time)
        try:
            lat, lon, bearing, elevation, speed, heart = interpolate_lat_lon(points, t)
            corrected_bearing = (bearing + offset_bearing) % 360
            self.gpx_data.append(GPSData(lat, lon, corrected_bearing, elevation,
                speed, heart, t, None))
        except ValueError as e:
            print("Skipping {0}: {1}".format(filename, e))

    def _estimate_sub_second_time(self, files, interval):
        '''
        Estimate the capture time of a sequence with sub-second precision

        EXIF times are only given up to a second of precission. This function
        uses the given interval between shots to Estimate the time inside that
        second that each picture was taken.

	If interval is 0 it just returns list of datetimes which are
	 DateTimeOriginal from EXIF of given files
        '''
        def exif_time(filename):
            img = Image.open(filename, "r")
            exif = {
                    PIL.ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in PIL.ExifTags.TAGS
                    }
            dt_str = exif["DateTimeOriginal"]
            dt = datetime.datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
            return dt

        if interval <= 0.0:
            return [exif_time(f) for f in files]

        onesecond = datetime.timedelta(seconds=1.0)
        T = datetime.timedelta(seconds=interval)
        for i, f in enumerate(files):
            m = exif_time(f)
            if i == 0:
                smin = m
                smax = m + onesecond
            else:
                m0 = m - T * i
                smin = max(smin, m0)
                smax = min(smax, m0 + onesecond)

        if smin > smax:
            print('Interval not compatible with EXIF times')
            return None
        else:
            s = smin + (smax - smin) / 2
            return [s + T * i for i in range(len(files))]
