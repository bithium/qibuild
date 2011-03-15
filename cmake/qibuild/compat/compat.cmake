## Copyright (C) 2011 Aldebaran Robotics


# This is to be used when the names of the
# flags have changed:


# Example:
# After calling:
#      _fix_flags(_res DEPENDS DEPENDENCIES
#          foo SRC foo.h foo.cpp DEPENDENCIES bar)
# _res equals:
#  "foo;SRC;foo.h;foo.cpp;DEPENDS;bar
function(_fix_flags _res _old _new)
  set(_out)
  foreach(_flag ${ARGN})
    string(REPLACE ${_old} ${_new} _new_flag ${_flag})
    list(APPEND _out ${_new_flag})
  endforeach()
  set(${_res} ${_out} PARENT_SCOPE)
endfunction()

function(sdk_add_include _name _subfolder)
  qi_warning("sdk_add_include is deprecated.

  Note:
    Assuming you have a foo.h in a bar library,
    calling this function lets you use:

      #include<foo.h>

    Instead of

      #include<bar/foo.h>

    Don't use that if you can fix the client code
    of the library !

  If you can not fix the client code, use the PATH_SUFFIXES argument of
  qi_stage_lib instead.

  Old:
    install_header(FOO SUBFOLDER bar foo.h)
    sdk_add_include(FOO bar)
    stage_lib(foo FOO)
  New:
    qi_stage_lib(foo PATH_SUFFIXES bar)
    qi_install_header(bar foo.h)
  ")
endfunction()

#####################
# Layout variables
#####################

# In theory those should not be used that often...
qi_set_global(_SDK_LIB           ${QI_SDK_LIB})
qi_set_global(_SDK_BIN           ${QI_SDK_BIN})
qi_set_global(_SDK_FRAMEWORK     ${QI_SDK_FRAMEWORK}    )
qi_set_global(_SDK_INCLUDE       ${QI_SDK_INCLUDE}      )
qi_set_global(_SDK_SHARE         ${QI_SDK_SHARE}        )
qi_set_global(_SDK_CONF          ${QI_SDK_CONF}         )
qi_set_global(_SDK_DOC           ${QI_SDK_DOC}          )
qi_set_global(_SDK_CMAKE         ${QI_SDK_CMAKE}        )
qi_set_global(_SDK_CMAKE_MODULES ${QI_SDK_CMAKE_MODULES})

qi_set_global(SDK_DIR ${QI_SDK_DIR})

function(win32_copy_target)
  qi_deprecated("win32_copy_target is deprecated.
  You sould even not have to call it now :)
  ")
endfunction()


######################
# Install
######################
function(install_header _staged_name)
  # old API:
  # install_header(STAGED_NAME [SUBFOLDER subfolder] [headers ...])
  # new API:
  # qi_install_header(subfolder [headers...])
  qi_deprecated("install_header is deprecated.
  Use qi_install_header instead
  Old:
    install_header(FOO SUBFOLDER foo foo.h)
  New:
    qi_install_header(foo foo.h)
  "
  )
  string(TOLOWER ${_staged_name} _targetname)
  cmake_parse_arguments(ARG "INCLUDEPATHEXPORT" "SUBFOLDER" "" ${ARGN})
  if(ARG_INCLUDEPATHEXPORT)
    qi_warning("
    Using  INCLUDEPATHEXPORT is not longer supported
    (problematic target: ${_targetname})
    Old:
      # include \"bar.h\"
    New:
      # include <${_targetname}/bar.h>
    "
    )
  endif()

  if(NOT ARG_SUBFOLDER)
    set(ARG_SUBFOLDER "")
  endif()

  qi_install_header(${ARG_SUBFOLDER} ${ARG_UNPARSED_ARGUMENTS})
endfunction()

function(install_data)
  qi_deprecated("install_data is deprecated.
  Use qi_install_data instead")
  qi_install_data(${ARGN})
endfunction()

function(install_data_dir _subfolder)
  qi_deprecated("no implementation")
endfunction()

function(install_doc)
  qi_deprecated("install_doc is deprecated.
  Use qi_install_doc instead")
  qi_install_doc(${ARGN})
endfunction()

function(install_conf)
  qi_deprecated("install_conf is deprecated.
  Use qi_install_conf instead")
  qi_install_conf(${ARGN})
endfunction()

function(install_cmake)
  qi_deprecated("install_cmake is deprecated.
  Use qi_install_cmake instead")
  qi_install_cmake(${ARGN})
endfunction()

######################
# Target
######################
function(create_bin)
  qi_deprecated("create_bin is deprecated:
    use qi_create_bin instead
  ")
  qi_create_bin(${ARGN})
endfunction()

function(create_script)
  qi_deprecated("create_script is deprecated:
    use qi_create_script instead")
  qi_create_script(${ARGN})
endfunction()

function(create_lib)
  qi_deprecated("create_lib is deprecated:
    use qi_create_lib instead")
  qi_create_lib(${ARGN})
endfunction()

function(create_config_h)
  qi_deprecated("create_config_h is deprecated:
    use qi_create_config_h instead")
  qi_create_config_h(_dummy ${ARGN})
endfunction()

function(create_gtest)
  qi_deprecated("create_gtest is deprecated:
    use qi_create_gtest instead")
  _fix_flags(_new_args DEPENDENCIES DEPENDS ${ARGN})
  qi_create_gtest(${_new_args})
endfunction()

function(create_cmake _NAME)
  qi_deprecated("create_cmake is deprecated
    use qi_stage_cmake instead.")
  qi_stage_cmake(${_NAME})
endfunction()

function(use module)
  # Some modules are now in qibuild/cmake, so
  # there is no need to find them anymore.
  set(_known_modules
    "PYTHON-TOOLS"
  )

  list(FIND _known_modules ${module} _index)

  if(NOT ${_index} EQUAL -1)
    qi_deprecated("use(${module}) is deprecated.
    This code has been put in qibuild/cmake.
    You can safely remove the call to this line now
    ")
    return()
  endif()

  # Small hack for QT-TOOLS
  if(${module} STREQUAL "QT-TOOLS")
    include(qibuild/modules/qt-tools)
    return()
  endif()


  qi_deprecated("use() is deprecated
   Simply use find_package() instead.
  Old:
    create_cmake(foo)
    use(foo)
  New:
    qi_stage_cmake(foo)
    find_package(foo)
  ")
  find_package(${module} REQUIRED)
endfunction()

function(use_lib)
  qi_deprecated("use_lib is deprecated.
    Note that the names can be target names.
    old:
      create_lib(foo foo.cpp)
      stage_lib(foo FOO)
      use_lib(bar FOO)
    new:
      qi_create_lib(foo foo.cpp)
      qi_stage_lib(foo)
      qi_use_lib(bar foo)
  ")

  cmake_parse_arguments(ARG "WINDOWS;MACOSX;LINUX" "" "" ${ARGN})

  if(ARG_WINDOWS OR ARG_MACOSX OR ARG_LINUX)
    qi_error("using use_lib with a \"platform\" flag is deprecated.
    Please use standard CMake code instead.
    old:
      use_lib(mylib LINUX bar WINDOWS foo MACOSX baz)
    new:
      if(UNIX)
        if(APPLE)
          qi_use_lib(mylib baz)
        else()
          qi_use_lib(mylib bar)
        endif()
      else()
        qi_use_lib(mylib foo)
      endif()

    ")
  endif()

  cmake_parse_arguments(ARG "REQUIRED" "" "" ${ARGN})
  if(ARG_REQUIRED)
    qi_warning("using use_lib() with a REQUIRED flag
    is no longer necessary.

    Note: optional dependencies are NOT supported in qibuild.

    Use something like:

        find_package(FOO)
        if(FOO_FOUND)
          qi_use_lib(bar foo)
        endif()

    if you really need optional dependencies.

    Note: the REQUIRED keyword is not used by use_lib() anyway ....
    "
    )
    qi_use_lib(${ARG_UNPARSED_ARGUMENTS})
    return()
  endif()


  qi_use_lib(${ARGN})

endfunction()

######################
# Log
######################
function(debug)
  qi_deprecated("debug is deprecated:
    Use qi_debug instead:
  ")
  qi_debug(${ARGN})
endfunction()

function(verbose)
  qi_deprecated("verbose is deprecated:
    Use qi_verbose instead:
  ")
  qi_verbose(${ARGN})
endfunction()

function(info)
  qi_deprecated("info is deprecated:
    Use qi_info instead:
  ")
  qi_info(${ARGN})
endfunction()

function(warning)
  qi_deprecated("warning is deprecated:
    Use qi_warning instead")
  qi_warning(${ARGN})
endfunction()

function(error)
  qi_deprecated("error is deprecated:
    Use qi_error instead")
  qi_error(${ARGN})
endfunction()

#####################
# stage
#####################
function(stage_lib _targetname _name)
  set(_need_other_name FALSE)
  qi_deprecated("stage_lib is deprecated:
    Use qi_stage_lib instead.
    Warning the signature has changed:
    Instead of:
      create_lib(foo foo.cpp)
      stage_lib(foo FOO)
    Use:
      qi_create_lib(foo foo.cpp)
      # No need for upper-case \"stage name\"
      # anymore:
      qi_stage_lib(foo)
  ")
  # old signature
  # stage_lib(target name [incdir ...] [DEFINITIONS def1])
  # new signature:
  # qi_stage_lib(name [INCLUDE_DIRS incdir ...] [DEFINITIONS def])

  string(TOUPPER ${_targetname} _U_targetname)
  if (NOT ${_U_targetname} STREQUAL ${_name})
    qi_deprecated("
      Not using stage_lib(foo FOO) where the second
      argument if not equals to the upper-version of the first
      argument is not supported anymore.
      Old:
        stage_lib(${_targetname} ${_name})
      New:
        stage_lib(${_targetname} ${_U_targetname})
    "
    )
    set(_need_other_name TRUE)
  endif()

  cmake_parse_arguments(ARG "" "" "DEFINITIONS" ${ARGN})
  set(_new_args
      ${_targetname}
      INCLUDE_DIRS ${ARG_UNPARSED_ARGUMENTS}
      DEFINITIONS ${ARG_DEFINITIONS}
  )
  if(_need_other_name)
    list(APPEND _new_args "STAGED_NAME" "${_name}")
  endif()

  qi_stage_lib(${_new_args})
endfunction()

function(stage_script _file _name)
  qi_deprecated("unimplemented")
endfunction()

function(stage_bin _targetname _name)
  qi_deprecated("unimplemented")
endfunction()

function(stage_header _name)
  qi_deprecated("unimplemented")
endfunction()

function(cond_subdirectory)
  qi_deprecated("cond_subdirectory is deprecated.
  Use qi_add_subdirectory() instead.")
  qi_add_subdirectory(${ARGN})
endfunction()


function(gen_trampoline _binary_name _trampo_name)
  qi_deprecated("unimplemented")
endfunction()

function(gen_sdk_trampoline _binary_name _trampo_name)
  qi_deprecated("unimplemented")
endfunction()

function(add_msvc_precompiled_header)
  qi_deprecated("not implemented yet")
endfunction()



#####################
# swig
#####################
function(wrap_python)
  qi_deprecated("wrap_python is deprecated.
  Instead of:
    use(PYTHON-TOOLS)
    wrap_python(foo foo.i
      SRCS foo.h
      DEPENDENCIES BAR
    )
  Use:
    include(qibuild/swig/python)
    qi_swig_wrap_python(foo foo.i
      SRCS foo.h
      DEPENDS BAR
    )
  "
  )
  include(qibuild/swig/python)
  _fix_flags(_new_args DEPENDENCIES DEPENDS ${ARGN})
  qi_swig_wrap_python(${_new_args})
endfunction()


#####################
# tests
#####################
function(configure_tests _name)
  if(BUILD_TESTS)
    include("${CMAKE_CURRENT_SOURCE_DIR}/${_name}")
  endif()
endfunction()

# Old undocumented functions. (Used for aldebaran's
# automatic testing only)
function(find)
endfunction()

function(gen_python_script)
endfunction()

function(add_python_test _name _pythonFile)
 add_test(${_name}  ${PYTHON_EXCUTABLE} ${_pythonFile} ${ARGN})
endfunction()

#copy file with dependency (if the file change in source => update the output)
function(copy_with_depend _src _dest)
  get_filename_component(_sname "${_src}"  NAME)
  get_filename_component(_dname "${_dest}" NAME)

  if (NOT EXISTS ${_src})
    if (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${_src})
      set(_src ${CMAKE_CURRENT_SOURCE_DIR}/${_src})
    endif()
  endif()

  #append the filename to the output filepath if necessary
  if (_dname STREQUAL "")
    set(_dest "${_dest}/${_sname}")
  endif()

  get_filename_component(_dirname "${_dest}" PATH)
  make_directory("${SDK_DIR}/${_dirname}/")

  configure_file("${_src}" "${SDK_DIR}/${_dest}" COPYONLY)
endfunction()
