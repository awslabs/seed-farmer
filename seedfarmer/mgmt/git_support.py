import logging
import os
from typing import Optional, Tuple
from urllib.parse import parse_qs

import git
from git import Repo

import seedfarmer.messages as messages
from seedfarmer import config
from seedfarmer.errors import InvalidConfigurationError

_logger: logging.Logger = logging.getLogger(__name__)


def get_commit_hash(repo: git.Repo) -> Optional[str]:
    try:
        return str(repo.head.object.hexsha)
    except Exception:
        _logger.warn("Could not get a commit hash, ignoring")
        return None


def clone_module_repo(git_path: str) -> Tuple[str, str, Optional[str]]:
    """Clone a git repo and return directory it is cloned into

    Rather than reinventing the wheel, we implement the Generic Git Repository functionality introduced by
    Terraform. Full documentation on the Git URL definition can be found at:
    https://www.terraform.io/language/modules/sources#generic-git-repository

    Parameters
    ----------
    git_path : str
        The Git URL specified in the Module Manifest. Full example:
        https://example.com/network.git//modules/vpc?ref=v1.2.0&depth=1

    Returns
    -------
    Tuple[str,str]
        Returns a tuple that contains (in order):
        - the full path of the seedfarmer.gitmodules where the repo was cloned to
        - the relative path to seedfarmer.gitmodules of the module code
        - the commit hash associated wtih this code
    """
    # gitpython library has started blocking non https and ssh protocols by default
    # codecommit is not _actually_ unsafe
    allow_unsafe_protocols = git_path.startswith("git::codecommit")

    git_path = git_path.replace("git::", "")
    ref: Optional[str] = None
    depth: Optional[int] = None
    module_directory = ""

    if "?" in git_path:
        git_path, query = git_path.split("?")
        query_params = parse_qs(query)
        ref = query_params.get("ref", [None])[0]
        if "depth" in query_params and query_params["depth"][0].isnumeric():
            depth = int(query_params["depth"][0])

    if ".git//" in git_path:
        git_path, module_directory = git_path.split(".git//")

    repo_directory = git_path.replace("https://", "").replace("git@", "").replace("/", "_").replace(":", "_")

    working_dir = os.path.join(
        config.OPS_ROOT, "seedfarmer.gitmodules", f"{repo_directory}_{ref.replace('/', '_')}" if ref else repo_directory
    )
    os.makedirs(working_dir, exist_ok=True)
    repo = None
    if not os.listdir(working_dir):
        if ref is not None:
            _logger.debug("Creating local repo and setting remote: %s into %s: ref=%s ", git_path, working_dir, ref)
            repo = Repo.init(working_dir)
            try:
                git.Remote.create(repo, "origin", git_path, allow_unsafe_protocols)
                repo.remotes["origin"].pull(ref, allow_unsafe_protocols=allow_unsafe_protocols)
            except git.GitError as ge:
                raise InvalidConfigurationError(f"\n Cannot Clone Repo: {ge} {messages.git_error_support()}")
        else:
            _logger.debug("Cloning %s into %s: ref=%s depth=%s", git_path, working_dir, ref, depth)
            try:
                repo = Repo.clone_from(
                    git_path, working_dir, branch=ref, depth=depth, allow_unsafe_protocols=allow_unsafe_protocols
                )
            except git.GitError as ge:
                raise InvalidConfigurationError(f"\n Cannot Clone Repo: {ge} {messages.git_error_support()}")
    else:
        _logger.debug("Pulling existing repo %s at %s: ref=%s", git_path, working_dir, ref)
        repo = Repo(working_dir)
        try:
            repo.remotes["origin"].pull(ref, allow_unsafe_protocols=allow_unsafe_protocols)
        except git.GitError as ge:
            raise InvalidConfigurationError(f"\n Cannot Clone Repo: {ge} {messages.git_error_support()}")
    commit_hash = get_commit_hash(repo)
    return (working_dir, module_directory, commit_hash)
