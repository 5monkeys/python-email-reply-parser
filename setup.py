#!/usr/bin/env python

from setuptools import setup, find_packages

import email_reply_parser

setup(
    name='python-email-reply-parser',
    version=".".join(map(str, email_reply_parser.__version__)),
    author='Anton Agestam',
    author_email="msn@antonagestam.se",
    url='https://github.com/antonagestam/python-email-reply-parser',
    description='Python port of https://github.com/github/email_reply_parser',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
    ],
)
