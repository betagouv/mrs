import pip
from setuptools import setup, find_packages, Command
import os, sys

with open('requirements.txt') as reqs_file:
    install_reqs = reqs_file.readlines()

setup(
    name='mrs',
    version='0.0.0',
    description='foo',
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://github.com/betagouv/mrs',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license = 'MIT',
    install_requires = install_reqs,
    entry_points = {
        'console_scripts': [
            'mrs = mrs.manage:main',
        ],
    },
    classifiers = [
        'Development Status :: 1 - Planning',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
