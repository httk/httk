#!/usr/bin/env python

import sys, os, glob, subprocess, datetime
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
#from setuptools.command.build import build #sigh...
from distutils.command.build import build 
import distutils.spawn
from codecs import open
from os import path

# Get access to httk config and versioning info
here = path.abspath(path.dirname(__file__))
sys.path.insert(1, os.path.join(here,'src/httk/config'))
import config

buildpath = path.join(here, 'BUILD')
if os.path.exists(buildpath):
    with open(buildpath, encoding='utf-8') as f:
        buildtag = '.'+f.read()
else:
    buildtag = ''

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
   
class HttkDevelopCommand(develop):
    description = "Development installation of httk"
    def run(self):
        develop.run(self)
        # We shouldn't write any distdata here at all, keep going
        # with whatever is happening in the present directory.

class HttkInstallCommand(install):
    description = "Installation of httk"
    user_options = install.user_options + [
        ('httkroot=', None, 'Specify the directory to use as httk root.'),
    ]
    def initialize_options(self):
        install.initialize_options(self)
        self.httkroot = None
    def finalize_options(self):
        install.finalize_options(self)
    def run(self):
        install.run(self)
        f = open(os.path.join(self.install_lib,'httk','distdata.py'),'w')
        f.write('version = \"' + config.version + '\"\n')
        f.write('version_date = \"' + config.version_date + '\"\n')
        f.write('copyright_note = \"' + config.copyright_note + '\"\n')
        if self.httkroot is None:
            f.write('root = \"' + config.httk_root + '\"\n')
        else:
            f.write('root = \"' + self.httkroot + '\"\n')
        f.close()

class HttkBuildCommand(build):
    description = "Build httk"
    user_options = build.user_options + [
        ('httkroot=', None, 'Specify the directory to use as httk root.'),
    ]
    def initialize_options(self):
        build.initialize_options(self)
        self.httkroot = None
    def finalize_options(self):
        build.finalize_options(self)
    def run(self):
        build.run(self)
        f = open(os.path.join(self.build_purelib,'httk','distdata.py'),'w')
        f.write('version = \"' + config.version + '\"\n')
        f.write('version_date = \"' + config.version_date + '\"\n')
        f.write('copyright_note = \"' + config.copyright_note + '\"\n')
        if self.httkroot is None:
            f.write('root = \"' + config.httk_root + '\"\n')
        else:
            f.write('root = \"' + self.httkroot + '\"\n')
        f.close()
        
setup(
     cmdclass={
         'develop': HttkDevelopCommand,
         'install': HttkInstallCommand,
         'build': HttkBuildCommand,
    },
    
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name='httk',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=config.version + buildtag,  # Required

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='The high-thoughput toolkit: workflow, project management, storage, and data analysis for large-scale computational projects',  # Required

    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional

    # Denotes that our long_description is in Markdown; valid values are
    # text/plain, text/x-rst, and text/markdown
    #
    # Optional if long_description is written in reStructuredText (rst) but
    # required for plain-text or Markdown; if unspecified, "applications should
    # attempt to render [the long_description] as text/x-rst; charset=UTF-8 and
    # fall back to text/plain if it is not valid rst" (see link below)
    #
    # This field corresponds to the "Description-Content-Type" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-content-type-optional
    #long_description_content_type='text/x-rst',  # Optional (see note above)

    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://httk.openmaterialsdb.se',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='Rickard Armiento, et al.',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    #author_email='pypa-dev@googlegroups.com',  # Optional

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries',

        # Pick your license as you wish
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
        #'Programming Language :: Python :: 3.6',
    ],

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    keywords='high-throughput workflow project-management storage database analysis computational atomistic',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages('src',exclude=['contrib', 'docs', 'tests']),  # Required
    package_dir={'': 'src'},
    
    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    #install_requires=['peppercorn'],  # Optional

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    #extras_require={  # Optional
    #    'dev': ['check-manifest'],
    #    'test': ['coverage'],
    #},

    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    #package_data={  # Optional
    #    'httk': ['httk.cfg', 'atomistic/spacegrouputils.pkl'],
    #},

    include_package_data=True,
    
    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('httk_data', glob.glob('src/httk/*/data/*') + glob.glob('src/httk/data/*'))],  # Optional

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    # For example, the following would provide a command called `sample` which
    # executes the function `main` from this package when invoked:
    entry_points={  # Optional
        'console_scripts': [
            'httk=httk.__main__:main',
        ],
    },

    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    #project_urls={  # Optional
    #    'Bug Reports': 'https://github.com/rartino/httk/issues',
    #    #'Funding': 'https://donate.pypi.org',
    #    #'Say Thanks!': 'http://saythanks.io/to/example',
    #    'Source': 'https://github.com/rartino/httk',
    #},
)




