try:
    from setuptools import setup
except:
    from distutils.core import setup

setup(
    name='gtaskcli',
    version='1.2.0',
    author='Neal Fultz',
    author_email='nfultz@gmail.com',
    url='https://github.com/nfultz/gtaskcli',
    py_modules=['gtaskcli'],
    entry_points={
        'console_scripts': [
            'gt = gtaskcli:_main',
        ],
    },
)
