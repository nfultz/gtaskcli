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
    python_requires='>=3',
    install_requires=[
          'google-api-python-client>=1.4',
          'httplib2',
          'oauth2client',
      ],
    entry_points={
        'console_scripts': [
            'gtaskcli = gtaskcli:_main',
        ],
    },
)
