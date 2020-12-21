# setuptools loads some plugins necessary for use here.
from setuptools import find_packages  # noqa: F401
from distutils.core import setup
from os import listdir
from version_info import version_func_adl

# Use the readme as the long description.
with open("README.md", "r") as fh:
    long_description = fh.read()

xaod_template_files = listdir('func_adl_xAOD/R21Code')
setup(name="func_adl_xAOD",
      version='0.0.0-alpha.10',
      packages=['func_adl_xAOD'] + [f'func_adl_xAOD.{f}' for f in ['cpplib', 'datasets', 'xAODlib']],
      scripts=[],
      description="Functional Analysis Description Language backend for accessing ATLAS xAOD files.",
      long_description=long_description,
      long_description_content_type="text/markdown",
      author="G. Watts (IRIS-HEP/UW Seattle)",
      author_email="gwatts@uw.edu",
      maintainer="Gordon Watts (IRIS-HEP/UW Seattle)",
      maintainer_email="gwatts@uw.edu",
      url="https://github.com/iris-hep/func_adl_xAOD",
      license="TBD",
      test_suite="tests",
      install_requires=[
          "requests~=2.0",
          "pandas~=1.0",
          "uproot~=3.7",
          "retry~=0.9",
          "jinja2",
          "qastle",
          f"func_adl.ast{version_func_adl}",
      ],
      extras_require={
          'test': [
              'pytest>=3.9',
              'pytest-asyncio',
              'pytest-mock',
              'pytest-cov',
              'coverage',
              'flake8',
              'codecov',
              'autopep8',
              'twine',
              'testfixtures',
              'wheel',
              'asyncmock'
          ],
      },
      classifiers=[
          "Development Status :: 3 - Alpha",
          # "Development Status :: 4 - Beta",
          # "Development Status :: 5 - Production/Stable",
          # "Development Status :: 6 - Mature",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Programming Language :: Python",
          "Topic :: Software Development",
          "Topic :: Utilities",
      ],
      package_data={
          'func_adl_xAOD': ['R21Code/*'],
      },
      platforms="Any",
      )
