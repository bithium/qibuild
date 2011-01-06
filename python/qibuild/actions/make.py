##
## Author(s):
##  - Cedric GESTES <gestes@aldebaran-robotics.com>
##  - Dimitri Merejkowsky <dmerejkowsy@aldebaran-robotics.com>
##
## Copyright (C) 2010, 2011 Aldebaran Robotics
##

"""Configure a project

"""

import logging
import qibuild
import qitools.cmdparse

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.build_parser(parser)
    qibuild.parsers.project_parser(parser)

def do(args):
    """Main entry point"""
    logger   = logging.getLogger(__name__)
    toc      = qibuild.toc.toc_open(args.work_tree, args, use_env=True)

    wanted_projects = qibuild.toc.get_projects_from_args(toc, args)
    (src_projects, bin_projects, not_found_projects) = toc.split_sources_and_binaries(wanted_projects)

    use_incredibuild = toc.configstore.get("general", "build", "incredibuild")


    # If the user specified "Visual Studio" in the configuration
    # file, assume it has visual studio :)
    generator = toc.configstore.get("general", "build", "cmake_generator")
    visual_studio = False
    if generator:
        if "Visual Studio" in generator:
            visual_studio = True
        else:
            visual_studio = False

    for project in src_projects:
        logger.info("Building %s in %s", project, toc.build_folder_name)
        logger.debug("%s", toc.projects[project])
        qibuild.project.make(toc.projects[project], toc.build_type,
            num_jobs = args.num_jobs,
            incredibuild = use_incredibuild,
            visual_studio = visual_studio)


if __name__ == "__main__":
    import sys
    qitools.cmdparse.sub_command_main(sys.modules[__name__])

