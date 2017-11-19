
class ConfigItem(object):
    def __init__(self, func=None, position=None, chart_func=None,
            chart_position=None, config=None, sample_value=None):
        self.func = func
        self.position = position
        self.chart_func = chart_func
        self.chart_position = chart_position
        self.config = config
        self.sample_value = sample_value

    def sample(self, clip):
        if callable(self.sample_value):
            return self.sample_value(clip, self.config)
        return self.sample_value

    def __repr__(self):
        s=("{} set: {}".format(key, value!=None) for key, value in
                vars(self).items())
        return ", ".join(s)
