import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='naas',
    version='0.0.1',
    scripts=['scripts/naas'] ,
    author="Martin Donadieu",
    author_email="martindonadieu@gmail.com",
    description="scheduler system for notebooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cashstory/naas",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)