import inspect
from util import BreakType

class ConfigItem(object):
    """Config for one overlay

    One overlay is one data shown (datetime, speed, speed gauge, elevation
    chart, map display)

    To create it we need to have function which creates Clip from GPS data and
    function which sets position based on whole clip size and generated clip
    size.

    We can have simple overlays which just show value (like speed, elevation,
    slope, heart rate, etc.)
    Or complex overlays like gauges, charts, maps.

    Values in [] show how can we show items:
        - S - simple - TextClip which is by default
        - G - gauge - spedometer for example uses GPSOverlay.GaugeClipMaker by
            default
        - C - chart - matplotlib chart uses GPSOverlay.ChartMaker by default

    Currently possible items are:
        - bearing : float - Compas bearing in degrees [S/G/C]
        - elevation : float - Elevation in meters [S/G/C]
        - speed : float - Moving speed in m/s [S/G/C]
        - heart : float - Heart rate in BPM (if exists in input file) [S/G/C]
        - slope : float - Slope between current points in % [S/G/C]
        - datetime : datetime - Time and date of GPX point (timezone?) [S] FIXME
        - map - Mapnik generated map of current point

    Parameters
    ---------
    func : function
        Input parameter is data for this, output needs to be moviepy.Clip
    position : function
        Input parameter is created clip made with previous function and width
        and height of full image. Output is Clip set to wanted position
    position_break_func :function
        Input parameters for function that is called when there are breaks
        FIXME: doc
    config : dict
        Specific needed settings for complex overlays (map and charts for now)
    sample_value 
        Sample input value that func can create valid Clip (Used for testing
        clip locations)

    See Also
    -------
    GPSOverlay.ChartMaker : Chart generator
    GPSOverlay.GaugeClipMaker : Gauge generator

    """
    def __init__(self, func=None, position=None, config=None,
            sample_value=None, position_break_func=None):
        self.func = func
        self.position = position
        self.position_break_func = position_break_func
        self.config = config
        self.sample_value = sample_value
        self.object = None
        self.chart_object = None

    def sample(self, clip):
        """Returns input value like it was read from GPX

        For example speed config would get speed in m/s as sample_value,
        map_config empty clip same size as map would be etc.

        if self.sample_value is function it calls it 
        with clip param and self.config
        otherwise it just returns it

        """
        if callable(self.sample_value):
            return self.sample_value(clip, self.config)
        return self.sample_value

    def get_clip(self, key, gps_info, gpx_index, W, H, break_type=BreakType.NO,
            end_break_time=None, time_in_break=None):
        """Fully creates clip

        Gets data( self.get_data), runs function (self.func) and sets position
        (self.position)

        Parameters
        ---------
        key : str
            Config key (elvation, speed, etc.) What do we want
        gps_info : util.GPSData
            Data to draw
        gpx_index : int
            Index in GPX points
        W : int
            Width of full picture
        H : int
            Height of full picture
        break_type : util.BreakType
            Type of break (Start, middle, End)
        end_break_time : int
            Number of seconds

        Returns
        ------
        moviepy.Clip 
            Clip generated from data set on correct position or None if clip
            couldn't be created
        """
        data = self.get_data(key, gps_info, gpx_index, break_type,
                end_break_time, time_in_break, W, H)
        if data is None:
            return None
        created_clip = self.func(data)
        if created_clip is None:
            return None
        if break_type != BreakType.NO and self.config is not None \
            and self.config.get("_support_breaks", False):
            c = self.position_break_func(self.position,
                    created_clip, W, H, break_type, end_break_time)
        else:
            c = self.position(created_clip, W, H)
        return c



    def get_data(self, key, gps_info, gpx_index, break_type, end_break_time,
            time_in_break, W, H):
        """Gets data for this key

        Parameters
        ---------
        key : str
            Config key (elvation, speed, etc.) What do we want
        is_chart : bool
            True if we want to draw chart from this or not
        gps_info : util.GPSData
            Data to draw
        gpx_index : int
            Index in GPX points

        Returns
        ------
            gps_info[key] if is_chart is False. chart_object.make_chart_at if
            it is True
        """
        if self.config is not None and "_run_func" in  self.config:
            func_name, config = self.config["_run_func"]
            #print (func_name, self.object)
            func_name = getattr(self.object, func_name)
#TODO: This should be done at init
#FIXME: make this better
            gps_info["angle"] = gps_info["bearing"]
            object_vars = locals()
            args = {k:self._magic_value(k, v, object_vars) \
                    for k,v in config.items() if self._is_argument(k) }
            #FIXME: This is ugly as hell
#If there is a break currently and this config supports breaks
            if break_type != BreakType.NO and self.config.get("_support_breaks", False):
#We get break function
                width_f, height_f = self.config["_break_func"](
                        (self.config["map_w"], self.config["map_h"]),
                        (W, H),
                        break_type, end_break_time)
