## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Launch automatic tests
"""

import os
import sys

import qibuild

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.build_parser(parser)
    parser.add_argument("project", nargs="?")
    parser.add_argument("-k", "--pattern", dest="pattern",
                        help="Filter tests matching this pattern")
    parser.add_argument("-l", "--list", dest="dry_run",
                        action="store_true",
                        help="List what tests would be run")
    parser.add_argument("--slow", action="store_true",
                        help="Also run slow tests")
    parser.add_argument("-V", action="store_true", dest="verbose_tests",
                        help="verbose tests")
    parser.add_argument("--valgrind", dest="valgrind", action="store_true",
                        help="run tests under valgrind")
    parser.add_argument("--nightmare", dest="nightmare", action="store_true",
                        help="run tests in shuffle and 20 times (apply only to gtest)")
    parser.add_argument("--test-args", dest="test_args",
                        help="Pass extra argument to test binary")
    parser.set_defaults(slow=False)

def do(args):
    """Main entry point"""
    toc = qibuild.toc_open(args.worktree, args)
    project = qibuild.cmdparse.project_from_args(toc, args)

    build_dir = project.build_directory
    cmake_cache = os.path.join(build_dir, "CMakeCache.txt")
    if not os.path.exists(cmake_cache):
        qibuild.toc.advise_using_configure(toc, project)

    res = qibuild.ctest.run_tests(project, toc.build_env,
            pattern=args.pattern, slow=args.slow,
            dry_run=args.dry_run, valgrind=args.valgrind,
            verbose=args.verbose_tests, nightmare=args.nightmare,
            test_args=args.test_args)
    if not res:
        sys.exit(1)
