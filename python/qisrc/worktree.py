## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""This package contains the WorkTree object.

"""

import os
import qibuild.log
import operator

from qibuild import ui
import qibuild.sh
import qisrc.git
import qixml
from qixml import etree

LOGGER = qibuild.log.get_logger("WorkTree")


class NotInWorktree(Exception):
    """ Just a custom exception """
    def __str__(self):
        return """ Could not guess worktree from current working directory
  Here is what you can do :
     - try from a valid work tree
     - specify an existing work tree with --work-tree PATH
     - create a new work tree with `qibuild init`
"""

class WorkTree:
    """ This class represent a :term:`worktree`

    """
    def __init__(self, root):
        """
        Construct a new worktree

        :param root: The root directory of the worktree.
        """
        self.root = root
        self.projects = list()
        self.git_projects = list()
        self.buildable_projects = list()
        self.load()

    def load(self):
        """
        Load the worktree.xml file

        """
        self.projects = list()
        self.git_projects = list()
        self.buildable_projects = list()
        dot_qi = os.path.join(self.root, ".qi")
        worktree_xml = os.path.join(dot_qi, "worktree.xml")
        if not os.path.exists(worktree_xml):
            qibuild.sh.mkdir(dot_qi)
            with open(worktree_xml, "w") as fp:
                fp.write("<worktree />\n")
        if os.path.exists(worktree_xml):
            self.xml_tree = qixml.read(worktree_xml)
            self.parse_projects()
            self.parse_buildable_projects()

        self.projects.sort(key=operator.attrgetter("src"))
        self.buildable_projects.sort(key=operator.attrgetter("src"))
        self.git_projects.sort(key=operator.attrgetter("src"))

    def get_manifest_projects(self):
        """ Get the projects mark as beeing 'manifest' projects

        """
        return [p for p in self.projects if p.manifest]

    def update_project_config(self, src, key, value):
        """ Update the project configuration """
        for elem in self.xml_tree.findall("project"):
            if elem.get("src") == src:
                elem.set(key, value)

    def set_manifest_project(self, src, profile="default"):
        """ Mark a project as being a manifest project

        """
        project = self.get_project(src, raises=True)
        self.update_project_config(project.src, "manifest", "true")
        self.update_project_config(project.src, "profile", profile)
        self.dump()
        self.load()

    def set_git_project_config(self, src, remote, branch):
        """ Set the 'remote' and the 'branch' attributes of a
        project config so that `qisrc sync` can work afterwards

        """
        project = self.get_project(src, raises=True)
        self.update_project_config(project.src, "remote", remote)
        self.update_project_config(project.src, "branch", branch)
        self.dump()
        self.load()

    def set_project_review(self, src, review):
        """ Mark a project as being under code review """
        project = self.get_project(src, raises=True)
        self.update_project_config(project.src, "review", "true")
        self.dump()
        self.load()

    def dump(self):
        """
        Dump self to the worktree.xml file

        """
        dot_qi = os.path.join(self.root, ".qi")
        qibuild.sh.mkdir(dot_qi, recursive=True)
        worktree_xml = os.path.join(self.root, ".qi", "worktree.xml")
        qixml.write(self.xml_tree, worktree_xml)

    def parse_projects(self):
        """ Parse .qi/worktree.xml, resolve subprojects, set the
        git_project attribute of every project

        """
        projects_elem = self.xml_tree.findall("project")
        for project_elem in projects_elem:
            project = Project()
            project.parse(project_elem)
            self.set_path(project)
            project.parse_qiproject_xml()
            self.projects.append(project)

        # Now parse the subprojects
        res = self.projects[:]
        for project in self.projects:
            self._rec_parse_sub_projects(project, res)
        self.projects = res[:]


    def _rec_parse_sub_projects(self, project, res):
        """ Recursively parse every project and subproject,
        filling up the res list

        """
        if os.path.exists(os.path.join(project.path, ".git")):
            self.git_projects.append(project)
            project.git_project = project
        for sub_project_src in project.subprojects:
            sub_project = Project()
            sub_project.src = os.path.join(project.src, sub_project_src)
            sub_project.src = qibuild.sh.to_posix_path(sub_project.src)
            self.set_path(sub_project)
            sub_project.parse_qiproject_xml()
            if project.git_project:
                sub_project.git_project = project.git_project
            res.append(sub_project)
            self._rec_parse_sub_projects(sub_project, res)

    def set_path(self, project):
        """ Set the path attribute of a project

        """
        p_path = os.path.join(self.root, project.src)
        project.path = qibuild.sh.to_native_path(p_path)


    def parse_buildable_projects(self):
        """ Iterate through every project.

        If project contains a qirpoject.xml and a CMakeLists.txt
        file, add it to the list

        """
        for project in self.projects:
            p_path = project.path
            qiproj_xml = os.path.join(p_path, "qiproject.xml")
            cmake_lists = os.path.join(p_path, "CMakeLists.txt")
            if os.path.exists(qiproj_xml) and \
                os.path.exists(cmake_lists):
                self.buildable_projects.append(project)

    def get_project(self, src, raises=False):
        """ Get a project

        :param src: a absolute path, or a path relative to the worktree
        :param raises: Raises if project is not found
        :returns:  a :py:class:`Project` instance or None if raises is
            False and project is not found

        """
        if os.path.isabs(src):
            src = os.path.relpath(src, self.root)
            src = qibuild.sh.to_posix_path(src)
        p_srcs = [p.src for p in self.projects]
        if not src in p_srcs:
            if not raises:
                return None
            mess  = "No project in '%s'\n" % src
            mess += "Know projects are in %s" % ", ".join(p_srcs)
            raise Exception(mess)
        match = [p for p in self.projects if p.src == src]
        res = match[0]
        return res

    def add_project(self, src):
        """ Add a project to a worktree

        :param src: path to the project, can be absolute,
                    or relative to the worktree root

        """
        # Coming from user, can be an abspath:
        if os.path.isabs(src):
            src = os.path.relpath(src, self.root)
            src = qibuild.sh.to_posix_path(src)
        p_srcs = [p.src for p in self.projects]
        if src in p_srcs:
            mess  = "Could not add project to worktree\n"
            mess += "Path %s is already registered\n" % src
            mess += "Current worktree: %s" % self.root
            raise Exception(mess)

        project = Project()
        project.src = src
        root_elem = self.xml_tree.getroot()
        root_elem.append(project.xml_elem())
        self.dump()
        self.load()

    def remove_project(self, src, from_disk=False):
        """ Remove a project from a worktree

        :param src: path to the project, can be absolute,
                    or relative to the worktree root
        :param from_disk: also erase project files from disk


        """
        # Coming from user, can be an abspath:
        if os.path.isabs(src):
            src = os.path.relpath(src, self.root)
            src = qibuild.sh.to_posix_path(src)
        p_srcs = [p.src for p in self.projects]
        if src not in p_srcs:
            raise Exception("No such project: %s" % src)
        root_elem = self.xml_tree.getroot()
        for project_elem in root_elem.findall("project"):
            if project_elem.get("src") == src:
                if from_disk:
                    to_remove = self.get_project(src).path
                    qibuild.sh.rm(to_remove)
                root_elem.remove(project_elem)
        self.dump()
        self.load()



    def __repr__(self):
        res = "<worktree in %s>" % self.root
        return res


def open_worktree(worktree=None):
    """
    Open a qi worktree.

    :return: a valid :py:class:`WorkTree` instance.
             If worktree is None, guess it from the current working dir.

    """
    if not worktree:
        worktree = guess_worktree()
    if worktree is None:
        raise NotInWorktree()
    if not os.path.exists(worktree):
        mess =  "Cannot open a worktree from %s\n" % worktree
        mess += "This path does not exist"
        raise Exception(mess)
    res = WorkTree(worktree)
    ui.debug("Opening worktree in", worktree)
    return res


def guess_worktree(cwd=None, raises=False):
    """Look for parent directories until a .qi dir is found somewhere.

    """
    if cwd is None:
        cwd = os.getcwd()
    head = cwd
    while True:
        d = os.path.join(head, ".qi")
        if os.path.isdir(d):
            return head
        (head, _tail) = os.path.split(head)
        if not _tail:
            break
    if raises:
        raise NotInWorktree()
    else:
        return None




def create(directory, force=False):
    """Create a new Qi work tree in the given directory.

    If already in a worktre, will do nothing, unless
    force is True, and then will re-initialize the worktree.

    """
    if not force:
        parent_worktree = guess_worktree(directory)
        if parent_worktree:
            if parent_worktree != directory:
                if not force:
                    qibuild.ui.warning("""{0} is already in a worktee
