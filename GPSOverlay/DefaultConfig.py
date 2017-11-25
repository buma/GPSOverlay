import datetime
from moviepy.video.VideoClip import ImageClip, ColorClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.tools.drawing import circle, color_gradient
from .util.Position import Position
from .util.ConfigItem import ConfigItem, ChartConfigItem
from .util import find_font
from TextClipPIL import TextClipPIL

from collections import defaultdict


class DefaultConfig(object):
    """Initializes config with default options

    Parameters
    ----------
    default_font : str
        Font used in TextClip. Valid value is one of TextClip.list("font")
    normal_font_size : int
        Normal font size (ImageMagic -pointsize parameter) By default used
        everywhere except speed clip
    large_font_size : int
        Large font size (ImageMagic -pointsize parameter) By default used
        in speed clip
    padding : Position
        How much padding is from the border of the image to overlays. Can
        be set each parameter individually or as in CSS when setting
        padding
    margin : int
        Margin between overlays

    """

    def __init__(self, default_font=find_font("Bitstream Vera Sans:bold:mono"),
            normal_font_size=30, large_font_size=40,
            padding=Position.make([40,30,0]),
            margin=10):
        self.default_font = default_font
        self.normal_font_size = normal_font_size
        self.large_font_size = large_font_size
        self.padding = padding
        self.margin = margin
        self.config = defaultdict(list)

    def config_items(self, need_config=False):
        """Returns config items same format as dict.items()

        Key is config key (elevation, speed, etc.), value is util.ConfigItem

        Parameters
        ---------
        need_config : bool
            If true returns only configs that need initialization (Have class
            in config)

        """
        for key, configs in self.config.items():
            for config in configs:
                if need_config and config.need_init():
                    yield key, config
                elif not need_config:
                    yield key, config

    def make_items(self):
        """Returns config items to be used in make frame

        Key is config key (elevation, speed, etc.), second value is
        util.ConfigItem

        Map is always returned first (if it exists)
        This is because map needs to be first when composing on breaks.
        Each ConfigItem that has multiple types of overlays (Simple, Chart,
        Gauges) is returned multiple types. (Key appears multiple types, each
        time with different ConfigItem)

        Yields
        -----
        str, util.ConfigItem
            First item is config key, second is ConfigItem

        """
        if "map" in self.config:
            yield "map", self.config["map"][0]
        the_rest = filter(lambda key_configs: key_configs[0] != "map",
                self.config.items())
        for key, configs in the_rest:
            for value in configs:
                yield key, value


    def make_default_config(self):
        self.make_datetime_config()
        self.make_elevation_config()
        self.make_heart_config()
        self.make_bearing_config()
        self.make_speed_config()
        self.make_map_config()

    def default_position(self, how_many_configs):
        """Function calculates default position based on how many configs
        already exists

        Position is calculated as such: Align to right on padding.right value
        First config is padding.top from top. Next are additonaly
        normal_font_size+margin moved from top as many times as there are
        configs.

        So you can call this function many times and it will align configs on
        the right one after another

        Parameters
        ----------
        how_many_configs : int
            How many configs already exists (Each config is element in
            self.config)

        Returns
        ------
        func
            PositionFunction (input is clip and full_clip width height, return
            is clip set at wanted position)
        """
        return lambda t, W,H: t.set_pos((W-t.w-self.padding.right,
            self.padding.top+how_many_configs*(self.normal_font_size+self.margin)))

    @staticmethod
    def _if_set(input_value, default_value):
        """If input_value is not None return it otherwise return
        default_value"""
        return default_value if input_value is None else input_value

    def make_datetime_config(self, func=None, position=None, stroke_color=None):
        how_many_configs = len(self.config.keys())
        self.config["datetime"].append( ConfigItem(
                func= self._if_set(func, lambda dt: TextClipPIL(dt.strftime("%d.%m.%Y %H:%M:%S"),
                    fontsize=self.normal_font_size, font=self.default_font, color='white',
                    stroke_color=stroke_color)),
                position=self._if_set(position,
                    self.default_position(how_many_configs)),
                sample_value=datetime.datetime.now()
                ))

    def make_elevation_config(self, func=None, position=None,
            config=None, stroke_color=None): 
        how_many_configs = len(self.config.keys())
        self.config["elevation"].append( ConfigItem(
                func = self._if_set(func, lambda alt: TextClipPIL("%4.2f m" % (alt,),
                    fontsize=self.normal_font_size, font=self.default_font, color='white',
                    stroke_color=stroke_color)),
                position=self._if_set(position,
                    self.default_position(how_many_configs)),
                config = config,
                sample_value=42.24
                ))
    def make_heart_config(self, func=None, position=None,
            config=None, stroke_color=None):
        how_many_configs = len(self.config.keys())
        self.config["heart"].append( ConfigItem(
                func = self._if_set(func, lambda alt: TextClipPIL("%d BPM" % (alt,),
                    fontsize=self.normal_font_size, font=self.default_font, color='red',
            stroke_color=stroke_color)),
                position=self._if_set(position,
                    self.default_position(how_many_configs)),
                config=config,
                sample_value=133
                ))
    def make_bearing_config(self, func=None, position=None,
            config=None, stroke_color=None):
        how_many_configs = len(self.config.keys())
        self.config["bearing"].append( ConfigItem(
                func = self._if_set(func,  lambda alt: TextClipPIL("%3.1f °" % (alt,),
                    fontsize=self.normal_font_size, font=self.default_font, color='white',
                    stroke_color=stroke_color)),
                position = self._if_set(position,
                    self.default_position(how_many_configs)),
                config=config,
                sample_value=260
                ))
    def make_speed_config(self, func=None, position=None,
            config=None, stroke_color=None):
        how_many_configs = len(self.config.keys())
        self.config["speed"].append( ConfigItem(
                func = self._if_set(func, self.make_speed_clip),
                position = self._if_set(position, self.default_position(how_many_configs)),
                config=config,
                sample_value=15.6
                ))
    def make_slope_config(self, func=None, position=None,
            config=None, stroke_color=None):
        how_many_configs = len(self.config.keys())
        self.config["slope"].append( ConfigItem(
                func = self._if_set(func, lambda slope: TextClipPIL("%d %%" % (slope,),
            fontsize=self.normal_font_size, font=self.default_font, color='white',
            stroke_color=stroke_color)),
                position = self._if_set(position,
                    self.default_position(how_many_configs)),
                config=config,
                sample_value=-4.3
                ))

    def make_map_config(self, map_width=250, map_height=250,
            map_zoom=16, map_mapfile=None, gpx_style=None,
            gpx_file=True, func=None, position=None, maps_cache=None,
            ):
        try:
            from .MapnikRenderer import MapnikRenderer
        except ImportError as i:
            print ("Skipping map configuration because mapnik couldn't be " +
                    "imported")
            return

        map_config = {
                "class": MapnikRenderer, #Calls init on this class with given
                #parameters
                "map_w": map_width,
                "map_h": map_height,
                "map_zoom": map_zoom,
                "mapfile": map_mapfile,
                "gpx_style": gpx_style,
                "gpx_file":"__gpx_file", #If true path to gpx file will be added when
                "maps_cache":maps_cache,
                #class is initialized
                "_run_func":("render_map", {
                    "_DICT": "gps_info",
#lat, lon, angle parameters will be copied from gps_info
                    "angle_offset": -10,
                    })
                }
        self.config["map"].append( ConfigItem(
                func= self._if_set(func, self.make_map_clip),
                # center
                #'map_pos': lambda t, W,H:
                #t.set_pos((W/2-t.w-self.padding.right,
                #H-t.h-100)),
                #right bottom
                position=self._if_set(position, lambda t, W,H: t.set_pos((W-t.w-self.padding.right,
                    H-t.h-100))),
                config=map_config,
                sample_value= lambda clip, config:ColorClip((config["map_w"],
                    config["map_h"]), [125,35,0])
                ))

    def make_chart_config(self, key, position, config, func=None):
        if "wanted_value" not in config:
            config["wanted_value"] = key
        if "gpx_data" not in config:
            config["gpx_data"] = "__gpx_data"
        func = self._if_set(func, lambda c: c)
        ci = ChartConfigItem(position=position,
                config=config, func=func)
        self.config[key].append(ci)

    def make_demo_clip(self, image=None):
        def make_frame(t):
            if image is None:
                f = ColorClip((1333,1000), [56, 14,252]).make_frame(0)
            else:
                f = ImageClip(image).make_frame(0)
            for key, key_config in self.config.make_items():
                data = key_config.sample(f)
                print ("data:", data)
                if data is None:
                    continue
                created_clip = ci.func(data)
                if created_clip is None:
                    continue
                c = ci.position(created_clip, f.shape[1], f.shape[0])
                f = c.blit_on(f, 0)
            return f
        return VideoClip(make_frame, duration=1)



    def make_speed_clip(self, speed):
        if speed*3.6 < 1:
            txt = "STOPPED"
        else:
            txt = "%2.2f km/h" % (speed*3.6)
        return TextClipPIL(txt,
            fontsize=self.large_font_size, font=self.default_font, color='white',
            stroke_color=None)



    def make_transparent_map_clip(self, map_clip):
        map_w = map_clip.w
        map_h = map_clip.h
