import os
import glob
import time

from moviepy.video.VideoClip import TextClip, ImageClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.resize import resize
from moviepy.editor import concatenate_videoclips
from moviepy.video.tools.drawing import color_gradient, circle

from GPXDataSequence import GPXDataSequence

partial = True
font="Bitstream-Vera-Sans-Mono-Bold"
#font="Liberation-Mono-Bold"
#font="EmojiOne-Color-SVGinOT"

def get_frames(filematch):
    sort = sorted(glob.glob(filematch))
    if partial:
        return sort[:220]
    return sort

normal_font = 60
top=40
margin=10

large_font=80
map_w = 500
map_h = 500
map_zoom = 19
map_mask = color_gradient((map_w, map_h), (map_w/2,map_h/2),
        (map_h/2,0), offset=0.9, shape='radial', col1=1, col2=0.0)
map_mask_clip = ImageClip(map_mask, ismask=True)
map_mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto.xml"
#map_mapfile="/home/mabu/Documents/MapBox/project/simple-osm/map.xml"
#map_mapfile="/home/mabu/Documents/MapBox/project/simple-osm/map_transparent.xml"

def make_speed_clip(speed):
    if speed*3.6 < 1:
        txt = "STOPPED"
    else:
        txt = "%2.2f km/h" % (speed*3.6)
    return TextClip(txt,
        fontsize=large_font, font=font, color='white',
        stroke_color='black')

#To make a circle on transparent background
#We make a circle size, center, radius, inside color RGB, outside
circle_clip =ImageClip(circle((map_w, map_h), (map_w/2, map_h/2), 8,
    (0,255,0), (0,0,0)))
#Make mask from it (channel 1 - green) since it's single color
circle_mask = circle_clip.to_mask(1)
#And use it as a mask
circle_clip = circle_clip.set_mask(circle_mask)
#We get circle on transparent background



def make_map(map_clip):
    #map_clip = map_clip.set_mask(map_mask_clip)
    #map_clip = map_clip.set_opacity(0.7)
    #We composite it on map image to get current location point
    both = CompositeVideoClip([map_clip, circle_clip])
    return both


frames = get_frames("/data2/snemanje/miklavz/original/1/changed/*.JPG")
frames2 = get_frames("/data2/snemanje/miklavz/original/2/changed/*.JPG")
data_clips = {
        'datetime': lambda dt: TextClip(dt.strftime("%d.%m.%Y %H:%M:%S"),
            fontsize=normal_font, font=font, color='white',
            stroke_color='black'),
        'datetime_pos': lambda t, W,H: t.set_pos((W-t.w-30, top)),
        'elevation': lambda alt: TextClip("%4.2f m" % (alt,),
            fontsize=normal_font, font=font, color='white',
            stroke_color='black'),
        'elevation_pos': lambda t, W,H: t.set_pos((W-t.w-30,
            top+normal_font+margin)),
        'heart': lambda alt: TextClip("%d BPM" % (alt,), fontsize=normal_font, font=font, color='red',
            stroke_color='orange'),
        'heart_pos': lambda t, W,H: t.set_pos((W-t.w-30,
            top+2*(normal_font+margin))),
        'bearing': lambda alt: TextClip("%3.1f °" % (alt,),
            fontsize=normal_font, font=font, color='white',
            stroke_color='black'),
        'bearing_pos': lambda t, W,H: t.set_pos((W-t.w-30,
            top+3*(normal_font+margin))),
        'speed': make_speed_clip,
        'speed_pos': lambda t, W,H: t.set_pos((W-t.w-30,H-t.h-200)),
        'map': make_map,
        'map_pos': lambda t, W,H: t.set_pos((W/2-t.w-30,
            H-t.h-100)),
        
        #'date1_pos': lambda t, W,H: ((W-t.w-30, 30)),
        }

fps=8
#print (TextClip.list('font'))
#fonts = TextClip.list('font')
#for font in fonts:
    #if "emoji" in font.lower():
        #print (font)

#a=5/0

gpx_seq = GPXDataSequence(frames[4:], fps, with_mask=False,
        gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx",
       time_offset=944, data_clips=data_clips, map_w=map_w, map_h=map_h,
       zoom=map_zoom)

#gpx_seq2 = GPXDataSequence(frames2[-10:], fps, with_mask=False,
        #gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx",
       #time_offset=-65, data_clips=data_clips )

str_format = "{:>3} {:20} {} {:03.3f} {:02.6f} {:02.6f} {:03.2f}°"

#for idx, (fn, gps, time1) in enumerate(zip(gpx_seq.sequence, gpx_seq.gpx_data,
    #gpx_seq.images_starts)):
    #print (str_format.format(idx, os.path.basename(fn), gps.datetime, time1, gps.lat, gps.lon,
        #gps.bearing))

#gpx_seq.make_frame(1)
#gpx_seq.save_frame("nekaj.jpg", 8)

#both = gpx_seq.fx(resize, height=1080)
#both.show(8, interactive=True)

if True:

    both = gpx_seq

    #both = concatenate_videoclips([gpx_seq, gpx_seq2])

    both = both.fx(resize, height=1080)


    #both.write_videofile("all1.mp4", fps=25, audio=False, preset='ultrafast',
            #threads=4)
    both.write_images_sequence("/data2/snemanje/output/frame_center2_%05d.jpg")


