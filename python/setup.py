import os
from setuptools import Extension, setup
from Cython.Build import cythonize

def packages(directory):
    return [
        _[0].replace('/','.')
        for _ in os.walk(directory)
        if os.path.isfile(os.path.join(_[0], '__init__.py'))
    ]

extensions = [
    Extension("netlink", ["vyos/cy_netlink/cy_netlink.pyx"],
        include_dirs=[...],
        libraries=[...],
        library_dirs=[...],
]

setup(
    name = "vyos",
    version = "1.3.0",
    author = "VyOS maintainers and contributors",
    author_email = "maintainers@vyos.net",
    description = ("VyOS configuration libraries."),
    license = "LGPLv2+",
    keywords = "vyos",
    url = "http://www.vyos.io",
    packages = packages('vyos'),
    ext_modules = cythonize(extensions, language_level = "3"),
    long_description="VyOS configuration libraries",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
    ],
)
