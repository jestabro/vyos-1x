from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("cy_netlink.pyx", language_level = "3")
)
