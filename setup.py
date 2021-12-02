from pathlib import Path

from setuptools import setup

setup(
    name='llconfig',
    version='2.0.1',
    packages=['llconfig'],
    license='Apache 2.0',
    author='Heureka.cz',
    author_email='vyvoj@heureka.cz',
    description='Lightweight layered configuration library.',
    long_description=Path(__file__).with_name('README.md').read_text(encoding='utf-8'),
    long_description_content_type='text/markdown',
    url='https://github.com/heureka/llconfig',
)
