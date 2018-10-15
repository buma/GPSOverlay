import os
import datetime

from moviepy.video.io.ImageSequenceClip import ImageSequenceClip

class ImageSequenceClipDelay(ImageSequenceClip):
    """

    A VideoClip made from a series of images.

    Parameters
    -----------
    sequence
      Can be one of these:
      - The name of a folder (containing only pictures). The pictures
        will be considered in alphanumerical order.
      - A list of names of image files. In this case you can choose to
        load the pictures in memory pictures
      - A list of Numpy arrays representing images. In this last case,
        masks are not supported currently.
    durations
      List of the duration of each picture.
    with_mask
      Should the alpha layer of PNG images be considered as a mask ?
    ismask
      Will this sequence of pictures be used as an animated mask.
    speedup_factor
      How much to speed up image durations (default makes images taken
       at 3 second interval played at 8 FPS)
    effect_length
      How long should zoom_in/out effect be (seconds)
    max_image_delay
      Maximal delay between images.
    Notes
    ------
    If your sequence is made of image files, the only image kept in

    """
    FORMAT="%Y%m%d_%H%M%S.JPG"
    def __init__(self, sequence, durations=None, with_mask=True,
                 ismask=False, load_images=False, speedup_factor=24,
                 max_image_delay=None):
        def make_time_diff(func, sequence):
            """Makes time difference for sequence
            and function which should return datetime
            """
            prev = None
            for file, dt in map(func, sorted(sequence)):
                if prev is not None:
                    if max_image_delay is None:
                        yield (dt-prev).seconds, file
                    else:
                        yield min(max_image_delay, (dt-prev).seconds), file
                prev = dt

        #ImageSequenceClip.__init__(self,sequence, fps, durations, with_mask,
                #ismask, load_images)
        #durations = [x[0]/24 for x in self.make_time_diff(self._add_geo_using_exif,
                #sequence)]
        self.speedup_factor = speedup_factor
#Reads image names and plays them for as far as they exists (images taken 5
        #seconds appart are shown for 5 seconds
#Because this would be slow speedup_factor is made 24 makes images taken 3
        #seconds appart play at 8 FPS
        durations = [x[0]/speedup_factor for x in make_time_diff(lambda x: (os.path.basename(x),
            datetime.datetime.strptime(os.path.basename(x),
                ImageSequenceClipDelay.FORMAT)),
            sequence)]
        fps=None
        super(ImageSequenceClipDelay, self).__init__(sequence, fps, durations, with_mask,
                ismask, load_images)
