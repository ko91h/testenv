#!/usr/bin/python

from setuptools import setup
setup(
    name = "testenv",
    version = "0.11",
    packages = ['testenv', 'testenv.contrib'],
    scripts = ['scripts/testenv'],
    author = "Dmitry Smal",
    author_email = "mialinx@gmail.com",
    description = "Tool to setup test environment for unit tests",
    license = "MIT",
    url = "https://github.com/ko91h/testenv",
    install_requires=[
        "PyYAML == 3.11",
        "six >= 1.10.0",
    ]
)
