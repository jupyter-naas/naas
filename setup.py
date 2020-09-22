from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import os

class FixUvloop():
    def __init__(self):
        try :
            import uvloop
            with open(uvloop.__file__, 'w') as fp:
                fp.write("raise ImportError\n")
                pass
        except ImportError:
            pass
        
class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        FixUvloop()
        
class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        FixUvloop()

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='naas',
    version='0.0.14',
    scripts=['scripts/naas'],
    author="Martin Donadieu",
    author_email="martindonadieu@gmail.com",
    description="scheduler system for notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cashstory/naas",
    packages=find_packages(exclude=["tests"]),
    package_data={
        "naas": ["runner/html/*.html", "runner/assets/*.png"],
    },
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    install_requires=[
        "papermill>=2,<3",
        "pretty-cron>=1,<2",
        "APScheduler>=3,<4",
        "pycron>=3,<4",
        "pandas>=1,<2",
        "daemonize>=2,<3",
        "escapism>=1,<2",
        "notebook>=6,<7",
        "ipython>=7,<8",
        "ipykernel>=5,<6",
        "requests>=2,<3",
        "sentry-sdk>=0,<1",
        "sanic>=20,<21",
        "sanic-openapi>=0,<1",
        "argparse>=1,<2",
        "nbconvert>=6,<7",
        "nbclient>=0,<1",
        "beautifulsoup4>=4,<5",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
