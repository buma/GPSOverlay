import time
import os
import glob
from GPSOverlay.DefaultConfig import DefaultConfig
from GPSOverlay.ChartMaker import ChartMaker
from GPSOverlay.util import find_font
from GPSOverlay.TextClipPIL import TextClipPIL
from GPSOverlay.util.Position import Position
from moviepy.video.VideoClip import ColorClip
from GPSOverlay.util.ConfigItem import ConfigItem

def get_frames(filematch=None, joined_match=None, start_at=0, partial=True):
    if joined_match is not None:
        filematch = os.path.join(joined_match, "resized_kept", "*.JPG")
    sort = sorted(glob.glob(filematch))[start_at:]
    if partial:
        return sort[:200]
    return sort

#Width of text information: speed/elevation etc.
CLIP_WIDTH = 284
#HEIGHT = 576
#WIDTH = 768

WIDTH=1920
HEIGHT=1080
#WIDTH=1280
#HEIGHT=720
SKIP_IMAGE_CLIPS = False
PARTIAL = False
map_file = "/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto_gpx1_h_bus.xml"
font_path = "/usr/share/fonts/noto/"
caption_font="Gotham-Bold"
slideshow_caption_font = "GothamNarrow-Bold"

if WIDTH == 1920:
    fontsize_title = 60*1.6
    fontsize_subtitle = 30*1.6
    elevation_height = int(100*1.6)
    map_position_func = lambda t, W,H: t.set_pos((W-t.w-df.padding.right,
                H-t.h-160-df.margin))
else:
    fontsize_title = 60
    fontsize_subtitle = 30
    elevation_height = 100
    map_position_func = None



elevation_chart_config = {
    "class": ChartMaker,
    "figure_size": ("w", elevation_height),
    "y_lim":(600,700), #min max elevation day1
    #"y_lim":(480,610), #min max elevation day2
    #"y_lim":(440,620), #min max elevation day3
    #"y_lim":(340,520), #min max elevation day4
    #"y_lim":(340,520), #min max elevation day5
   #ax.set_ylim(340,710) #overall min max elevation 
    "_run_func":("make_chart_at", {
        'index':"__gpx_index"}
        )
    }


df = DefaultConfig(default_font="/usr/share/fonts/OTF/GothamNarrow-Book.otf",
        #find_font("Gotham:Narrow:Thin"),
        padding=Position.make([20,20,0]))

df.WIDTH = WIDTH
df.HEIGHT = HEIGHT
df.FPS = 9
df.SKIP_IMAGE_CLIPS = SKIP_IMAGE_CLIPS
df.zoom_images = True
df.transition_duration = 1
df.caption_font = caption_font
#Adds datetime config, elevation config, heart rate config, bearing and speed
#config on default locations with default positions
df.make_default_config()
df.slideshow_caption_font = slideshow_caption_font
df.slideshow_fontsize = fontsize_subtitle
df.is_wide=(16/9)==(WIDTH/HEIGHT)
#df.make_gauge_config("speed",
        #position=lambda c, W,H: c.set_pos((df.padding.left, df.padding.top)),
        #config=gauge_speed_config)

#This needs mapnik and OSM data in postgresql one map needs around 8seconds to
#render on Intel(R) Core(TM) i5-3570K with 8 GB of RAM you need 12 in 25 FPS
#if you don't want to use it just comment it
df.make_map_config(
        map_mapfile=map_file,
        map_zoom=16, maps_cache="./.map_cache_180810", #8_1",
        support_breaks=True, angle_offset=-10,
        position=map_position_func,
        map_width=200, map_height=200, gpx_style="gpx", font_path=font_path)
        ##map_zoom=16, maps_cache="./.map_cacheGaj")

#FIXME: each day needs different map_cache, because of different gpx file on a
#map
