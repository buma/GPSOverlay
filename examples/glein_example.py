import os
import time
import datetime

from GPSOverlay.GPXDataSequence import GPXDataSequence
from moviepy.editor import concatenate_videoclips
from moviepy.video.VideoClip import ColorClip
import moviepy.video.compositing.transitions as transfx

#This uses default config
from config import (
        df,
        PARTIAL,
        get_frames
        )
#This uses custom config with some changes settings
#from custom_config import (
        #df,
        #PARTIAL,
        #get_frames
        #)

#This shows demo clip to test positions of data clips
clip = df.make_demo_clip()

clip.show(0, interactive=True)
clip.save_frame("demo_config.png", 0)
path = "/data2/snemanje/20180810/"
time_offset=-41
start_at=4
#Image sequence needs to have GPS location in images
frames = get_frames(filematch=os.path.join(path, "resized_tv", "*.JPG"), start_at=start_at, partial=PARTIAL)
gpx_seq_1 = GPXDataSequence.from_sequence_with_breaks(frames, df.FPS, with_mask=False,
        gpx_file=os.path.join(path,"data.gpx"),
       time_offset=time_offset, config=df )

print ("Duration:", gpx_seq_1.duration)


#Show 20th second of video
gpx_seq_1.show(20, interactive=True)
gpx_seq_1.save_frame("glein_config.jpg", 20)

final_clip = gpx_seq_1

#For testing if everything is OK:
final_clip.write_videofile("test", fps=10,
        audio=False, preset='ultrafast',
        threads=4)

#Rendering with map takes a long time. Map with mapnik takes around 8seconds
#per second in 25 FPS approximately 12 maps must be rendered
#For final render
#final_clip.write_videofile("/data2/20180810_25_hd_final1.mp4", fps=25,
        #audio=False, preset='medium',
        #threads=4)
