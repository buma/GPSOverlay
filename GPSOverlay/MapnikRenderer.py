import time
import os
import multiprocessing
from io import BytesIO

from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from .util import format_filename
from .DefaultConfig import DefaultConfig
from PIL import Image as ImagePIL
import numpy as np
try:
    import mapnik2 as mapnik
except:
    import mapnik


circle, radius = DefaultConfig._make_circle(8, (0,255,0))
def make_gpx_track_view(width, height, gpx_file=None, gpx_style=None, mapfile=None, 
        maps_cache=None, font_path=None, layer_padding=10, lat=45, lon=15,
        render_point=False):
    #TODO at given point location render something to show start
    map_renderer = MapnikRenderer(map_w=width, map_h=height, gpx_file=gpx_file,
            gpx_style=gpx_style, mapfile=mapfile, maps_cache=maps_cache,
            font_path=font_path)
    map_clip, center_coordinate = map_renderer.render_map(lat, lon, zoom_to_layer=True,
            layer_padding=layer_padding)
    if render_point:
        #We composite it on map image to get current location point
        map_w = map_clip.w
        map_h = map_clip.h
        circle_clip = circle
        circle_clip = circle_clip.set_pos((center_coordinate[0]-radius,
            center_coordinate[1]-radius))
#We get circle on transparent background
        both = CompositeVideoClip([map_clip, circle_clip])
        return both
    else:
        return map_clip

def make_map_view(width, height, gpx_file=None, gpx_style=None, mapfile=None, 
        maps_cache=None, font_path=None, layer_padding=10, lat=45, lon=15,
        render_point=False, map_zoom=18):
    #TODO at given point location render something to show start
    map_renderer = MapnikRenderer(map_w=width, map_h=height, gpx_file=gpx_file,
            gpx_style=gpx_style, mapfile=mapfile, maps_cache=maps_cache,
            font_path=font_path)
    map_clip, center_coordinate = map_renderer.render_map(lat, lon,
            zoom_to_layer=False,
            zoom=map_zoom,
            layer_padding=layer_padding)
    if render_point:
        #We composite it on map image to get current location point
        map_w = map_clip.w
        map_h = map_clip.h
        circle_clip = circle
        circle_clip = circle_clip.set_pos((center_coordinate[0]-radius,
            center_coordinate[1]-radius))
#We get circle on transparent background
        both = CompositeVideoClip([map_clip, circle_clip])
        return both
    else:
        return map_clip


#https://github.com/kevinstadler/southup

#Based on: https://gist.github.com/andrewharvey/1290744

# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
#merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

#South up
#merc = mapnik.Projection('+proj=tpeqd +lat_1=35 +lat_2=35 +lon_1=-80 +lon_2=-122  +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')

class MapnikRenderer(object):
    """Renders map with help of Mapnik

    And returns ImageClips

    Note
    ----
    If Mapnik XML style file uses relative paths to its datasources it can't be
    moved to different folder.


    Parameters
    ---------
    map_w : int
        Wanted map width
    map_h : int
        Wanted map height
    gpx_file : filepath
        GPX filepath to show on map (gpx_style also needs to be set if this is
        set)
    gpx_style : str
        Name of mapnik style layer that should be used to style GPX track
        layer. It needs to already exists in Mapnik style file!.
    map_zoom : float
        Mapnik zoom from 0-19 (higher number higher zoom) 
    mapfile : str
        Full path to mapnik XML style file. If it is None empty transparent map is
        rendered. If gpx_file is set then only the GPX track is rendered.
    maps_cache : str
        Path to where should we cache generated maps so that they are generated
        only once. Or None if no cache should be used
    """
# long/lat in degrees, aka ESPG:4326 and "WGS 84"
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    """mapnik.Projection: In what coordinate system are input coordinates.
     AKA EPSG:4326

    Project input latitude and latitude to spherical mercator
    """
    # spherical mercator (most common target map projection of osm data imported with osm2pgsql)
    mercator_projection = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')

    def __init__(self, map_w, map_h,
            gpx_file=None,
            gpx_style=None,
            map_zoom=18,
            mapfile=None,
            maps_cache=None, no_lazy_load=False,
            font_path=None):

        if font_path is not None:
            mapnik.register_fonts(font_path)


        self.m = None
        self.mapfile = mapfile
        self.gpx_style = gpx_style
        self.gpx_file = gpx_file
        self.map_width = map_w
        self.map_height = map_h
        if map_zoom is None:
            self.zoom_changeable = True
        else:
            self.zoom_changeable = False
        self.map_zoom = map_zoom
        self.maps_cache=maps_cache
        self.mapnik_style_file = mapfile

        if self.maps_cache is not None:
            self._save_cache()

        else:
            self._lazy_init_map()

        if no_lazy_load:
            self._lazy_init_map()

    def _lazy_init_map(self):
        if self.m is None:
            #start = time.perf_counter()
            self.m = mapnik.Map(self.map_width, self.map_height)
            #print ("Mapnik took %r s" % (time.perf_counter()-start,))
            #start = time.perf_counter()
            if self.mapfile is None:
                self.m.background = mapnik.Color('rgb(0,0,0,0)') #transparent
            else:
                mapnik.load_map(self.m, self.mapfile)
            #print ("loadint took %r s" % (time.perf_counter()-start,))
