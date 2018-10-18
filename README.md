GPS Data overlay for image sequences and videos
===============================

version number: 0.0.4
author: Marko Burjek

Overview
--------

A python package that can be installed with pip.

It can add data overlays to sequence of images or video. Similar to Garmin Virb editor.

It needs GPX file video/image sequence and time offset from imageSequence times and GPX file.
Those can be:
- text speed/slope/elevation/date time/heart rate
- chart speed/slope/elevation/heart rate
- Gauges made from SVG for speed/slope/elevation/heart rate
- map OpenStreetmap of current location map is rendered locally so postgresql, mapnik and render style

It is also possible to create full video with this:
- list of images + titles makes a slideshow clip with fade transitions between them
- Start/end titles etc.

It is currently little hard to configure since I haven't found good way to configure it

Installation / Usage
--------------------

To install use pip:

    $ pip install GPSOverlay


Or clone the repo:

    $ git clone https://github.com/buma/GPSOverlay.git
    $ python setup.py install
    
Contributing
------------

TBD

Example
-------

TBD
