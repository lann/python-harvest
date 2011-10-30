from distutils.core import setup
import sys

sys.path.append('harvest')
import harvest

NAME = 'harvest'

setup(
    name=NAME,
    version=harvest.__version__,
    author=harvest.__author__,
    author_email=harvest.__email__,
    url='https://github.com/lann/python-harvest',
    description='Python interface to Harvest API (getharvest.com)',
    long_description=harvest.__doc__,
    package_dir={'': NAME},
    py_modules=[NAME],
    provides=[NAME],
    keywords='harvest api',
    license=harvest.__license__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )
