import os
import types
import numpy as np

from moviepy.video.VideoClip import VideoClip, ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.editor import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.fx.scroll import scroll
import moviepy.video.compositing.transitions as transfx
from moviepy.video.fx.fadein import fadein

from ..SVGImageClip import SVGImageClip

def zoom(clip, screensize, show_full_height=False):
    """Zooms preferably image clip for clip duration a little

    To make slideshow more movable

    Parameters
    ---------
    clip
        ImageClip on which to work with duration
    screensize
        Wanted (width, height) tuple
    show_full_height
        Should this image be shown in full height. This is usefull when 4:3
        images are shown in 16:9 video and need to be shown in full.
        Otherwise they are shown in full width and top and bottom is cut off.

    Returns
    ------
    VideoClip in desired size
    """
    #We need to resize high imageč differently
    if clip.h > clip.w or show_full_height:
        clip_resized = (clip.fx(resize, width=screensize[0]*2)
                    .fx(resize, lambda t : 1+0.02*t)
                    .set_position(('center', 'center'))
                    )
        clip_composited = CompositeVideoClip([clip_resized]) \
                .fx(resize, height=screensize[1])
    else:
        clip_resized = (clip.fx(resize, height=screensize[1]*2)
                    .fx(resize, lambda t : 1+0.02*t)
                    .set_position(('center', 'center'))
                    )
        clip_composited = CompositeVideoClip([clip_resized]) \
                .fx(resize, width=screensize[0])


    vid = CompositeVideoClip([clip_composited.set_position(('center', 'center'))], 
                            size=screensize)
    return vid


def panorama(clip, screensize, duration=None, speed=None, freeze_duration=1.5):
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
    freeze_duration : float
        Number of seconds to freeze before scroll and at the end
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
    return concatenate_videoclips([scrolled.to_ImageClip(0).set_duration(freeze_duration),
        scrolled,
        #FIXME: why is +1 actually needed without it there is no freeze at end
        scrolled.to_ImageClip(scrolled.duration).set_duration(freeze_duration+1)])
 
def image_effect(clip, screensize, duration=None, speed=None, show_full_height=False):
    if clip.w/clip.h > 2:
        return panorama(clip, screensize, duration, speed)
    return zoom(clip, screensize, show_full_height)

def make_clip(clip, text, height, width, font, font_color, fontsize):
    if font is None:
        return clip
    #TODO: make text caption style configurable
    #Swimming changes text color to light blue, moves text up and resized
    #it
    #It also adds black stroke that's why resizing is needed
    #And adds icon of swimming on the bottom
    if text.startswith("KOP:"):
        text = text[4:]
        font_color_c="#00aaff"
        pos = "top"
        swimm = True
        stroke_color="black"
        factor=2
        mult=1.4*factor
    else:
        font_color_c = font_color
        pos = "bottom"
        swimm = False
        stroke_color = None
        mult=1
        factor=1
    if width is None:
        text_space_size = None
    else:
        text_space_size = (width*factor, 40*factor)
    text_caption = TextClip(text, size=text_space_size, method="caption",
            align="center",
            color=font_color_c, fontsize=fontsize*mult, font=font,
            stroke_color=stroke_color)
    if swimm:
        text_caption = text_caption.fx(resize, height=text_caption.h/2)
    text_caption = text_caption.set_pos(("center", "center"))
    #print (clip.size, tc.size)
    #TODO: makes transparent bar size same size (based on highest caption)
    #adds 60% transparent bar under the caption
    #Bar starts 5 pixels above caption and ends at the bottom
    if not swimm:
        text_caption_bar = text_caption.on_color(size=(clip.w, text_caption.h+5),
                color=(0,0,0), pos=('center'), col_opacity=0.6)
        text_caption_with_bar = text_caption_bar.set_pos(('center',
            'bottom'))
    else:
        text_caption_with_bar = text_caption.set_pos(('center', 20))
    clips = [clip, text_caption_with_bar]
    if swimm:
        swimm_size = fontsize
        #TODO: make location of this configurable
        swim_clip = \
        SVGImageClip("/home/mabu/programiranje/overlay/projects/glein/images/swimming-15.svg",
                width=swimm_size, height=swimm_size).set_pos(('center',
            clip.h-20-swimm_size))
        clips.append(swim_clip)
    return (CompositeVideoClip(clips) \
            .set_duration(clip.duration))

