try:
    import mapnik2 as mapnik
except:
    import mapnik


a='z15'
map_uri="map_aeqd137_18.png"

#https://github.com/kevinstadler/southup

#Based on: https://gist.github.com/andrewharvey/1290744

# Set up projections
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
#merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

#South up
#merc = mapnik.Projection('+proj=tpeqd +lat_1=35 +lat_2=35 +lon_1=-80 +lon_2=-122  +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')



# long/lat in degrees, aka ESPG:4326 and "WGS 84"
longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
# can also be constructed as:
#longlat = mapnik.Projection('+init=epsg:4326')

#y - lat - 46
#x - lon - 15
#angle of map, so that to direction is at the top
def render_map(centrey, centrex, angle, map_uri, 
        gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx",
        zoom=18,imgx=200,imgy=200,
        mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto.xml"):

    if angle is None:
# spherical mercator (most common target map projection of osm data imported with osm2pgsql)
        merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
    else:
#Map rotation https://gis.stackexchange.com/questions/183175/rotating-90-using-two-point-equidistant-projection-with-proj4
        merc = mapnik.Projection('+proj=aeqd +ellps=sphere +lat_0=90 +lon_0=-' +
                str(angle-10))



    m = mapnik.Map(imgx, imgy)
    mapnik.load_map(m, mapfile)

    if angle is not None:

# Create a symbolizer to draw the points
        style = mapnik.Style()
        rule = mapnik.Rule()
        point_symbolizer = mapnik.MarkersSymbolizer()
        point_symbolizer.allow_overlap = True
        point_symbolizer.opacity = 0.5 # semi-transparent
        rule.symbols.append(point_symbolizer)

        line_symbolizer = mapnik.LineSymbolizer()
        line_symbolizer.stroke = mapnik.Color('rgb(100%,0%,0%)')
        line_symbolizer.stroke_width = 0.4

        rule.symbols.append(line_symbolizer)
        style.rules.append(rule)
        m.append_style('GPS_tracking_points', style)

# Create a layer to hold the ponts
        layer = mapnik.Layer('GPS_tracking_points')
        layer.datasource = mapnik.Ogr(file=gpx_file,
                layer='tracks')
        layer.styles.append('GPS_tracking_points')
        m.layers.append(layer)

        gs = ('{ "type":"FeatureCollection", "features": [ {' +
                    '"type":"Feature", "properties":{"name":"current"},'+
                        '"geometry": { "type":"Point",' +
                    '"coordinates":[%f, %f]}}]}' %(centrex, centrey))
        ds = mapnik.Datasource(
                type='geojson',
                inline=gs
                )

        point = mapnik.Layer('current_point')
        point.datasource = ds
        point.styles.append('GPS_tracking_points')
        m.layers.append(point)

# ensure the target map projection is mercator
    m.srs = merc.params()

    centre = mapnik.Coord(centrex, centrey)  
    transform = mapnik.ProjTransform(longlat, merc)
    merc_centre = transform.forward(centre)

# 360/(2**zoom) degrees = 256 px
# so in merc 1px = (20037508.34*2) / (256 * 2**zoom)
# hence to find the bounds of our rectangle in projected coordinates + and - half the image width worth of projected coord units
    dx = ((20037508.34*2*(imgx/2)))/(256*(2 ** (zoom)))
    minx = merc_centre.x - dx
    maxx = merc_centre.x + dx

# grow the height bbox, as we only accurately set the width bbox
    m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT

    bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10) # the y bounds will be fixed by mapnik due to ADJUST_BBOX_HEIGHT



# Note: aspect_fix_mode is only available in Mapnik >= 0.6.0
    m.zoom_to_box(bounds)

## If a scale denominator is specified
#if scale_denom:
        ## Get current scale denom, calculate necessary change
        #scale_change = scale_denom / m.scale_denominator()
        ## Resize image size
        #m.zoom(scale_change)

    mapnik.render_to_file(m, map_uri)
if False:
# Print stats
    print("Stats:")
    print("  Mapnik version: " + mapnik.mapnik_version_string())
    print("  Using map file: " + mapfile)
    print("  Using bounds: " + repr(bounds))
    print("  Scale Denominator: " + str(m.scale_denominator()))
    print("  Render into file: " + map_uri)
    print("  Image size: " + str(m.width) + "x" + str(m.height))

if __name__ == "__main__":
    centrey, centrex, angle = (46.55711886333333, 15.62431150777778, 137.31216620286796)
    #render_map(centrey, centrex, angle, "map_aeqd137_18.png")
    centrey, centrex, angle = (46.556164420769235, 15.624496195384616, 191.10020115018185)
    #render_map(centrey, centrex, angle, "map_aeqd1191_18.png")
    render_map(46.5102,15.6956,None,"testmap.png", zoom=15,imgx=500,imgy=500)
