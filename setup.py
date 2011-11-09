from distutils.core import setup

VERSION = __import__('loci').__version__


setup(
    name='django-loci',
    version=VERSION,
    author='Midwest Communications',
    description='Place Management and Geolocation App',
    url='https://github.com/MidwestCommunications/django-loci',
    packages=['loci']
)
