from pathlib import Path
from setuptools import setup

README = (Path(__file__).parent / "README.md").read_text()

setup(
    name='geoapivietnam',
    version='0.2.7',
    description='Optimized Geo API for Vietnam',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/tranngocminhhieu/geo-api-vietnam',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=['geoapivietnam'],
    package_data={'geoapivietnam': ['data/*']},
    install_requires=[
        'pandas',
        'requests',
        'geopy',
        'tenacity',
        'unidecode',
        'openpyxl',
        'appdirs'
    ]
)