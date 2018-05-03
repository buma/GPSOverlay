import numpy as np
from moviepy.video.VideoClip import VideoClip, ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.editor import concatenate_videoclips
from moviepy.video.fx.resize import resize
import moviepy.video.compositing.transitions as transfx


def make_image_slideshow(sequence, titles, height=None, width=None, image_duration=4,
        transition_duration=1, test=False):
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
    #TODO: support folder as a sequence
    images = sequence
    assert len(images) == len(titles), "Number of images and titles needs \
    to be the same"
    if height is None and width is None:
        clips = (ImageClip(image, duration=image_duration) \
                for image in sorted(images))
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
        mask = np.ones((clip.size[1], clip.size[0]), 'float')
        #Bar starts 5 pixels above caption and ends at the bottom
        start_mask = clip.size[1]-tc.size[1]-5

        mask[start_mask:, :] = 0.75
        mask_clip = ImageClip(mask, ismask=True)
        clip.mask = mask_clip
        conc_clips.append(CompositeVideoClip([clip, tc]).set_duration(clip.duration))
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
