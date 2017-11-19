from setuptools import setup, find_packages
from codecs import open
from os import path

__version__ = '0.0.3'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = filter(lambda x: not x.startswith("#"), f.read().strip().split("\n"))

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name='GPSOverlay',
    version=__version__,
    description='A python package that can be installed with pip.',
    long_description=long_description,
    url='https://github.com/buma/GPSOverlay',
    download_url='https://github.com/buma/GPSOverlay/tarball/' + __version__,
    license='BSD',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='',
    packages=find_packages(exclude=['docs', 'tests*']),
    include_package_data=True,
    author='Marko Burjek',
    install_requires=install_requires,
    extras_require={
        'Charts': ["matplotlib==2.1.0"],
        'Gauges': ["cairocffi==0.8.0", "CairoSVG==2.1.1", "svgutils==0.3.0"],
        'map': ["pyproj==1.9.5.1", "mapnik==0.1"]
        },
    dependency_links=dependency_links,
    author_email='email4marko@gmail.com'
)
