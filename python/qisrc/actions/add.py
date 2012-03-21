## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Add a new project in a qisrc workspace """

import os
import logging
import urlparse
import getpass
import qisrc
import qibuild

LOGGER = logging.getLogger(__name__)


def configure_parser(parser):
    """Configure parser for this action """
    qibuild.parsers.work_tree_parser(parser)
    parser.add_argument("url",  metavar="URL", help="url of the project. "
        "right now only git URLs are supported")
    parser.add_argument("name", metavar="NAME", nargs="?",
        help="name of the project. If not given, this will be deduced from the "
             "URL")
    parser.add_argument("--username",  metavar="USERNAME", 
        help="username for authentication.")
    parser.add_argument("--password",  metavar="PASSWORD", 
        help="Ask for password to use in all projects.")             

def setupAuthentication( url, user, password = None ):

    if user == None:
        return url
        
    url = urlparse.urlsplit(url)
    
    temp = [ k for k in url ]
    netloc = temp[1].split("@")
    
    if len(netloc) == 1:
        netloc.append(netloc[0])    

    if password != None:
        netloc[0] = "%s:%s" % (user, password)
    else:
        netloc[0] = user 

    temp[1] = '@'.join(netloc)

    return urlparse.urlunsplit(temp)

def do(args):
    """Main entry point"""
    url = args.url
    name = args.name
    user = args.username
    password = args.password        
    
    if not name:
        name = url.split("/")[-1].replace(".git", "")

    work_tree = qibuild.worktree.worktree_open(args.work_tree)

    git_src_dir = os.path.join(work_tree.work_tree, name)
    LOGGER.info("Git clone: %s -> %s", url, git_src_dir)

    if os.path.exists(git_src_dir):
        raise qibuild.worktree.ProjectAlreadyExists(url, name, git_src_dir)

    url = setupAuthentication( url, user, password )
    
    git = qisrc.git.Git(git_src_dir)
    git.clone(url)

