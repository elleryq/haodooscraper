from setuptools import setup, find_packages

setup(name='HaodooScraper-Flask',
      version='1.0',
      description='HaodooScraper - Scraper and Web App',
      author='elleryq',
      author_email='elleryq@gmail.com',
      url='https://github.com/elleryq/haodooscraper',
      install_requires=['Flask',
                        'requests',
                        'SQLAlchemy',
                        'lxml',
                        'six'],
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Programming Language :: Python :: 3",
      ],
      #scripts=['scraper.py'],
      packages=find_packages(),
      )
