from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name='geoapivietnam',
    version='0.1.0',
    description='A short description of your module',
    url='https://github.com/tranngocminhhieu/geo-api-vietnam',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'requests',
        'geopy',
        'tenacity',
        'unidecode'
    ],
    zip_safe=False
)