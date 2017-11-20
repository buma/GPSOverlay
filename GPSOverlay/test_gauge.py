if __name__ == "__main__":

    from .GaugeClipMaker import GaugeClipMaker

    duration=5 #seconds
    fps=25



    import moviepy.editor as mpy

    gcm = GaugeClipMaker("./gauges/velocimetro3.svg", 0, 260, 48, 312)
    def make_frame(t):
#Makes cursor move from 0-max in the time of this clip
        speed = map_range(t, 0, duration, 0, 260)
        #return gcm.make_clip(speed, 500, 500).make_frame(t)
        return gcm.make_clip(speed).make_frame(t)

    clip = mpy.VideoClip(make_frame, duration=duration) # 2 seconds
    clip.write_gif("svg2.gif",fps=fps)

