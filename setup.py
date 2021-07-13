from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

NDV = "0.67.0"

driver_dep = [f'naas_drivers=={NDV}']
dev_dep = [
    "syncer==1.3.0",
    "backports.zoneinfo==0.2.1",
    "pytest==6.2.4",
    "pytest-tornasync==0.6.0.post2",
    "pytest-mock==3.6.0",
    "pytest-sanic==1.7.0",
    "pytest-asyncio==0.15.1",
    "requests-mock==1.9.2",
    "twine==3.4.1",
    "flake8==3.9.1",
    "pre-commit==2.12.1",
    "black==21.5b1",
    "imgcompare==2.0.1",
    "commitizen==2.17.4",
    "pytest-cov==2.11.1",
]
setup(
    name="naas",
    version="1.18.1b2",
    author="Martin Donadieu",
    author_email="martindonadieu@gmail.com",
    license="BSD",
    description="Scheduler system for notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cashstory/naas",
    packages=find_packages(exclude=["tests"]),
    package_data={
        "naas": ["runner/assets/*.html", "runner/assets/*.png", "runner/assets/*.svg"],
    },
    setup_requires=["wheel"],
    extras_require={
        "dev": dev_dep,
        'full': driver_dep,
        "fulldev": dev_dep + driver_dep
    },
    install_requires=[
        "nbconvert==6.0.7",
        "nest_asyncio==1.5.1",
        "ipywidgets==7.6.3",
        "papermill==2.3.3",
        "pretty-cron==1.2.0",
        "APScheduler==3.7.0",
        "pycron==3.0.0",
        "aiohttp==3.7.4",
        "html5lib==1.1",
        "Pillow==8.2.0",
        "markdown2==2.4.0",
        "pandas==1.2.4",
        "escapism==1.0.1",
        "notebook==6.4.0",
        "ipython==7.23.1",
        "ipykernel==5.5.3",
        "requests==2.25.1",
        "sentry-sdk==1.0.0",
        "sanic==20.12.2",
        "sanic-openapi==0.6.2",
        "argparse==1.4.0",
        "nbclient==0.5.3",
        "beautifulsoup4==4.9.3",
        "tzdata",
        "pysqlite3==0.4.6",
        "pymongo[srv]==3.11.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: BSD License",
        "Framework :: Jupyter",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering",
    ],
)
