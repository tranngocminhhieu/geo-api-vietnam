from setuptools import setup

setup(
    name='geoapivietnam',
    version='0.2.0',
    description='Geo API for Vietnam module',
    url='https://github.com/tranngocminhhieu/geo-api-vietnam',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=['src/geoapivietnam'],
    package_data={'geoapivietnam': ['data/*']},
    install_requires=[
        'pandas',
        'requests',
        'geopy',
        'tenacity',
        'unidecode',
        'openpyxl'
    ]
)