## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.


""" Parsing of qisrc command line arguments

"""

import os

import qisrc.worktree
import qibuild.sh

def guess_current_project(worktree, cwd):
    """ Guess the current project using a worktree and the
    current working directory

    """
    projects = worktree.projects[:]
    projects.reverse()
    for project in projects:
        if qibuild.sh.is_path_inside(cwd, project.path):
            return project

def projects_from_cwd(worktree, cwd, single=False):
    """ Used when --worktree was not specified.

    Return every projects found in the given cwd

    """
    relpath = os.path.relpath(cwd, worktree.root)
    if not single:
        # First, returns all the projects in the given subdirectory:
        res = projects_in_subdir(worktree, cwd, raises=False)
        if res:
            return res

    # Then, assume we are in a project subdir
    proj = guess_current_project(worktree, cwd)
    if proj:
        return [proj]

    # And then raise:
    mess  = "Could not find any project in '%s'\n" % relpath
    mess += "And '%s' is not inside any project\n" % relpath
    raise Exception(mess)


def parse_project_arg(worktree, project_arg, single=False):
    """ Used to parse one 'project arg'
    Can be :
        * an absolute path
        * the path of the project relative to the worktree
    Result will be:
        * all the projects in the given subdir (unles single is True)
        * a project returned by worktree.get_project()

    """
    if not single:
        as_path = qibuild.sh.to_native_path(project_arg)
        if os.path.exists(as_path):
            res = projects_in_subdir(worktree, as_path, raises=True)
            return res

    # Now assume it is a project src
    project = worktree.get_project(project_arg, raises=True)
    return [project]


def projects_in_subdir(worktree, subdir, raises=False):
    """ Return the list of the projects found in the given subdir

    """
    relpath = os.path.relpath(subdir, worktree.root)
    if relpath == ".":
        return worktree.projects
    res = list()
    projects = worktree.projects[:]
    for project in projects:
        if qibuild.sh.is_path_inside(project.src, relpath):
            res.append(project)
    if not res and raises:
        mess  = "Could not find any project in '%s'\n" % relpath
        raise Exception(mess)
    return res


def projects_from_args(args):
    """
    Return a list of projects to use.

    * --worktree not given: guess

      * if at the root of a worktree: return every project
      * if in a subdirectory of a a project: return the current project
      * otherwise return all the projects found inside the current working dir
      * otherwise raise an exception
    """
    worktree_was_explicit = False
    cwd = os.getcwd()
    if args.worktree:
        worktree = qisrc.worktree.open_worktree(args.worktree)
        worktree_was_explicit = True
    else:
        root = qisrc.worktree.guess_worktree(raises=True)
        worktree = qisrc.worktree.open_worktree(root)


    if not args.projects:
        if worktree_was_explicit or args.all:
            return worktree.projects
        return projects_from_cwd(worktree, cwd, single=args.single)

    if args.single:
        if len(args.projects) != 1:
            raise Exception("Using --single with several projects does not make sense")

    res = list()
    for project_arg in args.projects:
        projects = parse_project_arg(worktree, project_arg, single=args.single)
        res.extend(projects)
    return res
