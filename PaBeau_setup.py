try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
from Cython.Build import cythonize

#import datetime

extensions = [
    Extension('PaBeau',
        ['PaBeau.py'],
        include_dirs = ['C:/Program Files/Python27/Lib/site-packages/Cython/Includes/cpython'],
        )
]

setup(
    name = 'PaBeau',
    ext_modules = cythonize(extensions),
)
