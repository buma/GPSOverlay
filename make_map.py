import glob
import time
import os
import concurrent.futures
import multiprocessing
from tqdm import tqdm

from GPXDataSequence import GPXDataSequence
from MapnikRenderer import MapnikRenderer, MapnikMultiProcessRenderer

partial = True

def get_frames(filematch):
    sort = sorted(glob.glob(filematch))
    if partial:
        return sort[:220]
    return sort
map_w = 500
map_h = 500
map_zoom = 18
gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx"
map_mapfile="/home/mabu/Documents/MapBox/project/openstreetmap-carto1/openstreetmap-carto.xml"
maps_cache = "./.map_cache1"
fps=8
frames = get_frames("/data2/snemanje/miklavz/original/1/changed/*.JPG")

gpx_seq = GPXDataSequence(frames[4:24], fps, with_mask=False,
        gpx_file="/data2/snemanje/miklavz/2017-04-22_15-38-20.gpx",
       time_offset=944, map_w=map_w, map_h=map_h,
       zoom=map_zoom)




    #break
#start = time.process_time()
#list(map(get_map_image, gpx_list))
#print ("Rendering took %r s" % (time.process_time()-start,))
#Rendering took 8.732729653 s 30 sec
#time Rendering took 8.688216239 s 30 sec

#start = time.time()
#with concurrent.futures.ThreadPoolExecutor() as executor:
    #result = executor.map(get_map_image, gpx_list)
#print ("Rendering took %r s" % (time.time()-start,))
#Rendering took 9.372126215 s 21 secs
#time Rendering took 22.155088186264038 s 20 secs

#This is easiest and fastest mode, problem is that mapnik should be separate
#for each thread

#start = time.time()
#with concurrent.futures.ProcessPoolExecutor() as executor:
    #result = executor.map(get_map_image, gpx_list)
#print ("Rendering took %r s" % (time.time()-start,))
#Rendering took 0.016096673999999922 s 7 secs
#time Rendering took 8.810177087783813 s 7 secs
#Rendering took 2.9466331005096436 s after moving style loading to own function

#Process just monitors queue and updates progress bar
def monitor(queue, fullsize):
    with tqdm(total=fullsize, unit='map render') as pbar:
        size = queue.qsize()
        prevdone = 0
        while size >= 0:
            done = fullsize-size
            #print ("MONITOR: %d items in queue %d done" % (size,fullsize-size))
            pbar.update(done-prevdone)
            if size == 0:
                break
            prevdone = done
            #time.sleep(0.5)
            size = queue.qsize()

queue = multiprocessing.JoinableQueue()
result_queue = multiprocessing.Queue()

print ("Starting:")
num_consumers = multiprocessing.cpu_count()
print ("Made %d consumers" % (num_consumers, ))
consumers = [MapnikMultiProcessRenderer(queue, result_queue,
    map_w, map_h, gpx_file, map_zoom, maps_cache) for i in
        range(num_consumers)]

for idx, gps in enumerate(gpx_seq.gpx_data):
    queue.put((idx, gps.lat, gps.lon, gps.bearing))
#If number is in queue it prints number of items
    #if idx %10 == 0:
        #for i in range(num_consumers):
            #queue.put(42)

#On none consumers stop working
for i in range(num_consumers):
    queue.put(None)

monitor_p = multiprocessing.Process(target=monitor, args=(queue,queue.qsize()))

#print ("QUEUE:", queue.qsize())
start = time.time()
for c in consumers:
    c.start()
monitor_p.start()

queue.join()
monitor_p.join()
print ("Rendering took %r s" % (time.time()-start,))

for i in range(num_consumers):
    stat = result_queue.get()
    print (stat)

#Rendering took 2.60990834236145 s
