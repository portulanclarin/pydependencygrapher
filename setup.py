from setuptools import setup
from os import path
import re


def packagefile(*relpath):
    return path.join(path.dirname(__file__), *relpath)


def read(*relpath):
    with open(packagefile(*relpath)) as f:
        return f.read()


def get_version(*relpath):
    match = re.search(
        r'''^__version__ = ['"]([^'"]*)['"]''',
        read(*relpath),
        re.M
    )
    if not match:
        raise RuntimeError('Unable to find version string.')
    return match.group(1)


setup(
    name='pydependencygrapher',
    version=get_version('pydependencygrapher.py'),
    description='Draws dependency graphs.',
    long_description=read('README.rst'),
    url='https://github.com/joaoantonioverdade/pydependencygrapher',
    author='João Rodrigues',
    author_email='joao.rodrigues@di.fc.ul.pt',
    py_modules=['pydependencygrapher'],
    install_requires=[
        "pycairo",
    ],
    entry_points={
        'console_scripts': [
            'pydependencygrapher=pydependencygrapher:main',
        ],
    },
    include_package_data=True,
)
