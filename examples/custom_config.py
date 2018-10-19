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

#This are make_*clip function which get specific data: speed/elevation/slope
#and must return moviepyClip it can be text or anything else
#Units can be changed, colors etc.
#TextClipPIL is used instead of TextClip because it doesn't use ImageMagick and
#is faster
#For gauges and charts different config is used.
def make_desc_speed_clip(speed):
    if speed*3.6 < 1:
        txt = "Hitrost: STOJI"
    else:
        txt = u"Hitrost: %2d km/h" % (round(speed*3.6))

    return TextClipPIL(txt,
        fontsize=df.large_font_size, font=df.default_font, color='white',
        stroke_color=None)

def make_elevation_clip(elevation):
    round_elevation = round(elevation)
    return TextClipPIL("Nadmorska višina: %4d m" % (round_elevation,),
            fontsize=df.normal_font_size, font=df.default_font, color='white',
            stroke_color=None)

def make_slope_clip(slope):
    return TextClipPIL("Naklon: %.2f %%" % (slope,),
            fontsize=df.normal_font_size, font=df.default_font, color='white',
            stroke_color=None)

#Function adds dark background to date/slope/speed display
def dark_func(x):
    #3 because we have 3 displays date/slope/speed
    return ColorClip(size=(CLIP_WIDTH+5,
        df.padding.top+3*(df.normal_font_size+df.margin)+5),
            color=(0,0,0)).set_opacity(0.6)
df.WIDTH = WIDTH
df.HEIGHT = HEIGHT
df.FPS = 9
df.SKIP_IMAGE_CLIPS = SKIP_IMAGE_CLIPS
df.zoom_images = True
df.transition_duration = 1
#Since only custom func is used positions are set automatically
#Position is calculated as such: Align to right on padding.right value
#First config is padding.top from top. Next are additionaly
#normal_font_size+margin moved from top as many times as there are
#configs.
df.make_datetime_config(width=CLIP_WIDTH, strftime="%a %d %b %H:%M %Y")
df.make_slope_config(func=make_slope_clip, width=CLIP_WIDTH)
df.make_speed_config(func=make_desc_speed_clip, width=CLIP_WIDTH)
#Elevation has custom position on the middle and bottom of clip
df.make_chart_config("elevation", 
        position=lambda t, W,H: t.set_pos((0, H-t.h-df.padding.bottom)),
        config=elevation_chart_config)
df.make_elevation_config(func=make_elevation_clip, width=CLIP_WIDTH,
        position=lambda t, W,H: t.set_pos((W/2-CLIP_WIDTH/2,
            H-t.h-df.margin)))
dark_config = ConfigItem(
        func=dark_func,
        position=lambda t, W, H: t.set_pos((W-CLIP_WIDTH-5-df.padding.right,
            df.padding.top-5)),
        config=None
        )
df.config["datetime"].insert(0,dark_config)
df.caption_font = caption_font
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
