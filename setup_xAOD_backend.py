# setuptools loads some plugins necessary for use here.
from setuptools import find_packages  # noqa: F401
from distutils.core import setup
from version_info import version_func_adl_xaod_backend, version_func_adl_xaod

# Use the readme as the long description.
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="func_adl_xAOD.backend",
      version=version_func_adl_xaod_backend,
      packages=['func_adl_xAOD/backend'] + [f'func_adl_xAOD/backend.{f}' for f in ['cpplib', 'dataset_resolvers', 'xAODlib']],
      scripts=[],
      description="Backend to generate and run C++ files for Functional Analysis Description Language for accessing ATLAS xAOD files.",
      long_description=long_description,
      long_description_content_type="text/markdown",
      author="G. Watts (IRIS-HEP/UW Seattle)",
      author_email="gwatts@uw.edu",
      maintainer="Gordon Watts (IRIS-HEP/UW Seattle)",
      maintainer_email="gwatts@uw.edu",
      url="https://github.com/iris-hep/func_adl_xAOD",
      license="TBD",
      test_suite="tests",
      python_requires='>=3.7, <3.8',
      install_requires=[
          'jinja2',
          f"func_adl_xAOD=={version_func_adl_xaod}",
      ],
      classifiers=[
          "Development Status :: 3 - Alpha",
          # "Development Status :: 4 - Beta",
          # "Development Status :: 5 - Production/Stable",
          # "Development Status :: 6 - Mature",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.7",
          "Topic :: Software Development",
          "Topic :: Utilities",
      ],
      package_data={
          'func_adl_xAOD/backend': ['R21Code/*'],
      },
      platforms="Any",
      )
