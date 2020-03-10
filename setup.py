import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="icepyx",
    version="0.0.1",
    author="The icepyx Developers",
    author_email="jbscheick@gmail.com",
    maintainer="Jessica Scheick",
    maintainer_email=author_email,
    description="Python tools for obtaining and working with ICESat-2 data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/icesat2py/icepyx.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning",
        
    ],
)