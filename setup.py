import pip
from setuptools import setup, find_packages, Command
import os, sys

install_reqs = pip.req.parse_requirements(
    os.path.join(
        os.path.dirname(__file__),
        'requirements.txt'
    ),
    session=pip.download.PipSession()
)

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
    install_requires = [str(ir.req) for ir in install_reqs],
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
