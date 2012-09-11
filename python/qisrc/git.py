## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" A Pythonic git API

"""
import os
import contextlib
import subprocess

from qibuild import ui
import qibuild.config

class Git:
    """ The Git represent a git tree """
    def __init__(self, repo):
        """ :param repo: The path to the tree """
        self.repo = repo

    def call(self, *args, **kwargs):
        """
        Call a git command

        :param args: The arguments of the command.
                     For instance ["frobnicate", "--spam=eggs"]

        :param kwargs: Will be passed to subprocess.check_call()
                       command, with the following changes:

           * if cwd is not given it will be self.repo instead
           * if env is not given it will be read from the config file
           * if raises is False, no exception will be raise if command
             fails, and a (retcode, output) tuple will be returned.
        """
        if not "cwd" in kwargs.keys():
            kwargs["cwd"] = self.repo
        if not "quiet" in kwargs.keys():
            kwargs["quiet"] = False
        git = qibuild.command.find_program("git", raises=True)
        cmd = [git]
        cmd.extend(args)
        raises = kwargs.get("raises")
        if raises is False:
            del kwargs["raises"]
            del kwargs["quiet"]
            process = subprocess.Popen(cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                **kwargs)
            out = process.communicate()[0]
            # Don't want useless blank lines
            out = out.rstrip("\n")
            return (process.returncode, out)
        else:
            qibuild.command.call(cmd, **kwargs)

    def get_config(self, name):
        """ Get a git config value.
        Return None if not found

        """
        (status, out) = self.call("config", "--get", name, raises=False)
        if status != 0:
            return None
        return out.strip()

    def set_config(self, name, value):
        """ Set a new config value.
        Will be created if it does not exist
        """
        self.call("config", name, value)

    def get_current_ref(self, ref="HEAD"):
        """ return the current ref
        git symbolic-ref HEAD
        else: git name-rev --name-only --always HEAD
        """
        (status, out) = self.call("symbolic-ref", ref, raises=False)
        lines = out.splitlines()
        if len(lines) < 1:
            return None
        if status != 0:
            return None
        return lines[0]

    def get_current_branch(self):
        """ return the current branch """
        branch = self.get_current_ref()
        if not branch:
            return branch
        return branch[11:]


    def get_tracking_branch(self, branch=None):
        if not branch:
            branch = self.get_current_branch()

        remote = self.get_config("branch.%s.remote" % branch)
        merge  = self.get_config("branch.%s.merge" % branch)
        if not remote:
            return None
        if not merge:
            return None
        if merge.startswith("refs/heads/"):
            return "%s/%s" % (remote, merge[11:])
        return "%s/%s" % (remote, merge)

    def add(self, *args, **kwargs):
        """ Wrapper for git add """
        return self.call("add", *args, **kwargs)

    def commit(self, *args, **kwargs):
        """ Wrapper for git commit """
        return self.call("commit", *args, **kwargs)

    def fetch(self, *args, **kwargs):
        """ Wrapper for git fetch """
        return self.call("fetch", *args, **kwargs)

    def init(self, *args, **kwargs):
        """ Wrapper for git init """
        return self.call("init", *args, **kwargs)

    def reset(self, *args, **kwargs):
        """ Wrapper for git reset """
        return self.call("reset", *args, **kwargs)

    def checkout(self, *args, **kwargs):
        """ Wrapper for git checkout """
        return self.call("checkout", *args, **kwargs)

    def pull(self, *args, **kwargs):
        """ Wrapper for git pull """
        return self.call("pull", *args, **kwargs)

    def clone(self, *args, **kwargs):
        """ Wrapper for git clone """
        args = list(args)
        args.append(self.repo)
        kwargs["cwd"] = None
        return self.call("clone", *args, **kwargs)

    def push(self, *args, **kwargs):
        """ Wrapper for git push """
        return self.call("push", *args, **kwargs)

    def remote(self, *args, **kwargs):
        """ Wrapper for git remote """
        return self.call("remote", *args, **kwargs)

    def update_submodules(self, raises=True):
        """ Update submodule, cloning them if necessary """
        # This will fail if some pushed a broken submodule
        # (ie git metadata does not match .gitmodules)
        res, out = self.call("submodule", "status", raises=False)
        if res != 0:
            mess  = "Broken submodules configuration detected for %s\n" % self.repo
            mess += "git status returned %s\n" % out
            if raises:
                raise Exception(mess)
            else:
                return mess
        if not out:
            return
        res, out = self.call("submodule", "update", "--init", "--recursive",
                            raises=False)
        if res == 0:
            return
        mess  = "Failed to update submodules\n"
        mess += out
        if raises:
            raise Exception(mess)
        return mess


    def get_local_branches(self):
        """ Get the list of the local branches in a dict
        master -> tracking branch

        """
        (status, out) = self.call("branch", "--no-color", raises=False)
        if status != 0:
            mess  = "Could not get the list of local branches\n"
            mess += "Error was: %s" % out
            raise Exception(mess)
        lines = out.splitlines()
        # Remove the star and the indentation:
        return [x[2:] for x in lines]

    def is_valid(self):
        """ Check if the worktree is a valid git tree
        """
        if not os.path.isdir(self.repo):
            return False
        (status, out) = self.call("show-ref", "--quiet", raises=False)
        return status == 0

    def is_clean(self, untracked=True):
        """
        Returns true if working dir is clean.
        (ie no untracked files, no unstaged changes)

            :param untracked: will return True even if there are untracked files.
        """
        if untracked:
            (status, out) = self.call("status", "-s", raises=False)
        else:
            (status, out) = self.call("status", "-suno", raises=False)
        lines = [l for l in out.splitlines() if len(l.strip()) != 0 ]
        if len(lines) > 0:
            return False
        return True

    def set_remote(self, name, url):
        """
        Set a new remote with the given name and url

        """
        # If it is already here, do nothing:
        in_conf = self.get_config("remote.%s.url" % name)
        if in_conf and in_conf == url:
            return
        self.call("remote", "rm",  name, quiet=True, raises=False)
        self.call("remote", "add", name, url, quiet=True)

    def set_tracking_branch(self, branch, remote_name, fetch_first=True, remote_branch=None):
        """
        Create a or update the configuration of a branch to track
        a given remote branch

        :param branch: the branch to be created, or to set configuration for
        :param remote_name: the name of the remove ('origin' in most cases)
        :param remote_branch: the name of the remote to track. If not given
            will be the same of the branch name
        :param fetch_first: if you know you just have fetched, (such as when running
            qisrc sync -a), set this to ``False`` to save some time

        """
        if remote_branch is None:
            remote_branch = branch
        tracked = self.get_tracking_branch(branch=branch)
        remote_ref = "%s/%s" % (remote_name, remote_branch)
        if tracked is not None:
            if tracked != remote_ref:
                mess = "%s will now track %s instead of %s"
                mess = mess % (branch, remote_ref, tracked)
                qibuild.ui.warning(mess)
            else:
                return

        if fetch_first:
            # Fetch just in case the branch just has been created
            self.call("fetch", remote_name, quiet=True)

        # If the branch does not exist yet, create it at the right commit
        if not branch in self.get_local_branches():
            self.call("branch", branch, remote_ref, quiet=True)
        self.call("branch", "--set-upstream", branch, remote_ref, quiet=True)

    def update_branch(self, *args, **kwargs):
        """ Update the given branch to match the given remote branch

        :param branch: the local branch to update
        :param remote_name: the name of the remote
        :param remote_branch: the remote branch to update (by default, same name as
                             the local branch)
        :param fetch_first: if you know you just have fetched, (such as when running
            qisrc sync -a), set this to ``False`` to save some time

        Return an string describing what happened.
        The string will be empty iv everything went fine.

        """
        mess = self.update_submodules(raises=False)
        if mess:
            return mess
        return _update_branch(self, *args, **kwargs)


def _update_branch(git, branch, remote_name,
                   remote_branch=None, fetch_first=True):
    """ Helper for git.update_branch

    """
    class Status:
        pass
    status = Status()
    status.mess = ""
    current_branch = git.get_current_branch()
    if not current_branch:
        return "Not currently on any branch"
    if fetch_first:
        (ret, out) = git.call("fetch", remote_name, raises=False)
        if out:
            print out
        if ret != 0:
            status.mess += "Fetch failed\n"
            status.mess += out
            return status.mess
    if not remote_branch:
        remote_branch = branch
    remote_ref = "%s/%s" % (remote_name, remote_branch)
    if current_branch != branch:
        _update_branch_if_ff(git, status, branch, remote_ref)
        return status.mess
    with _stash_changes(git, status):
        # _stash_changes can fail if we think the repo is clean,
        # but first stash fails for some reason ...
        if status.mess:
            return status.mess
        (ret, out) = git.call("rebase", remote_ref, raises=False)
        if ret != 0:
            print "Rebasing failed!"
            print "Calling rebase --abort"
            status.mess += "Could not rebase\n"
            status.mess += out
            (ret, out) = git.call("rebase", "--abort", raises=False)
            if ret == 0:
                return status.mess
            else:
                status.mess += "rebase --abort failed!\n"
                status.mess += out
                return status.mess
    if status.mess:
        # Stashing back failse: calling rebase --abort
        print "Stasthing back changes failed"
        print "Calling rebase --abort"
        (ret, out) = git.call("rebase", "--abort", raises=False)
        if ret != 0:
            status.mess += "rebase --abort failed!\n"
            status.mess += out
    return status.mess

###
# Internal functions used by _update_branch()

@contextlib.contextmanager
def _stash_changes(git, status):
    """ Stash changes. To be used in a 'with' statement """
    if git.is_clean(untracked=False):
        yield
        return
    (ret, out) = git.call("stash", raises=False)
    if ret != 0:
        status.mess += "Stashing changes failed\n"
        status.mess += out
    yield
    # If first stash fails, no need to try stash pop:
    if status.mess:
        return
    (ret, out) = git.call("stash", "pop", raises=False)
    if ret != 0:
        status.mess = "Stashing back changes failed\n"
        status.mess += out

@contextlib.contextmanager
def _change_branch(git, status, branch):
    """ Change branch. To be used in a 'with' statement """
    current_branch = git.get_current_branch()
    if current_branch == branch:
        yield
        return
    with _stash_changes(git, status):
        (ret, out) = git.call("checkout", branch, raises=False)
        if ret != 0:
            status.mess += "Checkout to %s failed\n" % branch
            status.mess += out
        yield
        (ret, out) = git.call("checkout", current_branch, raises=False)
        if ret != 0:
            status.mess += "Checkout back to %s failed\n" % current_branch
            status.mess += out

def _update_branch_if_ff(git, status, local_branch, remote_ref):
    """ Update a local branch with a remote branch if the
    merge is fast-forward

    """
    (ret, out) = git.call("show-ref", "--verify",
                           "refs/heads/%s" % local_branch,
                           raises=False)
    if ret != 0:
        status.mess += "Calling show-ref --verify failed\n"
        status.mess += out
        return
    local_sha1 = out.split()[0]
    (ret, out) = git.call("show-ref", "--verify",
                                "refs/remotes/%s" % remote_ref,
                                raises=False)
    if ret != 0:
        status.mess += "Calling show-ref --verify failed\n"
        status.mess += out
        return

    remote_sha1 = out.split()[0]
    (retcode, out) = git.call("merge-base", local_sha1, remote_sha1,
                               raises=False)
    if retcode != 0:
        status.mess += "Calling merge-base failed"
        status.mess += out
        return
    common_ancestor = out.strip()
    if common_ancestor != local_sha1:
        status.mess += "Could not update %s with %s\n" % (local_branch, remote_ref)
        status.mess += "Merge is not fast-forward and you are not on %s" % local_branch
        return
    if local_sha1 == remote_sha1:
        # Nothing to do
        return
    print "Updating %s with %s ..." % (local_branch, remote_ref)
    # Safe to checkout the branch, run merge and then go back
    # to where we were:
    with _change_branch(git, status, local_branch):
        (ret, out) = git.call("merge", "-v", remote_sha1, raises=False)
        if ret != 0:
            status.mess += "Merging %s with %s failed" % (local_branch, remote_ref)
            status.mess += out

def get_repo_root(path):
    """ Return the root dir of a git worktree given a path

    :return None: if no .git was found

    """
    head = path
    while True:
        if os.path.exists(os.path.join(head, ".git")):
            break
        (head, tail) = os.path.split(head)
        if not tail:
            return None
    return head

def is_submodule(path):
    """ Tell if the given path is a submodule

    """
    repo_root = get_repo_root(path)
    if not repo_root:
        return False
    git = Git(repo_root)
    (retcode, out) = git.call("submodule", raises=False)
    if retcode == 0:
        if not out:
            return False
        else:
            lines = out.splitlines()
            submodules = [x.split()[-1] for x in lines]
            rel_path = os.path.relpath(path, repo_root)
            return rel_path in submodules
    else:
        ui.warning("git submodules configuration is broken for",
                   repo_root, "!",
                   "\nError was: ", ui.reset, "\n", "  " + out)
        # clone_project will just erase it and create a git repo instead
        return True


def open(repo):
    """ Open a new worktree
    """
    git = Git(repo)
    return git
