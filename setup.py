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
              'issue = tpv.github.cli.issue:Issues',
              'issue/list = tpv.github.cli.issue:List',
              'issue/show = tpv.github.cli.issue:Show',
              'issue/add = tpv.github.cli.issue:Add',
              'issue/update = tpv.github.cli.issue:Update',
              'issue/comment = tpv.github.cli.issue:Comments',
              'issue/comment/list = tpv.github.cli.issue:CommentsList',
              'issue/comment/add = tpv.github.cli.issue:CommentsAdd',
              'issue/comment/update = tpv.github.cli.issue:CommentsUpdate',
              'issue/comment/remove = tpv.github.cli.issue:CommentsRemove',
              'pull = tpv.github.cli.pullrequest:Pulls',
              'pull/list = tpv.github.cli.pullrequest:List',
              'pull/show = tpv.github.cli.pullrequest:Show',
              'pull/add = tpv.github.cli.pullrequest:Add',
              'pull/update = tpv.github.cli.pullrequest:Update',
              'pull/comment = tpv.github.cli.pullrequest:Comments',
              'pull/comment/list = tpv.github.cli.pullrequest:CommentsList',
              'pull/comment/add = tpv.github.cli.pullrequest:CommentsAdd',
              'pull/comment/update = tpv.github.cli.pullrequest:CommentsUpdate',
              'pull/comment/remove = tpv.github.cli.pullrequest:CommentsRemove',
              'repo = tpv.github.cli.repo:Repos',
              'repo/list = tpv.github.cli.repo:List',
              'repo/add = tpv.github.cli.repo:Add',
              'repo/update = tpv.github.cli.repo:Update',
              'user = tpv.github.cli.user:User',
              'user/show = tpv.github.cli.user:Show',
              'user/update = tpv.github.cli.user:Update',
              'org = tpv.github.cli.org:Org',
              'org/show = tpv.github.cli.org:Show',
              'org/update = tpv.github.cli.org:Update',
              'org/member = tpv.github.cli.org:Members',
              'org/member/list = tpv.github.cli.org:MemList',
              'org/member/add = tpv.github.cli.org:MemAdd',
              'org/member/remove = tpv.github.cli.org:MemRemove',
              'org/team = tpv.github.cli.org:Teams',
              'org/team/list = tpv.github.cli.org:TeamsList',
              'org/team/show = tpv.github.cli.org:TeamsShow',
              'org/team/add = tpv.github.cli.org:TeamsAdd',
              'org/team/remove = tpv.github.cli.org:TeamsRemove',
              'org/team/repo = tpv.github.cli.org:TeamsRepos',
              'org/team/repo/list = tpv.github.cli.org:TeamsReposList',
              'org/team/repo/add = tpv.github.cli.org:TeamsReposAdd',
              'org/team/repo/remove = tpv.github.cli.org:TeamsReposRemove',
          ],
      },
      )
