"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_namespace_packages
from os import path
from glob import glob

here = path.abspath(path.dirname(__file__))


def get_install_requires(pinned=False):
    packages = []
    try:
        with open("install_requires.txt") as requires_file:
            for line in requires_file:
                line = line.strip()
                if not line.startswith("#"):
                    if pinned:
                        package = line.split(" ")[0]
                    else:
                        package = line.split("==")[0]
                    packages.append(package)
    except IOError:
        raise
    return packages


# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
    name="fts-rest-flask",  # Required
    version="0.1",  # Required
    description="fts-rest in Flask and Python3",  # Optional
    url="https://gitlab.cern.ch/fts/fts-rest-flask",  # Optional
    author="CERN -- FTS team",  # Optional
    author_email="fts-devel@cern.ch",  # Optional
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Framework :: Flask",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    package_dir={"": "src"},  # Optional
    packages=find_namespace_packages(where="src"),  # Required
    python_requires=">=3.6",
    install_requires=get_install_requires(),  # Optional
    scripts=glob(path.join(here, "src", "cli", "fts-*")),
)
