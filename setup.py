import setuptools

with open("README.md", "r") as f:
    long_desc = f.read()

setuptools.setup(
    name="depstack",
    version="0.0.1",
    author="Eero Talus",
    author_email="eero@talus.cc",
    description="Easily deploy Docker Swarm stacks with dependencies.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/eerotal/depstack",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD 3-clause license",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=[
        "schema>=0.7.4",
        "pyaml>=20.4.0"
    ],
    entry_points={
        "console_scripts": [
            "depstack = depstack.main:entrypoint"
        ]
    }
)
