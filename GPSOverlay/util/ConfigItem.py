
class ConfigItem(object):
    """Config for one overlay

    One overlay is one data shown (datetime, speed, speed gauge, elevation
    chart, map display)

    To create it we need to have function which creates Clip from GPS data and
    function which sets position based on whole clip size and generated clip
    size.

    We can have simple overlays which just show value (like speed, elevation,
    slop, heart rate, etc.)
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
    chart_func : function
        No idea FIXME
    chart_position : function
        Input parameter is created clip made with previous function and width
        and height of full image. Output is Clip set to wanted position
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
    def __init__(self, func=None, position=None, chart_func=None,
            chart_position=None, config=None, chart_config=None,
            sample_value=None):
        self.func = func
        self.position = position
        self.chart_func = chart_func
        self.chart_position = chart_position
        self.config = config
        self.chart_config = chart_config
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

    def get_clip(self, key, is_chart, gps_info, gpx_index, W, H):
        """Fully creates clip

        Gets data( self.get_data), runs function (self.func) and sets position
        (self.position)

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
        W : int
            Width of full picture
        H : int
            Height of full picture

        Returns
        ------
        moviepy.Clip 
            Clip generated from data set on correct position or None if clip
            couldn't be created
        """
        name = ""
        if is_chart:
            name = "chart_"
        data = self.get_data(key, is_chart, gps_info, gpx_index)
        if data is None:
            return None
        created_clip = getattr(self, name+"func")(data)
        if created_clip is None:
            return None
        c = getattr(self, name+"position")(created_clip, W, H)
        return c



    def get_data(self, key, is_chart, gps_info, gpx_index):
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
        if is_chart:
            return self.chart_object.make_chart_at(gpx_index)
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
            if strip_value in object_vars:
                return object_vars[strip_value]
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
        class_init = False
        if self.config is not None:
            class_init = "class" in self.config
        if self.chart_config is not None:
            return class_init or "class" in self.chart_config
        return class_init


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
        self.chart_object = init_class(self.chart_config)


    def __repr__(self):
        s=("{} set: {}".format(key, value!=None) for key, value in
                vars(self).items())
        return ", ".join(s)
