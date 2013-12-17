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
              'issues/update = tpv.github.cli.issues:Update',
              'issues/comments = tpv.github.cli.issues:Comments',
              'issues/comments/list = tpv.github.cli.issues:CommentsList',
              'issues/comments/add = tpv.github.cli.issues:CommentsAdd',
              'issues/comments/update = tpv.github.cli.issues:CommentsUpdate',
              'issues/comments/remove = tpv.github.cli.issues:CommentsRemove',
              'pulls = tpv.github.cli.pullrequests:Pulls',
              'pulls/list = tpv.github.cli.pullrequests:List',
              'pulls/show = tpv.github.cli.pullrequests:Show',
              'pulls/add = tpv.github.cli.pullrequests:Add',
              'pulls/update = tpv.github.cli.pullrequests:Update',
              'pulls/comments = tpv.github.cli.pullrequests:Comments',
              'pulls/comments/list = tpv.github.cli.pullrequests:CommentsList',
              'pulls/comments/add = tpv.github.cli.pullrequests:CommentsAdd',
              'pulls/comments/update = tpv.github.cli.pullrequests:CommentsUpdate',
              'pulls/comments/remove = tpv.github.cli.pullrequests:CommentsRemove',
              'repos = tpv.github.cli.repos:Repos',
              'repos/list = tpv.github.cli.repos:List',
              'repos/add = tpv.github.cli.repos:Add',
              'repos/update = tpv.github.cli.repos:Update',
              'user = tpv.github.cli.user:User',
              'user/show = tpv.github.cli.user:Show',
              'user/update = tpv.github.cli.user:Update',
              'org = tpv.github.cli.org:Org',
              'org/show = tpv.github.cli.org:Show',
              'org/update = tpv.github.cli.org:Update',
              'org/members = tpv.github.cli.org:Members',
              'org/members/list = tpv.github.cli.org:MemList',
              'org/members/add = tpv.github.cli.org:MemAdd',
              'org/members/remove = tpv.github.cli.org:MemRemove',
              'org/teams = tpv.github.cli.org:Teams',
              'org/teams/list = tpv.github.cli.org:TeamsList',
              'org/teams/show = tpv.github.cli.org:TeamsShow',
              'org/teams/add = tpv.github.cli.org:TeamsAdd',
              'org/teams/remove = tpv.github.cli.org:TeamsRemove',
              'org/teams/repos = tpv.github.cli.org:TeamsRepos',
              'org/teams/repos/list = tpv.github.cli.org:TeamsReposList',
              'org/teams/repos/add = tpv.github.cli.org:TeamsReposAdd',
              'org/teams/repos/remove = tpv.github.cli.org:TeamsReposRemove',
          ],
      },
      )
