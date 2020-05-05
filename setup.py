""""
SYSTEM REQUIREMENTS:
The following Centos packages are required for M2Crypto:
python3-devel openssl-devel swig gcc-c++
"""

# A setuptools based setup module. See:
# https://packaging.python.org/guides/distributing-packages-using-setuptools/
# https://github.com/pypa/sampleproject

from setuptools import setup, find_namespace_packages
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


# python2 setup
# setup(
#     name='fts3-rest',
#     version='3.10.0',
#     description='FTS3 Python Libraries',
#     long_description='FTS3 Python Libraries',
#     author='FTS3 Developers',
#     author_email='fts-devel@cern.ch',
#     url='http://fts.web.cern.ch/',
#     download_url='https://gitlab.cern.ch/fts/fts-rest',
#     license='Apache 2',
#     packages=['fts3', 'fts3.cli', 'fts3.model', 'fts3.rest', 'fts3.rest.client', 'fts3.rest.client.easy'],
#     package_dir={'fts3': os.path.join(base_dir, 'src', 'fts3')},
#     scripts=glob(os.path.join(base_dir, 'src', 'cli', 'fts-*')),
#     keywords='fts3, grid, rest api, data management clients',
#     platforms=['GNU/Linux'],
#     classifiers=[
#         "Intended Audience :: Developers",
#         "Topic :: Software Development :: Libraries :: Python Modules",
#         "License :: OSI Approved :: Apache Software License",
#         "Development Status :: 5 - Production/Stable",
#         "Operating System :: Unix",
#         "Programming Language :: Python"
#     ],
#
#     install_requires=['M2Crypto>=0.16', 'pycurl%s' % pycurl_ver, 'requests']
# )
