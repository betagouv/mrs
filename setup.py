from setuptools import setup, find_packages, Command
import os, sys

setup(
    name='mrs',
    version='0.0.0',
    description='foo',
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://github.com/sgmap/mrs',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    license = 'MIT',
    extras_require={
        'debug': [
            'ipdb',
        ],
        'test': [
            'freezegun',
            'pytest',
            'pytest-django',
            'pytest-cov',
            'mock',
        ],
    },
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
