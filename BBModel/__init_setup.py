try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension('BBModel',
        ['__init__.py'],
        #['tide.py', 'river.py', 'station.py', '__init__.py'],
        include_dirs = ['C:/Program Files/Python27/Lib/site-packages/Cython/Includes/cpython'],
        )
]

setup(
    name = 'BBModel',
    ext_modules = cythonize(extensions),
)
