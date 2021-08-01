from setuptools import setup
from Cython.Build import cythonize

setup(
    name='cy_netlink',
    ext_modules = cythonize("cy_netlink.pyx", language_level = "3"),
    zip_safe=False,
)
