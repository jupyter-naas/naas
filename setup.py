from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="naas",
    version="0.0.21",
    scripts=["scripts/naas"],
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
    tests_require=[
        "pytest==5.2",
        "pytest-sanic==1.6.1",
        "requests-mock==1.8.0",
        "twine==3.2.0",
        "flake8==3.1.1",
        "black==20.8b1",
        "commitizen==2.4.0",
    ],
    install_requires=[
        "versioneer",
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