# Create a symbolizer to draw the points
            #if "openstreetmap-carto" in mapfile:


            self.draw_gpx_track(self.gpx_file, self.gpx_style)

    def _save_cache(self):
        """Saved options for map generation to cache


        All settings are saved in config.json in maps_cache folder.

        If config.json already exists in cache folder it is compared with
        current settings. If it is not the same Exception is raised
        """
        import json
        import os.path

        current_cache = {k:v for k,v in vars(self).items() if k != 'm'}
        cache_fn = os.path.join(self.maps_cache, "config.json")

        if os.path.isfile(cache_fn):
            with open(cache_fn, "r") as f:
                saved_cache = json.load(f)
                if current_cache != saved_cache:
                    raise Exception("Saved map_cache != current mapnik " +
                            "config. Change maps_cache or delete previous "+
                            " cache file.{} Current:{}".format(saved_cache,
                                current_cache))

        with open(cache_fn, "w") as f:
            json.dump(current_cache, f)

    def add_gpx_style(self, gpx_style):
        """Adds mapnik style for styling GPX track

        This is blue 40% transparent 4 width line.

        Parameters
        ---------
        gpx_style : str
            Name of the style layer


        Note
        ----
        This doesn't work for some reason. Style is added and if mapnik XML is
        saved and read it is used.
        """
        self._lazy_init_map()
        style = mapnik.Style()
        style.filter_mode=mapnik.filter_mode.FIRST
        rule = mapnik.Rule()
        line_symbolizer = mapnik.LineSymbolizer()
        line_symbolizer.stroke = mapnik.Color('rgb(0%,0%,100%)')
        line_symbolizer.stroke_width = 4
        line_symbolizer.stroke_opacity= 0.4
        #line_symbolizer.simplify = 0.1

        rule.symbols.append(line_symbolizer)
        style.rules.append(rule)
        self.m.append_style(gpx_style, style)
        print ("Making style")

    def draw_gpx_track(self, gpx_file, gpx_style):
        """Adds layer which draws GPX Track

        Tracks layer from GPX file is drawn

        Notes
        ----
        Since adding gpx_style to Mapnik XML doesn't work for some reason.
        Style for styling lines needs to already exists in Mapnik XML

        Parameters
        ---------
        gpx_file : str
            Full path to gpx file
        gpx_style : str
            Name of style layer for gpx file

        """
        if gpx_file is not None and gpx_style is not None:
