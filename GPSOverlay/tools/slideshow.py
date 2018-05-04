from moviepy.video.VideoClip import VideoClip, ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.editor import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.fx.scroll import scroll
import moviepy.video.compositing.transitions as transfx

def zoom(clip, screensize):
    """Zooms preferably image clip for clip duration a little

    To make slideshow more movable

    Parameters
    ---------
    clip
        ImageClip on which to work with duration
    screensize
        Wanted (width, height) tuple

    Returns
    ------
    VideoClip in desired size
    """
    clip_resized = (clip.fx(resize, height=screensize[1]*2)
                .fx(resize, lambda t : 1+0.02*t)
                .set_position(('center', 'center'))
                )
    clip_composited = CompositeVideoClip([clip_resized]) \
            .fx(resize, width=screensize[0])


    vid = CompositeVideoClip([clip_composited.set_position(('center', 'center'))], 
                            size=screensize)
    return vid


def panorama(clip, screensize, duration=None, speed=None):
    """Makes image panorama of large images

    It pans image from left to right since they are very wide
    It works in two ways if duration is given it calculates speed to pan whole
    panorama in given number of seconds. If speed is given it sets duration so
    that whole pan will happen at given speed

    Parameters
    ---------
    clip
        ImageClip (not resized)
    screensize
        Wanted (width, height) tuple
    duration
        If given wanted duration of pan
    speed
        Number of pixel of move per time unit (duration is calculated)
    """

    #TODO: pause image at start and/or end for some time
    print("DURATION", duration, "SPEED:", speed)
    #FIXME: add workable assert
    #assert duration is None or speed is None
    clip = clip.fx(resize, height=screensize[1])

    width = screensize[0]

    if speed is not None:
        clip = clip.set_duration((clip.w-width)/speed)
    else:
        clip = clip.set_duration(duration)
        speed = (clip.w-width)/duration

    scrolled = scroll(clip, w=width, x_speed=speed)
    return scrolled

def make_image_slideshow(sequence, titles, height=None, width=None, image_duration=4,
        transition_duration=1, zoom_images=False, test=False):
    """Function makes slideshow VideoClip from sequence of images with their
    captions
    
    Parameters
    ---------
    sequence
        List of paths to images
    titles : list
        List of image captions
    height
        Height of wanted VideoClip
    width
        Width of wanted VideoClip
    image_duration
        How long is one image visible
    transition_duration
        How long is fade transition between images
    test : bool
        If true shows each image with caption in preview


    """
    #TODO: list of clip effects (so that panoramas can be panorama or specific
    #panorama)
    #TODO: support folder as a sequence
    images = sequence
    assert len(images) == len(titles), "Number of images and titles needs \
    to be the same"
    if height is None and width is None:
        clips = (ImageClip(image, duration=image_duration) \
                for image in sorted(images))
    else:
        if zoom_images:
            clips = (ImageClip(image, duration=image_duration) \
                    .fx(zoom, screensize=(width, height)) for image in sorted(images))
        else:
            clips = (ImageClip(image, duration=image_duration) \
                    .fx(resize, height=height, width=width) for image in sorted(images))
    conc_clips = []
    for clip, text in zip(clips, titles):
        #TODO: make text caption style configurable
        tc = TextClip(text, clip.size, method="caption", align="South",
                color="white", fontsize=30, font="M+-1p-medium")
        tc = tc.set_pos(("center", "bottom"))
        #print (clip.size, tc.size)
        #TODO: makes transparent bar size same size (based on highest caption)
        #adds 75% transparent bar under the caption
        #Bar starts 5 pixels above caption and ends at the bottom
        tc_col = tc.on_color(size=(clip.w,tc.h+5),
                color=(0,0,0), pos=('center'), col_opacity=0.6)
        tc_with_color = tc_col.set_pos(('center', 'bottom'))
        conc_clips.append(CompositeVideoClip([clip, tc_with_color]).set_duration(clip.duration))
    if test:
        for clip in conc_clips:
            clip.show(0, interactive=True)
    #TODO: make transition configurable
#1 is how long is the effect
    slided_clips = [clip.fx(transfx.crossfadein, transition_duration)
            for clip in conc_clips]
#-1 is how much is overlap between clips. It should be the same as effect
                #length
    final_clip = concatenate_videoclips(slided_clips,
            padding=-transition_duration, method="compose")
    return final_clip