#And add the arguments
                args["img_width"] = int(round(width_f(time_in_break)))
                args["img_height"] = int(round(height_f(time_in_break)))
                #print ("WxH: {}x{}".format(args["img_width"], args["img_height"]))

            if "_DICT" in config:
                our_dict = object_vars[config["_DICT"]]
                #print (func_name, config, args)
                s = inspect.signature(func_name)
#Gets parameters from wanted function
                func_params = set(s.parameters.keys())
                both = func_params.intersection(our_dict.keys())
                #print ("BOTH:", both)
                pos_args = []
                for param_name, param in s.parameters.items():
                    if param_name in both:
                        pos_args.append(our_dict[param_name])
                #print ("POS ARGS:", pos_args)
                return func_name(*pos_args, **args)
            else:
                #print ("Calling {} with {}".format(func_name, args))
                return func_name(**args)
        return gps_info[key]

    @staticmethod
    def _is_argument(argument):
        """Clip argument is anything not starting with _
        and not class"""
        if argument.startswith("_"):
            return False
        if argument == "class":
            return False
        return True

    @staticmethod
    def _magic_value(key, value, object_vars):
        """Converts config values

        If config value starts with `__` it is transformed to the value of this
        variable in GPXDataSequence. For example `__gpx_file` is transformed to
        `/home/user/gpx.gpx` if that is the input of GPXDataSequence.
        If it also contains : value after : is the key since variable is
        assumed to be dictionary. For example __gps_info:speed is transformed
        to the speed key in gps_info dictionary.


        If key contains size and value is tuple `w` will be converted to picture
        width and `h` to picture height.

        All the other values are unchanged

        Parameters
        ---------
        key
            Config key
        value
            Config value
        object_vars : dict
            Variables and its values in GPXDataSequence
        """
        if isinstance(value, str) and value.startswith("__"):
            strip_value = value.lstrip("_")
            if ":" in strip_value:
                strip_value, strip_key = strip_value.split(":")
            else:
                strip_key = None
            if strip_value in object_vars:
                read_value = object_vars[strip_value]
                if strip_key is not None:
                    return read_value[strip_key]
                else:
                    return read_value
        elif "size" in key:
            if isinstance(value, tuple):
                out_tuple = []
                found_string = False
                for val in value:
                    if isinstance(val, str):
                        low_val = val.lower()
                        found_string = True
                        if low_val  == "w":
                            out_tuple.append(object_vars["size"][0])
                        elif low_val == "h":
                            out_tuple.append(object_vars["size"][1])
                        else:
                            raise Exception("Wrong text size: Supported " +
                                    "values  are integers and 'w', 'h' "+
                                    "Given values are {} in {}".format(value,
                                        key))
                    else:
                        out_tuple.append(val)
                if found_string:
                    return tuple(out_tuple)
        else:
            return value

    def need_init(self):
        """Checks if configs needs initialization

        Configs need initialization if class exists in config or chart_config.

        This is needed for Gauges, charts and map creation

        Returns
        ------
        bool
            True if initialization is needed
        """
        if self.config is not None:
            return "class" in self.config


    def init(self, object_vars):
        """Initializes configs

        If config or chart_config contains class with Classname. This class is
        initialized here with needed arguments and object is saved in object or
        chart_object
        """
        def get_args(config, object_vars):
            return {k:self._magic_value(k, v, object_vars) \
                    for k,v in config.items() if self._is_argument(k) }

        def init_class(config):
            if config is not None and "class" in config:
                args = get_args(config, object_vars)
                print ("CONF:", config)
                print ("ARGS:", args)
                return config["class"](**args)
        self.object = init_class(self.config)


    def __repr__(self):
        s=("{} set: {}".format(key, value!=None) for key, value in
                vars(self).items())
        return ", ".join(s)

    @property
    def config_type(self):
        return "S"

class ChartConfigItem(ConfigItem):
    """Config for chart overlay

    Basically the same as ConfigItem only config_type is different.

    Parameters
    ---------
    func : function
        No idea FIXME
    position : function
        Input parameter is created clip made with previous function and width
        and height of full image. Output is Clip set to wanted position
    config : dict
        Specific needed settings for complex overlays (map and charts for now)
    sample_value 
        Sample input value that func can create valid Clip (Used for testing
        clip locations)
    """
    def __init__(self, func=None, position=None,
            config=None, sample_value=None):
        super().__init__(func, position, config, sample_value)

    @property
    def config_type(self):
        return "C"

class GaugeConfigItem(ConfigItem):
    """Config for chart overlay

    Basically the same as ConfigItem only config_type is different.

    Parameters
    ---------
    func : function
        No idea FIXME
    position : function
        Input parameter is created clip made with previous function and width
        and height of full image. Output is Clip set to wanted position
    config : dict
        Specific needed settings for complex overlays (map and charts for now)
    sample_value 
        Sample input value that func can create valid Clip (Used for testing
        clip locations)
    """
    def __init__(self, func=None, position=None,
            config=None, sample_value=None):
        super().__init__(func, position, config, sample_value)

    @property
    def config_type(self):
        return "G"

