from setuptools import setup, find_packages
import os
import sys

version = '0'
shortdesc = "Connect vortex to github's facilities"
#longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

install_requires = [
    'setuptools',
    'requests',
    'tpv',
    'tpv.cli',
]


if sys.version_info < (2, 7):
    install_requires.append('ordereddict')
    install_requires.append('unittest2')


setup(name='tpv.nix',
      version=version,
      description=shortdesc,
      #long_description=longdesc,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Software Development',
      ],
      keywords='',
      author='Florian Friesdorf',
      author_email='flo@chaoflow.net',
      url='http://github.com/chaoflownet/tpv.github',
      license='AGPLv3+',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['tpv'],
      include_package_data=True,
      zip_safe=True,
      install_requires=install_requires,
      entry_points={
          'console_scripts': ['gh = tpv.github.cli:app'],
          'tpv.github.gh.commands': [
              'issues = tpv.github.cli.issues:Issues',
              'issues/list = tpv.github.cli.issues:List',
              'issues/show = tpv.github.cli.issues:Show',
              'issues/add = tpv.github.cli.issues:Add',
              'pr = tpv.github.cli.pullrequests:Pullrequests',
              'pr/list = tpv.github.cli.pullrequests:List',
              'pr/show = tpv.github.cli.pullrequests:Show',
              'pr/add = tpv.github.cli.pullrequests:Add',
              'repos = tpv.github.cli.repos:Repos',
              'repos/list = tpv.github.cli.repos:List',
              'repos/add = tpv.github.cli.repos:Add',
              'repos/update = tpv.github.cli.repos:Update'
          ],
      },
      )
