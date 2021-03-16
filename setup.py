from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="naas",
    version="1.5.0",
    scripts=["scripts/naas"],
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
        "dev": [
            "syncer==1.3.0",
            "backports.zoneinfo==0.2.1",
            "pytest==6.2.1",
            "pytest-tornasync==0.6.0.post2",
            "pytest-mock==3.5.1",
            "pytest-sanic==1.7.0",
            "pytest-asyncio==0.14.0",
            "requests-mock==1.8.0",
            "twine==3.3.0",
            "flake8==3.8.4",
            "pre-commit==2.11.1",
            "black==20.8b1",
            "imgcompare==2.0.1",
            "commitizen==2.16.0",
            "pytest-cov==2.11.1",
        ]
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
        "Pillow==8.1.2",
        "markdown2==2.4.0",
        "pandas==1.2.3",
        "escapism==1.0.1",
        "notebook==6.2.0",
        "ipython==7.21.0",
        "ipykernel==5.5.0",
        "requests==2.25.1",
        "sentry-sdk==1.0.0",
        "sanic==20.12.2",
        "sanic-openapi==0.6.2",
        "argparse==1.4.0",
        "nbclient==0.5.3",
        "beautifulsoup4==4.9.3",
        "tzdata"
    ],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: BSD License",
        "Framework :: Jupyter",
        "Operating System :: OS Independent",
    ],
)
