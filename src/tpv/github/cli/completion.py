from tpv.cli import DynamicCompletion
from types import user_type, repo_type


class RepositoryDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete repositories '''

    def complete(self, command, prefix):
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

    def complete(self, command, prefix):
        repo = repo_type(command.repo)

        return [x
                for x in map(str, repo["issues"])
                if x.startswith(prefix)]


class CommentIdDynamicCompletion(DynamicCompletion):
    '''Completion class to dynamically complete commentids '''

    def complete(self, command, prefix):
        repo = repo_type(command.repo)

        return [x
                for x in map(str, repo["comments"])
                if x.startswith(prefix)]
