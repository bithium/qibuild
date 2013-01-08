## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Deploy project(s) on a remote target

All deployed material is installed in the location 'path' on
the target 'hostname'.

Examples:

  qibuild deploy foobar john@mytarget:deployed

Installs everything on the target 'mytarget' in the
'deployed' directory from the 'john' 's home.

  qibuild deploy foobar john@mytarget:/tmp/foobar

Installs everything on the target 'mytarget' in the
'/tmp/foobar' directory.
"""

import os

from qisys import ui
import qibuild
import qisys.sh
import qibuild.deploy

def configure_parser(parser):
    """Configure parser for this action"""
    qibuild.parsers.toc_parser(parser)
    qibuild.parsers.project_parser(parser)
    qibuild.parsers.build_parser(parser)
    group = parser.add_argument_group("deploy options")
    group.add_argument("url", help="remote target url: user@hostname:path")
    group.add_argument("--port", help="port", type=int)
    group.add_argument("--split-debug", action="store_true",
                        dest="split_debug", help="split debug symbols. "
                        "Enable remote debuging")
    group.add_argument("--no-split-debug", action="store_false",
                        dest="split_debug", help="do not split debug symbols. "
                        "Remote debugging won't work")
    parser.set_defaults(port=22, split_debug=True)

def do(args):
    """Main entry point"""
    url = args.url
    qibuild.deploy.parse_url(url) # throws if url is invalid
    toc = qibuild.toc.toc_open(args.worktree, args)
    ui.info(ui.green, "Current worktree:", ui.reset, ui.bold, toc.worktree.root)
    if toc.active_config:
        ui.info(ui.green, "Active configuration: ",
                ui.blue, "%s (%s)" % (toc.active_config, toc.build_type))
    rsync = qisys.command.find_program("rsync", env=toc.build_env)
    use_rsync = False
    if rsync:
        use_rsync = True
    else:
        ui.warning("Please install rsync to get faster synchronisation")
        scp = qisys.command.find_program("scp", env=toc.build_env)
        if not scp:
            raise Exception("Could not find rsync or scp")

    # Resolve deps:
    (packages, projects) = qibuild.cmdparse.deps_from_args(toc, args)

    if not args.single:
        ui.info(ui.green, "The following projects")
        for project in projects:
            ui.info(ui.green, " *", ui.blue, project.name)
        if not args.single and packages:
            ui.info(ui.green, "and the following packages")
            for package in packages:
                ui.info(" *", ui.blue, package.name)
        ui.info(ui.green, "will be deployed to", ui.blue, url)

    # Deploy packages: install all of them in the same temp dir, then
    # deploy this temp dir to the target
    if not args.single and packages:
        print
        ui.info(ui.green, ":: ", "Deploying packages")
        with qisys.sh.TempDir() as tmp:
            for (i, package) in enumerate(packages):
                ui.info(ui.green, "*", ui.reset,
                        "(%i/%i)" % (i+1, len(package.name)),
                        ui.green, "Deploying package", ui.blue, package.name,
                        ui.green, "to", ui.blue, url)
                toc.toolchain.install_package(package.name, tmp, runtime=True)
            qibuild.deploy.deploy(tmp, args.url, use_rsync=use_rsync, port=args.port)
        print

    if not args.single:
        ui.info(ui.green, ":: ", "Deploying projects")
    # Deploy projects: install them inside a 'deploy' dir inside the build dir,
    # then deploy this dir to the target
    deployed_list = list()
    for (i, project) in enumerate(projects):
        ui.info(ui.green, "*", ui.reset,
                "(%i/%i)" % (i+1, len(projects)),
                ui.green, "Deploying project", ui.blue, project.name,
                ui.green, "to", ui.blue, url)
        destdir = os.path.join(project.build_directory, "deploy")
        #create folder for project without install rules
        qisys.sh.mkdir(destdir, recursive=True)
        toc.install_project(project, destdir, prefix="/",
                            runtime=True, num_jobs=args.num_jobs,
                            split_debug=args.split_debug)
        ui.info(ui.green, "Sending binaries to target ...")
        qibuild.deploy.deploy(destdir, args.url, use_rsync=use_rsync, port=args.port)
        if not args.split_debug:
            continue
        gdb_script, message = qibuild.deploy.generate_debug_scripts(toc, project.name,
                                                                    args.url,
                                                                    deploy_dir=destdir)

        bindir = os.path.join(destdir, "bin")
        binaries = list()
        if os.path.exists(bindir):
            binaries = [x for x in os.listdir(bindir)]
            binaries = [x for x in binaries if os.path.isfile(os.path.join(bindir, x))]
            binaries = [os.path.join("bin", x) for x in binaries]
        deployed_list.append((project, binaries, gdb_script, message))
    if not args.split_debug:
        return
    ui.info(ui.green, ":: ", "Deployed projects")
    for (i, deployed) in enumerate(deployed_list):
        project, binaries, gdb_script, message = deployed
        if not binaries:
            ui.info(ui.green, "*", ui.reset,
                    "(%i/%i)" % (i+1, len(projects)),
                    ui.green, "Project", ui.blue, project.name,
                    ui.green, "- No executable deployed")
            continue
        binaries = "\n".join(["    %s" % bin_ for bin_ in binaries])
        ui.info(ui.green, "*", ui.reset,
                "(%i/%i)" % (i+1, len(projects)),
                ui.green, "Project", ui.blue, project.name,
                ui.green, "- Deployed binaries:",
                ui.reset, "\n%s" % binaries)
        if gdb_script:
            ui.info(ui.green, "*", ui.reset,
                    "To remotely debug a binary from the above list, run:")
            ui.info("    %s <binary>" % gdb_script)
        else:
            ui.warning(message)
