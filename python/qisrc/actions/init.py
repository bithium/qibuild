##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>
##  - Dimitri Merejkowsky <dmerejkowsky@aldebaran-robotics.com>
##
## Copyright (C) 2010, 2011 Aldebaran Robotics
##

"""Init a new qisrc workspace """

import os
import qitools
import qisrc


def configure_parser(parser):
    """Configure parser for this action """
    qitools.qiworktree.work_tree_parser(parser)

def do(args):
    """Main entry point"""
    #work_tree = qibuild.toc.guess_work_tree(args.work_tree)
    #LOGGER.debug("worktree: %s", work_tree)
    work_tree = qitools.qiworktree.guess_work_tree(args.work_tree)

    if work_tree is None:
        work_tree = os.getcwd()
    qisrc.create(work_tree)

if __name__ == "__main__" :
    import sys
    qitools.cmdparse.sub_command_main(sys.modules[__name__])