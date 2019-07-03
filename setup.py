
from setuptools import setup, find_packages
from cranberry.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='cranberry',
    version=VERSION,
    description='OAuth 2.0 Authentication Service',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Sayyed Alireza Hoseini',
    author_email='alireza.hosseini@zoodroom.com',
    url='https://github.com/johndoe/myapp/',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'cranberry': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        cranberry = cranberry.main:main
    """,
)
