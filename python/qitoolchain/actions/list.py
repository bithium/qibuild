## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Display the toolchains names.

"""

import qisys
import qibuild
import qitoolchain

from qisys import ui

def configure_parser(parser):
    """Configure parser for this action """
    qibuild.parsers.worktree_parser(parser)


def do(args):
    """ Main method """
    tc_names = qitoolchain.get_tc_names()
    if not tc_names:
        print "No toolchain yet"
        print "Use `qitoolchain create` to create a new toolchain"
        return
    default_toc_name = None
    try:
        worktree = qisys.worktree.open_worktree(args.worktree)
        toc = qibuild.toc.Toc(worktree)
        default_toc_name = toc.config.local.defaults.config
    except qisys.worktree.NotInWorktree, e:
        pass
    print "Known toolchains:"
    for tc_name in tc_names:
        print "* " if tc_name == default_toc_name else "  ", tc_name
    print
    if default_toc_name is not None:
        ui.info("Worktree", ui.green, worktree.root, ui.reset, "is using",
                ui.blue, default_toc_name, ui.reset,
                "as its default toolchain.")
    print "Use ``qitoolchain info <tc_name>`` for more info"
