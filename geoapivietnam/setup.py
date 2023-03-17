from setuptools import setup, find_packages

setup(
    name='geoapivietnam',
    version='0.1.0',
    description='A short description of your module',
    author='Tran Ngoc Minh Hieu',
    author_email='tnmhieu@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'requests',
        'geopy',
        'tenacity',
        'unidecode',
        'geoapivietnam @ git+ssh://git@github.com/tranngocminhhieu/geo-api-vietnam.git#egg=geoapivietnam-0.1.0'
    ],


    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ]
)