#Makes radial mask which is used to blur map as a circle with transparent
#background
        map_mask = color_gradient((map_w, map_h), (map_w/2,map_h/2),
                (map_h/2,0), offset=0.9, shape='radial', col1=1, col2=0.0)
        map_mask_clip = ImageClip(map_mask, ismask=True)
        map_clip = map_clip.set_mask(map_mask_clip)
        map_clip = map_clip.set_opacity(0.7)
        return self.make_map_clip(map_clip)

    def make_map_clip(self, map_clip):
        #We composite it on map image to get current location point
#TODO: make circle once and just compose it in currently it is very wasteful
        map_w = map_clip.w
        map_h = map_clip.h
        circle_clip = ImageClip(circle((map_w, map_h), (map_w/2, map_h/2), 8,
            (0,255,0), (0,0,0)))
#Make mask from it (channel 1 - green) since it's single color
        circle_mask = circle_clip.to_mask(1)
#And use it as a mask
        circle_clip = circle_clip.set_mask(circle_mask)
#We get circle on transparent background
        both = CompositeVideoClip([map_clip, circle_clip])
        return both

    def __repr__(self):
        skeys = sorted(self.config.keys())
        out = []
        for key in skeys:
            c = self.config[key][0]
            f = []
            cache = ""
            if key == "map" and c.config is not None:
                if c.config.get("maps_cache", None) != None:
                    cache = "[C]"
            else:
                for c in self.config[key]:
                    f.append(c.config_type)
            out.append("{}{}:{}".format(key, cache, "".join(f)))
        return ",".join(out)
