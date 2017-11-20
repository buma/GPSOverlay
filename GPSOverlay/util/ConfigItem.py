
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
            chart_position=None, config=None, sample_value=None):
        self.func = func
        self.position = position
        self.chart_func = chart_func
        self.chart_position = chart_position
        self.config = config
        self.sample_value = sample_value

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

    def __repr__(self):
        s=("{} set: {}".format(key, value!=None) for key, value in
                vars(self).items())
        return ", ".join(s)
