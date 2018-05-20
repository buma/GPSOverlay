from .lib.exif import EXIF
from joblib import Memory

#TODO: make configurable
cachedir = "/var/tmp/overlay"
memory = Memory(cachedir=cachedir, verbose=0)


@memory.cache
def exif_fields(filename):
    exif = EXIF(filename)
    geo_data = exif.extract_geo()
    exif_time = exif.extract_capture_time()
    bearing = exif.extract_direction()
    return geo_data, exif_time, bearing

#Doesn't work
def configure(cachedir_config):
    global cachedir, memory
    cachedir = cachedir_config
    memory = Memory(cachedir=cachedir, verbose=1)
    #exif_fields = memory.cache(exif_fields)
    print(memory)
