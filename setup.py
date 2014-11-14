import os
from setuptools import setup, find_packages

required_packages = ['Flask',
                     'Flask-JsonTools',
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