# Create a layer to hold GPX points
            print ("Adding GPX file")
            layer = mapnik.Layer("gpx")
            layer.datasource = mapnik.Ogr(file=gpx_file,
                    layer='tracks')
            layer.styles.append(gpx_style)
            self.m.layers.append(layer)
            #print (self.m.layers)
            #print ("symbolizer took %r s" % (time.perf_counter()-start,))
            #mapnik.save_map(self.m,
                    #"/home/mabu/Documents/MapBox/project/openstreetmap-carto1/file.xml")
            #mapnik.save_map(self.m, "file.xml")
        #for layer in self.m.layers:
            #print (layer.name)

    def _make_name(self, lat, lon, width=None, height=None, zoom=None,
            zoom_to_layer=False):
        """Generates name based on lat, lon width and height

        Name is lat_lon rounded to 5 decimal places after multipled by 10^5
        So that we have integer. _width_height is added if they are not None

        Parameters
        ---------
        lat : float
            Latitude in WGS84 - center point of a map (around 46 in Europe)
        lon : float
            Longitude in WGS84 - center point of a map (around 15 in Europe)
        width : int
            Wanted width of the map
        height : int
            Wanted height of the map
        zoom : float
            map zoom
        zoom_to_layer : bool
            If true map shows whole layer and lat,lon, zoom are actually
            ignored


        Returns
        ------
        str
            Filename

        """
        if zoom_to_layer:
            name = "LAYER_"+format_filename(self.gpx_file[-20:])
            return name
        round_lat = round(lat*10**5)
        round_lon = round(lon*10**5)
        latlon= "{}_{}".format(round_lat, round_lon)
        if width and height:
            name = latlon + "_{}_{}".format(width,height)
        else:
            name = latlon
        if zoom:
            round_zoom = int(round(zoom*10**5))
            name += "_Z{}".format(round_zoom)
        return name

    def render_map(self, lat, lon, angle=None, angle_offset=0, zoom=None,
            overwrite=False, img_width=None, img_height=None,
            zoom_to_layer=False, layer_padding=10):
        """Renders map with help of mapnik

        If maps_cache is used it is first checked if image already exists in
        cache. Image name is created with self._make_name which creates name
        from lat_lon rounded to 5 decimals and width height if they are
        provided. If image exists and overwrite is False image is returned as
        ImageClip. If overwrite is True image is deleted and image is rendered
        and also returned as ImageClip.

        Parameters
        ---------
        lat : float
            Latitude in WGS84 - center point of a map (around 46 in Europe)
        lon : float
            Longitude in WGS84 - center point of a map (around 15 in Europe)
        angle : float
            If we want to rotate map. It should show where up is. AKA bearing
        angle_offset : int
            How much offset is between camera and forward direction so that
            map is correctly oriented
        zoom : float
            Mapnik zoom from 0-19 (higher number higher zoom) If we want
            different zoom then what was set in constructor
        overwrite : bool
            If we are using map cache do we want to overwrite existing images
        img_width : int
            If we want different size of map then what was set in constructor
        img_height : int
            If we want different size of map then what was set in constructor
        zoom_to_layer: bool
            If true it shows whole gpx layer in a map. lat, lon, zoom, angle are
            ignored
        layer_padding: int
            How much padding to add between edges of layer and image

        Returns
        -------
        moviepy.video.VideoClip.ImageClip, tuple
            Rendered image as clip, and tuple with x and y coordinate of center
            in pixel units. (Used to add point on current location)


        """
        map_uri = None
        width = self.map_width if img_width is None else img_width
        height = self.map_height if img_height is None else img_height
        if zoom is None:
            if self.map_zoom is None:
                raise Exception("One of map_zoom or zoom needs to be set!")
            zoom = self.map_zoom

        if angle is None:
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
            merc = self.mercator_projection
        else:
#Map rotation https://gis.stackexchange.com/questions/183175/rotating-90-using-two-point-equidistant-projection-with-proj4
            merc = mapnik.Projection('+proj=aeqd +ellps=sphere +lat_0=90 +lon_0=-' +
                    str(angle+angle_offset))
        self._lazy_init_map()
# ensure the target map projection is mercator
        self.m.srs = merc.params()

        centre = mapnik.Coord(lon, lat)  
        transform = mapnik.ProjTransform(MapnikRenderer.longlat, merc)
        merc_centre = transform.forward(centre)


        if img_width is not None and img_height is not None:
            self.m.resize(width, height)

        if not zoom_to_layer:
# 360/(2**zoom) degrees = 256 px
# so in merc 1px = (20037508.34*2) / (256 * 2**zoom)
# hence to find the bounds of our rectangle in projected coordinates + and - half the image width worth of projected coord units
            dx = ((20037508.34*2*(width/2)))/(256*(2 ** (zoom)))
            minx = merc_centre.x - dx
            maxx = merc_centre.x + dx
# grow the height bbox, as we only accurately set the width bbox
            self.m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT
            bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10) # the y bounds will be fixed by mapnik due to ADJUST_BBOX_HEIGHT
        else:
            names = ["gpx"]
            ppmm = 90.7 / 25.4
            self.m.aspect_fix_mode = mapnik.aspect_fix_mode.GROW_BBOX
            #Next for loop is from Zverik/Nik4 app
            #Calculate extent of given layers and bbox
            for layer in (l for l in self.m.layers if l.name in names):
                # it may as well be a GPX layer in WGS84
                proj = mapnik.Projection(layer.srs)
                bbox = layer.envelope() \
                        .inverse(proj).forward(self.mercator_projection)
                tscale = min((bbox.maxx - bbox.minx) / max(width, 0.01),
                             (bbox.maxy - bbox.miny) / max(height, 0.01))
                bbox.pad(layer_padding * ppmm * tscale)
                bounds = bbox



# Note: aspect_fix_mode is only available in Mapnik >= 0.6.0
        self.m.zoom_to_box(bounds)

        center_pixel_coord = self.m.view_transform().forward(merc_centre)
        #print ("img_width: {} map_width:{} width:{}".format(img_width, self.map_width, width))
        if self.maps_cache is not None:
            zoom_name = zoom if self.zoom_changeable else None
            fn = self._make_name(lat, lon, width,
                height, zoom_name, zoom_to_layer)
            #print ("Rendering " + fn)
            map_uri = os.path.join(self.maps_cache, "{}.png".format(fn))