(in {1})
Use --force if you want to re-initialize the worktree""".format(directory, parent_worktree))
                    return open_worktree(parent_worktree)

        git_project = git_project_path_from_cwd(directory)
        if git_project:
            mess  = "Trying to create a worktree inside a git project\n"
            mess += "(in %s)\n" % git_project
            raise Exception(mess)

    to_create = os.path.join(directory, ".qi")
    qibuild.sh.mkdir(to_create, recursive=True)
    qi_xml = os.path.join(directory, ".qi", "qibuild.xml")
    if not os.path.exists(qi_xml) or force:
        with open(qi_xml, "w") as fp:
            fp.write("<qibuild />\n")
    return open_worktree(directory)

def git_project_path_from_cwd(cwd=None):
    """ Get the path to the git repo of the current
    project using cwd

    """
    if not cwd:
        cwd = os.getcwd()
    return qisrc.git.get_repo_root(cwd)

class Project:
    def __init__(self, src=None):
        self.src = src
        self.path = None
        self.git_project = None
        self.subprojects = list()
        self.manifest = False
        self.remote = None
        self.branch = None
        self.profile = None
        self.review = False

    def parse(self, xml_elem):
        self.src = qixml.parse_required_attr(xml_elem, "src")
        self.manifest = qixml.parse_bool_attr(xml_elem, "manifest")
        self.review = qixml.parse_bool_attr(xml_elem, "review")
        self.profile = xml_elem.get("profile", "default")
        self.remote = xml_elem.get("remote", "origin")
        self.branch = xml_elem.get("branch", "master")

    def parse_qiproject_xml(self):
        qiproject_xml = os.path.join(self.path, "qiproject.xml")
        if not os.path.exists(qiproject_xml):
            return
        tree = qixml.read(qiproject_xml)
        project_elems = tree.findall("project")
        for project_elem in project_elems:
            src = qixml.parse_required_attr(project_elem, "src", xml_path=qiproject_xml)
            self.subprojects.append(src)

    def xml_elem(self):
        res = etree.Element("project")
        res.set("src", self.src)
        if self.git_project:
            res.set("git_project", self.git_project)
        if self.manifest:
            res.set("manifest", "true")
        if self.review:
            res.set("review", "true")
        if self.profile:
            res.set("profile", self.profile)
        if self.remote:
            res.set("remote", self.remote)
        if self.branch:
            res.set("branch", self.branch)
        return res

    def __repr__(self):
        res = "<Project in %s>" % (self.src)
        return res
