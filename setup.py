"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""
from setuptools import setup, find_namespace_packages
from os import path
from glob import glob

here = path.abspath(path.dirname(__file__))

# this is not really needed for this package
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
    name="fts-rest-py3",  # Required
    version="0.1",  # Required
    description="FTS Python3 CLI and libraries",  # Optional
    url="https://gitlab.cern.ch/fts/fts-rest-flask",  # Optional
    author="CERN -- FTS team",  # Optional
    author_email="fts-devel@cern.ch",  # Optional
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    package_dir={"": "src"},  # Optional
    packages=[
        "fts3",
        "fts3.rest",
        "fts3.cli",
        "fts3.rest.client",
        "fts3.rest.client.easy",
    ],  # Required
    python_requires=">=3.6",
    install_requires=["M2Crypto", "requests"],  # Optional
    scripts=glob(path.join(here, "src", "cli", "fts-*")),
)

# The following OS packages are required for M2Crypto:
# python3-devel openssl-devel swig gcc gcc-c++ make
