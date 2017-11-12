import datetime
import os
import collections
from lib.gps_parser import get_lat_lon_time_from_gpx
from lib.geo import interpolate_lat_lon, decimal_to_dms
from gpxpy import geo
import exifread
from lib.exif import EXIF
from util import make_offsets
GPSData = collections.namedtuple('GPSData', ['lat', 'lon', 'bearing',
'elevation', 'speed', 'heart', 'datetime', 'map', 'slope', 'offset'])

class GPXData(object):
    def __init__(self, sequence, gpx_file=None, time_offset=0, interval=0):
        self.gpx_data = []
# Estimate capture time with sub-second precision
        image_creation_times = self._estimate_sub_second_time(sequence, interval)
        if not image_creation_times:
            sys.exit(1)
        # read gpx file to get track locations
        self.gpx = get_lat_lon_time_from_gpx(gpx_file)
        #For each image in sequence based on imagecreation time and gpx file time offset
        # find closest saved track_point in gpx file and interpolate lat,lon, elevation, speed etc
        #So that self.gpx_data has same number of items as input self.sequence
        #And each item is GPSData with information at this point in time as image was creatd
        for filepath, file_creation_time in zip(sequence, image_creation_times):
            if self.gpx_data:
                time_offset = self.gpx_data[-1].offset
            self._add_exif_using_timestamp(filepath, file_creation_time, self.gpx,
                    time_offset, 0)
        self.gpx_start_time = self.gpx_data[0].datetime

        self.index_for = {
                'elevation':3,
                'speed':4,
                'heart':5
                }

    def get_geo_at(self, index, seconds_from_start, return_index=False):
        """Gets geo information based on time from start"""
        #TODO: make it work if offsets differ
        offset_time = self.gpx_data[index].offset
        if offset_time is None:
            offset_time = 0
        offset_bearing = 0
#Offset needs to be substracted that we get same point as it was in image
        t = self.gpx_start_time+datetime.timedelta(seconds=seconds_from_start-offset_time)
        lat, lon, bearing, elevation, speed, heart, idx = \
                interpolate_lat_lon(self.gpx, t)
        #if not return_index:
        corrected_bearing = (bearing + offset_bearing) % 360
#Returned times are not the same as times in Exif pictures they differ by
        #offset time since this is GPX time
        data = GPSData(lat, lon, corrected_bearing, elevation,
            speed, heart, t, None, None, offset_time), idx
        return data
        #else:
            #return idx


    def _get_geo_from_exif(self, filename):
        try:
            exif = EXIF(filename)
            geo_data = exif.extract_geo()
            if self.gpx_data:
                offset_time = self.gpx_data[-1].offset
            else:
                offset_time = 0
            t = exif.extract_capture_time() - \
                datetime.timedelta(seconds=offset_time)
            lat = geo_data["latitude"]
            lon = geo_data["longitude"]
            elevation = geo_data["altitude"]
            bearing = exif.extract_direction()
            speed = None
            slope = None
            if self.gpx_data:
                last = self.gpx_data[-1]
                seconds = (t-last.datetime).total_seconds()
                length = geo.distance(last.lat, last.lon, last.elevation, lat,
                        lon, elevation)
                speed = length / float(seconds)
                slope = round((elevation-last.elevation)/length*100)
            return GPSData(lat, lon, bearing, elevation, speed, None, None,
                    None, slope, None)
        except ValueError as e:
            print("Skipping {0}: {1}".format(filename, e))



    #Adds lat,lon, bearing, elevation,speed, heart, time to gpx_data list at time when gilename image was created
    #Those information are interpolated from points array and found based on offset_time 
    def _add_exif_using_timestamp(self, filename, file_creation_time, points,
            given_offset_time=0, offset_bearing=0):
        try:
            geo_exif = self._get_geo_from_exif(filename)
            lat_exif = round(geo_exif.lat, 5)
            lon_exif = round(geo_exif.lon, 5)
            found_diff = False
            for offset_time in make_offsets(given_offset_time,50):
                # subtract offset in s beween gpx time and exif time
                t = file_creation_time - datetime.timedelta(seconds=offset_time)
                lat, lon, bearing, elevation, speed, heart, _ = interpolate_lat_lon(points, t)
                lat_round = round(lat, 5)
                lon_round = round(lon, 5)
                if lat_round-lat_exif == 0 and lon_round-lon_exif == 0:
                    found_diff = True
                    break
            if not found_diff:
                print ("No offset diff found for {}".format(filename))
                offset_time = self.gpx_data[-1].offset
                #return

            corrected_bearing = (geo_exif.bearing + offset_bearing) % 360
            self.gpx_data.append(GPSData(geo_exif.lat, geo_exif.lon,
                corrected_bearing, geo_exif.elevation,
                speed, heart, t, os.path.basename(filename), geo_exif.slope, offset_time))
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
            img = open(filename, 'rb')
            tags = exifread.process_file(img, details=False,
                    stop_tag="EXIF DateTimeOriginal")
            dt_str = tags["EXIF DateTimeOriginal"]
            #print (dt_str)
            dt = datetime.datetime.strptime(str(dt_str), "%Y:%m:%d %H:%M:%S")
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
