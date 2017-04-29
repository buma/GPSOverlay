import os
import glob

from moviepy.video.VideoClip import TextClip
from moviepy.video.fx.resize import resize
from moviepy.editor import concatenate_videoclips

from GPXDataSequence import GPXDataSequence

partial = False
font="Bitstream-Vera-Sans-Mono-Bold"
#font="Liberation-Mono-Bold"
#font="EmojiOne-Color-SVGinOT"

def get_frames(filematch):
    sort = sorted(glob.glob(filematch))
    if partial:
        return sort[:20]
    return sort

normal_font = 60
top=40
margin=10

large_font=80

def make_speed_clip(speed):
    if speed*3.6 < 1:
        txt = "STOPPED"
    else:
        txt = "%2.2f km/h" % (speed*3.6)
    return TextClip(txt,
        fontsize=large_font, font=font, color='white',
        stroke_color='black')

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
       time_offset=944, data_clips=data_clips )

gpx_seq2 = GPXDataSequence(frames2[-10:], fps, with_mask=False,
        gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx",
       time_offset=-65, data_clips=data_clips )

#for (fn, gps, time) in zip(gpx_seq.sequence, gpx_seq.gpx_data,
        #gpx_seq.images_starts):
    #print (os.path.basename(fn), gps.datetime, time, gps.speed*3.6, gps.heart)

#gpx_seq.make_frame(1)
#gpx_seq.save_frame("nekaj.jpg", 8)
#gpx_seq.show(1)

if False:

    both = concatenate_videoclips([gpx_seq, gpx_seq2])

    both = both.fx(resize, height=1080)


    both.write_videofile("all1.mp4", fps=25, audio=False, preset='ultrafast',
            threads=4)


