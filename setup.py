import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="otree_manager",
    version="0.0.1",
    author="Christian König-Kersting",
    author_email="koenig.kersting@gmail.com",
    description="A manager for containerized, multi-user oTree installations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chkgk/otree_manager",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)