from setuptools import setup, find_packages

setup(
    name='geoapivietnam',
    version='0.1.0',
    description='A short description of your module',
    url='https://github.com/tranngocminhhieu/geo-api-vietnam',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=['geoapivietnam'],
    install_requires=[
        'pandas',
        'numpy',
        'requests',
        'geopy',
        'tenacity',
        'unidecode'
    ],

    # dependency_links = ['https://github.com/tranngocminhhieu/geo-api-vietnam.git#egg=geoapivietnam']
)