class SlideshowImagesClip(VideoClip):

    def __init__(self, sequence, titles, height=None, width=None, image_duration=4,
        transition_duration=1, fontsize=30, font="M+-1p-medium",
        font_color="white", zoom_images=False, test=False):
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
        fontsize
            Font point size
        font
            Name of the font to use. See ``TextClip.list('font')`` for
        the list of fonts you can use on your computer.
        font_color
            Color of the text. See ``TextClip.list('color')`` for a
        list of acceptable names.
        test : bool
            If true shows each image with caption in preview


        """

        VideoClip.__init__(self, ismask=False)
        image_duration+=transition_duration*2
        #FIXME: duration is wrong if there is panorama in images
        tt = np.cumsum([0] + list(np.repeat(image_duration, len(sequence))))
        #print (tt)
        self.images_starts = np.maximum(0, tt + (-1*transition_duration)*np.arange(len(tt)))
        self.duration = self.images_starts[-1]
        self.end = self.images_starts[-1]
        self.sequence = sequence
        #print(self.images_starts)
        #print ("DUR:", self.duration)
        def find_image_index(t):
            return max([i for i in range(len(self.sequence))
                              if self.images_starts[i]<=t])
        self.lastindex = None
        self.lastimage = None

        self.previndex = None
        self.previmage = None

        def load_clip(index):
            image = self.sequence[index]
            text = titles[index]
            if text.startswith("W:"):
                text = text[2:]
                show_full_height = True
            else:
                show_full_height = False
            if height is None and width is None:
                clip = ImageClip(image, duration=image_duration)
            else:
                if zoom_images:
                    clip = ImageClip(image, duration=image_duration) \
                            .fx(image_effect, screensize=(width, height), \
                            duration=20, show_full_height=show_full_height)
                elif show_full_height:
                    clip = ImageClip(image, duration=image_duration) \
                            .fx(resize, height=height).set_position('center',
                                    'center')
                    clip = CompositeVideoClip([clip], 
                                            size=(width, height))

                else:
                    clip = ImageClip(image, duration=image_duration) \
                            .fx(resize, height=height, width=width)
            #Adds text label etc. on clip
            clip = make_clip(clip, text, height, width, font, font_color,
            fontsize)
            return clip

        def make_frame(t):
        
            index = find_image_index(t)
            fade = False
            #print ("INDEX:", index)
            #print ("TIME:", t, t-self.images_starts[index])
            clip_time = t- self.images_starts[index]
            #At the start of the clip we need to fade to the next
            if clip_time < transition_duration:
                fade = True
                #print ("FADE IN")

                if self.lastindex == index-1 and self.previndex != index-1:
                    self.previmage = self.lastimage
                    self.previndex = self.lastindex

                #print ("PREV IDX:", self.previndex)
            #When we are on last image we delete previous one from memory
            #Instead of 2 images in memory we have only one
            #Bu this can only happen on last image
            elif self.previndex and index == len(self.sequence)-1:
                #print ("LAST INDEX")
                del self.previmage
                self.previmage = None
                self.previndex = None

            #If we need to load new image we load it add the mask and add fade
            #if needed
            if index != self.lastindex:
                clip = load_clip(index)
                #print ("MASK:", clip.mask)
                if clip.mask:
                    #TODO: is mask actually needed outside fading?
                    clip.mask.duration = clip.duration
                    newclip = clip.copy()
                    newclip.mask = clip.mask.fx(fadein, transition_duration)
                else:
                    newclip = clip

                self.lastimage = newclip
                self.lastindex = index
            
            #Fading between two images
            if fade and self.previmage:
                image = self.lastimage.blit_on(
                        self.previmage.get_frame(t-self.images_starts[self.previndex]),
                        t-self.images_starts[self.lastindex])
            else:
                ##Fade at the start where we don't have previous image
                ##TODO: is this actually needed
                #if fade:
                    #self.set_mask(
                            #self.lastimage.mask)
                    ##print ("Fade MASK")
                #else:
                    #self.mask = None
                self.mask = None
                #Normal image without fading
                image = self.lastimage.get_frame(t-self.images_starts[index])
            #print ("DIFF:", self.duration-t, 1/25)
            #Deletes image from memory if we are closer to end of the clip as
            #last frame in 25 FPS
            #If we are wrong we will just load the image again
            if index == len(self.sequence)-1 and self.duration-t < 2/25:
                #print ("LAST FRAME")
                del self.lastimage
                self.lastimage = None
                self.lastindex = None
            return image

        self.make_frame = make_frame
        if width is not None and height is not None:
            self.size = (width, height)
        else:
            self.size = make_frame(0).shape[:2][::-1]


#@profile
def make_image_slideshow(sequence, titles, height=None, width=None, image_duration=4,
        transition_duration=1, fontsize=30, font="M+-1p-medium",
        font_color="white", zoom_images=False, test=False):
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
    fontsize
        Font point size
    font
        Name of the font to use. See ``TextClip.list('font')`` for
      the list of fonts you can use on your computer.
    font_color
        Color of the text. See ``TextClip.list('color')`` for a
      list of acceptable names.
    test : bool
        If true shows each image with caption in preview


    """
    #TODO: list of clip effects (so that panoramas can be panorama or specific
    #panorama)
    #TODO: support folder as a sequence
    images = sequence
    assert len(images) == len(titles), "Number of images and titles needs \
    to be the same"
    return SlideshowImagesClip(images, titles, height, width, image_duration,
            transition_duration, fontsize, font, font_color, zoom_images, test)

    def dump(self):
        ret_string = ["<slideshow>"]
        ret_string.append("size:{}x{} transition:{}s fontsize:{} "
                "font:{} font_color:{} zoom_images:{}".format(width, height,
                    transition_duration, fontsize, font, font_color,
                    zoom_images))
        ret_string.append("Duration:{}s".format(final_clip.duration))
        for image, title, clip in zip(sequence, titles, slided_clips):
            ret_string.append("{2: 6.2f}s {0} {1}".format(
                os.path.basename(image), title, clip.duration))
        ret_string.append("</slideshow>")
        return "\n".join(ret_string)

    final_clip.dump = types.MethodType(dump, final_clip)
    return final_clip
