import time
import os
import multiprocessing
try:
    import mapnik2 as mapnik
except:
    import mapnik



#https://github.com/kevinstadler/southup

#Based on: https://gist.github.com/andrewharvey/1290744

# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
#merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

#South up
#merc = mapnik.Projection('+proj=tpeqd +lat_1=35 +lat_2=35 +lon_1=-80 +lon_2=-122  +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')


class MapnikRenderer(object):
# long/lat in degrees, aka ESPG:4326 and "WGS 84"
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')

    def __init__(self, imgx, imgy,
            gpx_file=None,
            gpx_style=None,
            mapfile=None):
        #start = time.process_time()
        self.m = mapnik.Map(imgx, imgy)
        #print ("Mapnik took %r s" % (time.process_time()-start,))
        #start = time.process_time()
        if mapfile is None:
            self.m.background = mapnik.Color('rgb(0,0,0,0)') #transparent
        else:
            mapnik.load_map(self.m, mapfile)
        #print ("loadint took %r s" % (time.process_time()-start,))
# Create a symbolizer to draw the points
        #if "openstreetmap-carto" in mapfile:

#Why this doesn't draw gpx line, but if we save xml and draw map with it line
#is drawn
        #style = mapnik.Style()
        #style.filter_mode=mapnik.filter_mode.FIRST
        #rule = mapnik.Rule()
        #line_symbolizer = mapnik.LineSymbolizer()
        #line_symbolizer.stroke = mapnik.Color('rgb(0%,0%,100%)')
        #line_symbolizer.stroke_width = 4
        #line_symbolizer.stroke_opacity= 0.4
        ##line_symbolizer.simplify = 0.1

        #rule.symbols.append(line_symbolizer)
        #style.rules.append(rule)
        #self.m.append_style('gps', style)
        #print ("Making style")


        if gpx_file is not None and gpx_style is not None:
# Create a layer to hold GPX points
            print ("Adding GPX file")
            layer = mapnik.Layer(gpx_style)
            layer.datasource = mapnik.Ogr(file=gpx_file,
                    layer='tracks')
            layer.styles.append(gpx_style)
            self.m.layers.append(layer)
            #print (self.m.layers)
            #print ("symbolizer took %r s" % (time.process_time()-start,))
            #mapnik.save_map(self.m,
                    #"/home/mabu/Documents/MapBox/project/openstreetmap-carto1/file.xml")
            #mapnik.save_map(self.m, "file.xml")
        #for layer in self.m.layers:
            #print (layer.name)

        self.imgx = imgx
        self.imgy = imgy

#y - lat - 46
#x - lon - 15
#angle of map, so that to direction is at the top
    def render_map(self, centrey, centrex, angle, map_uri, zoom=18,
            overwrite=False):

#If we don't want to overwrite and file already exists skip map rendering
        if not overwrite and os.path.isfile(map_uri):
            return
#If we want to overwrite and file exists we remove file
        if overwrite and os.path.isfile(map_uri):
            os.remove(map_uri)

        #self.m.zoom_all()
        #mapnik.render_to_file(self.m, map_uri)
        #return


        if angle is None:
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
            merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
        else:
#Map rotation https://gis.stackexchange.com/questions/183175/rotating-90-using-two-point-equidistant-projection-with-proj4
            merc = mapnik.Projection('+proj=aeqd +ellps=sphere +lat_0=90 +lon_0=-' +
                    str(angle-10))

#Layer with current location:
            if False:

                gs = ('{ "type":"FeatureCollection", "features": [ {' +
                            '"type":"Feature", "properties":{"name":"current"},'+
                                '"geometry": { "type":"Point",' +
                            '"coordinates":[%f, %f]}}]}' %(centrex, centrey))
                ds = mapnik.Datasource(
                        type='geojson',
                        inline=gs
                        )
                #point = None
                for layer in self.m.layers:
                    if layer.name == "current_point":
                        point = layer
                        point.active=False
                        break
                point = mapnik.Layer('current_point')
                point.datasource = ds
                point.styles.append('GPS_tracking_points')
                self.m.layers.append(point)
                #if point is None:
                    #new=True
                    #point = mapnik.Layer('current_point')
                #else:
                    #new = False
                #point.datasource = ds
                #if new:
                    #point.styles.append('GPS_tracking_points')
                    #self.m.layers.append(point)

# ensure the target map projection is mercator
        self.m.srs = merc.params()

        centre = mapnik.Coord(centrex, centrey)  
        transform = mapnik.ProjTransform(MapnikRenderer.longlat, merc)
        merc_centre = transform.forward(centre)

# 360/(2**zoom) degrees = 256 px
# so in merc 1px = (20037508.34*2) / (256 * 2**zoom)
# hence to find the bounds of our rectangle in projected coordinates + and - half the image width worth of projected coord units
        dx = ((20037508.34*2*(self.imgx/2)))/(256*(2 ** (zoom)))
        minx = merc_centre.x - dx
        maxx = merc_centre.x + dx

# grow the height bbox, as we only accurately set the width bbox
        self.m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT

        bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10) # the y bounds will be fixed by mapnik due to ADJUST_BBOX_HEIGHT



# Note: aspect_fix_mode is only available in Mapnik >= 0.6.0
        self.m.zoom_to_box(bounds)


        #start = time.process_time()
        mapnik.render_to_file(self.m, map_uri)
        #print ("render took %r s" % (time.process_time()-start,))
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

    def __init__(self, task_queue, result_queue, imgx, imgy,
            gpx_file=None, zoom=18, maps_cache = "./.map_cache",
            mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto.xml"):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.zoom = zoom
        self.maps_cache = maps_cache
        self.renderer = MapnikRenderer(imgx, imgy, gpx_file, mapfile)
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
    centrey, centrex, angle = (46.55711886333333, 15.62431150777778, 137.31216620286796)
    #render_map(centrey, centrex, angle, "map_aeqd137_18.png")
    centrey, centrex, angle = (46.556164420769235, 15.624496195384616, 191.10020115018185)
    #render_map(centrey, centrex, angle, "map_aeqd1191_18.png")
    #render_map(46.5102,15.6956,None,"testmap.png", zoom=15,imgx=500,imgy=500)
    m = MapnikRenderer(500,500, gpx_file="/data2/snemanje/20171016/data.gpx")
            #mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/file.xml")
            #mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto_gpx.xml")
    m.render_map(46.556164420769235, 15.624496195384616, None,
            "./test/testmap_gpx.png", overwrite=True)
