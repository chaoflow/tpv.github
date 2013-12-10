from tpv.cli import DynamicCompletion
from types import user_type, repo_type, org_type, team_type


class RepositoryDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete repositories '''

    def complete(self, command, prefix, posargs):
        if '/' not in prefix:
            # if we don't have a user, yet, we provide the
            # repositories of the authenticated user as possible
            # completions

            user = user_type(None)
            return [x for x in user["repos"] if x.startswith(prefix)]
        else:
            # a user has been given, complete his repositories
            (user_name, repo_prefix) = prefix.split("/", 1)
            user = user_type(user_name)
            return [user_name + "/" + x
                    for x in user["repos"]
                    if x.startswith(repo_prefix)]


class IssueNoDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete issuenumbers '''

    def complete(self, command, prefix, posargs):
        repo = repo_type(command.repo)

        return [x
                for x in map(str, repo["issues"])
                if x.startswith(prefix)]


class CommentIdDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete commentids '''

    def complete(self, command, prefix, posargs):
        repo = repo_type(command.repo)

        return [x
                for x in map(str, repo["comments"])
                if x.startswith(prefix)]


class OwnOrgsDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete the organisations of the
authorized user'''

    def complete(self, command, prefix, posargs):
        user = user_type(None)

        return [x
                for x in user["orgs"]
                if x.startswith(prefix)]


class TeamDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete the teams of an organisation'''

    def __init__(self, argument="org"):
        self._argument = argument

    def complete(self, command, prefix, posargs):
        org = org_type(posargs[self._argument])
        return [x["name"]
                for x in org["teams"].itervalues()
                if x["name"].startswith(prefix)]


class TeamOrgMembersDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete the members of either a team
or an organisation'''

    def __init__(self, argument="org"):
        self._argument = argument

    def complete(self, command, prefix, posargs):
        org = org_type(posargs[self._argument])
        if command.team is not None:
            collection = team_type(org, command.team)
        else:
            collection = org

        return [x
                for x in collection["members"]
                if x.startswith(prefix)]
