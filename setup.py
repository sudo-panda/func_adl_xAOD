# setuptools loads some plugins necessary for use here.
import os
from distutils.core import setup

from version_info import version_func_adl

# Use the readme as the long description.
with open("README.md", "r") as fh:
    long_description = fh.read()

# Get the version number right
version = os.getenv('func_adl_xaod_version')
if version is None:
    version = '0.0.0-alpha.10'
else:
    version = version.split('/')[-1]

# Finally, the setup.
setup(name="func_adl_xAOD",
      version=version,
      packages=['func_adl_xAOD'] + [f'func_adl_xAOD.{f}' for f in ['atlas.xaod', 'cms.aod', 'common']],
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
              'asyncmock',
              "pandas~=1.0",
              "uproot~=3.7",
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
          'func_adl_xAOD': ['template/atlas/r21/*', 'template/cms/r5/*'],
      },
      platforms="Any",
      )
