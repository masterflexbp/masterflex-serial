"""Setup configuration for MasterflexSerial module."""
import os
import sys

from setuptools import find_packages, setup
here = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, here)

requirements_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')

with open(requirements_path) as requirements_file:
    requirements = requirements_file.readlines()


config = dict(
    classifiers=[
        'Environment :: Console',
        'License :: New-BSD',
        'Operating System :: POSIX :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8 or above',
    ],
    # Necessary for `python setup.py install` to find internal packages.
    dependency_links=[
        # '<repo>/some-other-pkg@<branch>#egg=some-other-pkg'
    ],
    description='Masterflex Serial communication.',
    install_requires=requirements,
    license='New BSD',
    name='masterflex-serial',
    packages=find_packages(),
    test_suite='tests',
    url='https://github.com/masterflexbp/masterflex-serial.git',
    version='0.1.0',
    zip_safe=False,
)

# Allow this module to be imported without actually running setup()
if __name__ == '__main__':
    setup(**config)
