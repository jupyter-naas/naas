from setuptools import setup, find_packages

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

with open("README.md", "r") as fh:
    long_description = fh.read()

install_reqs = parse_requirements('requirements.txt')
reqs = install_reqs

setup(
    name='naas',
    version='0.0.3',
    scripts=['scripts/naas'] ,
    author="Martin Donadieu",
    author_email="martindonadieu@gmail.com",
    description="scheduler system for notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cashstory/naas",
    packages=find_packages(),
    install_requires=reqs,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)