#If we don't want to overwrite and file already exists skip map rendering
            if not overwrite and os.path.isfile(map_uri):
                return ImageClip(map_uri), (center_pixel_coord.x,
                        center_pixel_coord.y)
#If we want to overwrite and file exists we remove file
            if overwrite and os.path.isfile(map_uri):
                os.remove(map_uri)


        #start = time.perf_counter()
        if self.maps_cache is not None:
            mapnik.render_to_file(self.m, map_uri)
            map_data = map_uri
        else:
#Renders map to image in memory saves it to buffer and reads in numpy
            im = mapnik.Image(self.m.width, self.m.height)
            mapnik.render(self.m, im)
            #im.save("/tmp/tmp.png", 'png256')
#Saving image to bytes buffer needs to be nonpalletted image otherwise it needs
            #to be converted to RGB when reading in numpy anyways
            string_image = im.tostring('png32')
            buffer = BytesIO(string_image)
            #with open("/tmp/tmp1.png", "wb") as o:
                #o.write(buffer.getvalue())
            pil_image = ImagePIL.open(buffer)
            #print (pil_image.format, pil_image.mode, pil_image.size,
                    #pil_image.palette)
            map_data = np.asarray(pil_image)
            #map_data = "/tmp/tmp.png"
        if img_width is not None and img_height is not None:
            self.m.resize(self.map_width, self.map_height)

        #print ("render took %r s" % (time.perf_counter()-start,))
        return ImageClip(map_data), (center_pixel_coord.x,
                center_pixel_coord.y)
    if False:
# Print stats
        print("Stats:")
        print("  Mapnik version: " + mapnik.mapnik_version_string())
        print("  Using map file: " + mapfile)
        print("  Using bounds: " + repr(bounds))
        print("  Scale Denominator: " + str(m.scale_denominator()))
        print("  Render into file: " + map_uri)
        print("  Image size: " + str(m.width) + "x" + str(m.height))


class MapnikMultiProcessRenderer(multiprocessing.Process):

    def __init__(self, task_queue, result_queue, map_width, map_height,
            gpx_file=None, zoom=18, maps_cache = "./.map_cache",
            mapfile=None):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.zoom = zoom
        self.maps_cache = maps_cache
        self.renderer = MapnikRenderer(map_width, map_height, gpx_file=gpx_file,
                map_zoom=zoom,
                mapfile=mapfile, maps_cache=maps_cache)
        self.cnt_times = 0
        self.cnt_items = 0

    def run(self):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                #print ('%s Exiting' % (proc_name,))
                if self.cnt_times > 0:
                   self.result_queue.put('%s done %d tasks in %f s %f items per second' %(proc_name, self.cnt_items,
                    self.cnt_times, self.cnt_items/self.cnt_times))
                else:
                   self.result_queue.put('%s done %d tasks in %f s ' %(proc_name, self.cnt_items,
                    self.cnt_times))
                self.task_queue.task_done()
                break
            if isinstance(next_task, int):
                print ('%s done %d tasks in %f s' %(proc_name, self.cnt_items,
                    self.cnt_times))
                self.task_queue.task_done()
                continue
            #print("%s GOT: %s" % (proc_name, next_task,))
            index, center_lat, center_lon, bearing = next_task
            mapname = os.path.join(self.maps_cache, "{}.png".format(index))
            #print ("Map image: ", mapname)
            #print ("Got ", index, center_lat, center_lon, bearing, self.zoom)
            start = time. time()
            self.renderer.render_map(center_lat, center_lon, bearing,
                    mapname, self.zoom)
            self.cnt_times+= time.time()-start
            self.cnt_items+=1

            self.task_queue.task_done()


if __name__ == "__main__":
    lat, lon, angle = (46.55711886333333, 15.62431150777778, 137.31216620286796)
    #render_map(lat, lon, angle, "map_aeqd137_18.png")
    lat, lon, angle = (46.556164420769235, 15.624496195384616, 191.10020115018185)
    #render_map(lat, lon, angle, "map_aeqd1191_18.png")
    #render_map(46.5102,15.6956,None,"testmap.png", zoom=15,map_width=500,map_height=500)
    m = MapnikRenderer(500,500, gpx_file="/data2/snemanje/20171016/data.gpx",
            gpx_style="gpx",
            mapfile="/home/mabu/Documents/MapBox/project/simple-osm/map_transparent.xml")
            #mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/file.xml")
            #mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto_gpx.xml")
    m.render_map(46.556164420769235, 15.624496195384616, 160,
            "./test/testmap_gpx.png", overwrite=True)
