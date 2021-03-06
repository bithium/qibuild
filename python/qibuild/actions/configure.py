## Copyright (c) 2012, 2013 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Configure a project

"""

from qisys import ui
import qibuild
import qibuild.cmake

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.build_parser(parser)
    qibuild.parsers.project_parser(parser)
    group = parser.add_argument_group("configure options")
    group.add_argument("--build-directory", dest="build_directory",
        action="store",
        help="override the default build directory used by cmake")
    group.add_argument("-D", dest="cmake_flags",
        action="append",
        help="additional cmake flags")
    group.add_argument("--no-clean-first", dest="clean_first",
        action="store_false",
        help="do not clean CMake cache")
    group.add_argument("--debug-trycompile", dest="debug_trycompile",
        action="store_true",
        help="pass --debug-trycompile to CMake call")
    group.add_argument("--eff-c++", dest="effective_cplusplus",
        action="store_true",
        help="activate warnings from the 'Effective C++' book (gcc only)")
    group.add_argument("--werror", dest="werror",
        action="store_true",
        help="tread warnings as error")
    parser.add_argument("--profiling", dest="profiling", action="store_true",
        help="profile cmake execution")
    parser.add_argument("--summarize-options", dest="summarize_options",
                        action="store_true",
                        help="summarize build options at the end")
    parser.set_defaults(clean_first=True, effective_cplusplus=False,
                        werror=False, profiling=False)
    if not parser.epilog:
        parser.epilog = ""
    parser.epilog += """
Note:
    if CMAKE_INSTALL_PREFIX is set during configure, it will be necessary to
    repeat it at install (for further details, see: qibuild install --help).
"""


def do(args):
    """Main entry point"""
    if args.build_directory and not args.single:
        raise Exception("You should use --single "
                        "when specifying a build directory")

    if not args.cmake_flags:
        args.cmake_flags = list()
    if args.effective_cplusplus:
        args.cmake_flags.append("QI_EFFECTIVE_CPP=ON")
    if args.werror:
        args.cmake_flags.append("QI_WERROR=ON")

    toc = qibuild.toc.toc_open(args.worktree, args)
    (_, projects) = qibuild.cmdparse.deps_from_args(toc, args)
    if args.build_directory:
        projects[0].set_custom_build_directory(args.build_directory)

    if args.debug_trycompile:
        print "--debug-trycompile ON"

    ui.info(ui.green, "Current worktree:", ui.reset, ui.bold, toc.worktree.root)
    if toc.active_config:
        ui.info(ui.green, "Active configuration:", ui.blue, toc.active_config)
    for profile in toc.profiles:
        ui.info(ui.green, "Using profile:", ui.blue, profile)
    if toc.local_cmake:
        ui.info(ui.green, "Using custom CMake file:", ui.reset,
                ui.bold, toc.local_cmake)

    project_count = len(projects)
    i = 0
    for project in projects:
        i = i + 1
        ui.info(ui.green, "*", ui.reset, "(%i/%i)" %  (i, project_count),
                ui.green, "Configuring",
                ui.blue, project.name)
        toc.configure_project(project,
            clean_first=args.clean_first,
            debug_trycompile=args.debug_trycompile,
            profiling=args.profiling)
        if args.summarize_options:
            project.summarize_options()
