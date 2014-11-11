import os
from distutils.core import setup


def is_package(path):
    """Does path contain packages"""
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
    )


def find_packages(path, base=""):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir_ = os.path.join(path, item)
        if is_package(dir_):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir_
            packages.update(find_packages(dir_, module_name))
    return packages


required_packages = ['Flask',
                     'requests',
                     'SQLAlchemy',
                     'lxml',
                     'six']

if 'REDISCLOUD_URL' in os.environ \
        and 'REDISCLOUD_PORT' in os.environ \
        and 'REDISCLOUD_PASSWORD' in os.environ:
    required_packages.append('django-redis-cache')
    required_packages.append('hiredis')


setup(name='HaodooScraper-Flask',
      version='1.0',
      description='HaodooScraper - Scraper and Web App',
      author='elleryq',
      author_email='elleryq@gmail.com',
      url='https://github.com/elleryq/haodooscraper',
      install_requires=required_packages,
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3",
      ],
      #scripts=['scraper.py'],
      packages=find_packages("."),
      )
