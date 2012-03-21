## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Clean build directories.

By default all build directories for all projects are removed.
You can specify a list of build directory names to cleanup.
"""

import os
import glob
import logging
import qibuild

def configure_parser(parser):
    """Configure parser for this action"""    
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.build_parser(parser)
    qibuild.parsers.project_parser(parser)
    
def cleanup( build_dir ):
    
    files = os.listdir(build_dir)

    for f in files:
        path = fullpath=os.path.join( build_dir, f )
        qibuild.sh.rm(path)

def do(args):
    """Main entry point"""
    logger   = logging.getLogger(__name__)
    qiwt     = qibuild.worktree_open(args.work_tree)
    toc      = qibuild.toc_open(args.work_tree, args)

    (project_names, _, _) = toc.resolve_deps()

    projects = [toc.get_project(name) for name in project_names]
    
    logger.info("Workdir : " + qiwt.work_tree )
    
    logger.info("Cleaning directories :")

    for project in projects:        
        bdir = project.build_directory        
        bdir_rel = os.path.relpath(bdir, qiwt.work_tree )        
        print "\t%s\t: %s" % (project.name, bdir_rel)
        cleanup( bdir )        
        print " ... done !"
        
