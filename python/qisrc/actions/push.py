## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Push changes for review

"""
import sys

from qisys import ui
import qisys
import qisrc

def configure_parser(parser):
    """Configure parser for this action """
    qisys.parsers.worktree_parser(parser)
    parser.add_argument("--no-review", action="store_false", dest="review",
        help="Do not go through code review")
    parser.add_argument("-n", "--dry-run", action="store_true", dest="dry_run",
        help="Dry run")
    parser.add_argument("--cc", "--reviewers", action="append", dest="reviewers",
        help="Add reviewers (full email or just username if the domain is the same as yours)")
    parser.set_defaults(review=True, dry_run=False)


def do(args):
    """ Main entry point """
    git_path = qisys.worktree.git_project_path_from_cwd()
    git = qisrc.git.Git(git_path)
    current_branch = git.get_current_branch()
    if not current_branch:
        ui.error("Not currently on any branch")
        sys.exit(2)
    qisrc.review.push(git_path, current_branch,
                      review=args.review, dry_run=args.dry_run,
                      reviewers=args.reviewers)
