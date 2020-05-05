""""
SYSTEM REQUIREMENTS:
The following Centos packages are required for M2Crypto:
python3-devel openssl-devel swig gcc-c++
"""

# A setuptools based setup module. See:
# https://packaging.python.org/guides/distributing-packages-using-setuptools/
# https://github.com/pypa/sampleproject

from setuptools import setup
from os import path
from glob import glob

here = path.abspath(path.dirname(__file__))

# Arguments marked as "Required" below must be included for upload to PyPI.
setup(
    name="fts-client-py3",  # Required
    version="1",  # Required
    description="FTS Python3 CLI and libraries",  # Optional
    url="https://gitlab.cern.ch/fts/fts-rest-flask",  # Optional
    author="CERN -- FTS team",  # Optional
    author_email="fts-devel@cern.ch",  # Optional
    classifiers=[  # Optional
        "Development Status :: 4 - Beta",
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
