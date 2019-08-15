class CoreException(Exception):
    """Exists for the benefit of making the cli easier to catch exceptions."""


class SubmoduleFindingError(CoreException):
    """when struggling to find the submodule."""


class DirtyRepoError(CoreException):
    """dirty repo, d'uh"""


class MasterBranchError(CoreException):
    """Not on the right branch"""
