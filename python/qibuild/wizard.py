## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" qibuild wizard

"""

import os
import sys

from qisys import ui
import qisys
import qibuild
import qitoolchain

def guess_cmake(qibuild_cfg):
    """ Try to find cmake

    """
    # FIXME: loook for it in registry on windows
    # FIXME: look for it in /Applications on mac
    build_env = qibuild.config.get_build_env()
    cmake = qisys.command.find_program("cmake", env=build_env)
    if cmake:
        print "Found CMake:" , cmake
        return cmake
    print "CMake not found"
    cmake = qisys.interact.ask_program("Please enter full CMake path")
    if not cmake:
        raise Exception("qiBuild cannot work without CMake\n"
            "Please install CMake if necessary and re-run this wizard\n")
    # Add path to CMake in build env
    cmake_path = os.path.dirname(cmake)
    qibuild_cfg.add_to_default_path(cmake_path)
    qibuild_cfg.write()
    return cmake

def ask_cmake_generator():
    """ Ask the user to choose a cmake generator

    """
    cmake_generators = qibuild.cmake.get_known_cmake_generators()
    cmake_generator = qisys.interact.ask_choice(cmake_generators,
        "Please choose a generator")

    return cmake_generator

def ask_ide(qibuild_cfg):
    """ Ask the user to choose an IDE

    """
    ides = ["QtCreator", "Eclipse CDT"]
    if sys.platform.startswith("win"):
        ides.append("Visual Studio")
    if sys.platform == "darwin":
        ides.append("Xcode")
    ide = qisys.interact.ask_choice(ides,
        "Please choose an IDE")
    return ide

def ask_incredibuild(qibuild_cfg):
    """ Ask the user if he wants to use IncrediBuild

    """
    build_env = qibuild.config.get_build_env()
    answer = qisys.interact.ask_yes_no("Do you want to use IncrediBuild?", False)
    if not answer:
        return

    build_console = qisys.command.find_program("BuildConsole.exe", env=build_env)
    if build_console:
        print "Found BuildConsole.exe:", build_console
        qibuild_cfg.build.incredibuild = True
        return

    build_console = qisys.interact.ask_program("Please enter full BuildConsole.exe path")
    if not build_console:
        print "Cannot use Incredibuild without knowing the path to BuildConsole.exe"
        return
    # Add path to CMake in build env
    build_console_path = os.path.dirname(build_console)
    qibuild_cfg.add_to_default_path(build_console_path)
    qibuild_cfg.build.incredibuild = True

def configure_qtcreator(qibuild_cfg):
    """ Configure QtCreator

    """
    ide = qibuild.config.IDE()
    ide.name = "QtCreator"
    build_env = qibuild.config.get_build_env()
    qtcreator_path = qisys.command.find_program("qtcreator", env=build_env)
    if qtcreator_path:
        ui.info(ui.green, "::", ui.reset,  "Found QtCreator:", qtcreator_path)
        mess  = "Do you want to use qtcreator from %s?\n" % qtcreator_path
        mess += "Answer 'no' if you installed qtcreator from Nokia's installer"
        answer = qisys.interact.ask_yes_no(mess, default=True)
        if not answer:
            qtcreator_path = None
    else:
        ui.warning("QtCreator not found")
    if not qtcreator_path:
        qtcreator_path = qisys.interact.ask_program(
            "Please enter full qtcreator path")
    if not qtcreator_path:
        ui.warning("Not adding config for QtCreator",
                   "qibuild open will not work", sep="\n")
        return
    ide.path = qtcreator_path
    qibuild_cfg.add_ide(ide)


def configure_ide(qibuild_cfg, ide_name):
    """ Configure an IDE

    """
    if ide_name == "QtCreator":
        configure_qtcreator(qibuild_cfg)
        return
    ide = qibuild.config.IDE()
    ide.name = ide_name
    qibuild_cfg.add_ide(ide)

def configure_local_settings(toc):
    """ Configure local settings for this worktree

    """
    print
    ui.info(ui.green, "::", ui.reset,  "Found a worktree in", toc.worktree.root)
    answer = qisys.interact.ask_yes_no(
        "Do you want to configure settings for this worktree?",
        default=True)
    if not answer:
        return
    tc_names = qitoolchain.get_tc_names()
    if tc_names:
        ui.info(ui.green, "::", ui.reset,
                "Found the following toolchains: ", ", ".join(tc_names))
        answer = qisys.interact.ask_yes_no(
            "Use one of these toolchains by default",
            default=True)
        if answer:
            default = qisys.interact.ask_choice(tc_names,
                "Choose a toolchain to use by default")
            if default:
                toc.config.local.defaults.config = default
                toc.save_config()
    answer = qisys.interact.ask_yes_no(
        "Do you want to use a unique build dir?"
        " (mandatory when using Eclipse)",
        default=False)

    build_dir = None
    if answer:
        build_dir = qisys.interact.ask_string("Path to a build directory")
        build_dir = os.path.expanduser(build_dir)
        full_path = os.path.join(toc.worktree.root, build_dir)
        ui.info(ui.green, "::", ui.reset,
                "Will use", full_path, "as a root for all build directories")
    toc.config.local.build.build_dir = build_dir
    toc.save_config()



def run_config_wizard(toc):
    """ Run a nice interactive config wizard

    """
    if toc:
        qibuild_cfg = toc.config
    else:
        qibuild_cfg = qibuild.config.QiBuildConfig()
        qibuild_cfg_path = qibuild.config.get_global_cfg_path()
        if not os.path.exists(qibuild_cfg_path):
            to_create = os.path.dirname(qibuild_cfg_path)
            qisys.sh.mkdir(to_create, recursive=True)
            with open(qibuild_cfg_path, "w") as fp:
                fp.write('<qibuild version="1" />\n')
        qibuild_cfg.read()

    # Ask for a default cmake generator
    guess_cmake(qibuild_cfg)
    generator = ask_cmake_generator()
    qibuild_cfg.defaults.cmake.generator = generator

    ide = ask_ide(qibuild_cfg)
    if ide:
        configure_ide(qibuild_cfg, ide)

    if sys.platform.startswith("win"):
        ask_incredibuild(qibuild_cfg)

    qibuild_cfg.write()

    if toc:
        configure_local_settings(toc)
