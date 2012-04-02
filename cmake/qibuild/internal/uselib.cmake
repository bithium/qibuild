## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

if (_QI_USELIB_CMAKE_)
  return()
endif()
set(_QI_USELIB_CMAKE_ TRUE)
include(qibuild/internal/list)


# Set CMAKE_FIND_LIBRARY_SUFFIXES so that
# only static libs are searched when ${pkg}_STATIC
# is set.
# The _backup argument will be set to the previous
# value of CMAKE_FIND_LIBRARY_SUFFIXES.
# Don't forget to call _qi_disable_check_for_static(_backup)
# afterwards !
function(_qi_check_for_static pkg _backup)
  set(${_backup} ${CMAKE_FIND_LIBRARY_SUFFIXES} PARENT_SCOPE)
  if(${pkg}_STATIC)
    if(UNIX)
      set(CMAKE_FIND_LIBRARY_SUFFIXES ".a" PARENT_SCOPE)
    endif()
  endif()
endfunction()

function(_qi_disable_check_for_static _backup)
  set(CMAKE_FIND_LIBRARY_SUFFIXES "${_backup}" PARENT_SCOPE)
endfunction()


#compute the dependencies list, removing duplicate
function(_qi_use_lib_get_deps name _OUT_list)
  set(_result ${ARGN})
  list(LENGTH _result _count)
  if (_count EQUAL 0)
    return()
  endif()

  string(TOUPPER ${name} _U_NAME)

  foreach(_pkg ${ARGN})
    string(TOUPPER ${_pkg} _U_PKG)
    # First, we search for *-config.cmake files
    # generated by qiBuild, then we look
    # for upstream Find-*.cmake
    # See: http://www.cmake.org/cmake/help/cmake-2-8-docs.html#command:find_package
    if (NOT ${_U_PKG}_SEARCHED AND NOT ${_U_PKG}_PACKAGE_FOUND)

      _qi_check_for_static("${_U_PKG}" _backup_static)

      # find_package in two calls. The first call:
      # Uses NO_MODULE - looks for PKGConfig.cmake, not FindPKG.cmake
      # Uses QUIET     - no warning will be generated
      # If Config is found, then PKG_DIR will be set so that the following
      # find_package knows where to look
      find_package(${_U_PKG} NO_MODULE QUIET)
      # _PACKAGE_FOUND is only set when using qibuild/cmake modules,
      # see comments in find.cmake for details.
      if(NOT ${_U_PKG}_PACKAGE_FOUND)
        find_package(${_U_PKG} QUIET REQUIRED)
      endif()

      _qi_disable_check_for_static("${_backup_static}")

      qi_set_global("${_U_PKG}_SEARCHED" TRUE)
    endif()

    foreach(_sub_dep ${${_U_PKG}_DEPENDS})
      _qi_use_lib_get_deps("${_U_PKG}" _new_deps "${_sub_dep}")
      list(APPEND _result ${_new_deps})
    endforeach()
  endforeach()

  #We remove duplicate here..
  #Problem: If libA and libB each depends on libC, we will have "A C B C".
  # libC need to be after libA and libB, so we need to take each libC occurence into acount,
  # in fact, we could optimise if we want and only take the last one,
  # but REMOVE_DUPLICATES keep the first occurence
  # so ... we reverse the list, remove duplicate and reverse again!
  list(REVERSE _result)
  list(REMOVE_DUPLICATES _result)
  list(REVERSE _result)

  set(${_OUT_list} ${_result} PARENT_SCOPE)
endfunction()


#! Find dependencies and add them to the target <name>.
#
# This will call include_directories with XXX_INCLUDE_DIRS or fallback to XXX_INCLUDE_DIR.
# This will call target_link_libraries with XXX_LIBRARIES or fallback to XXX_LIBRARY.
# All dependencies should be found, otherwize it will fail. If you want to check if a
# package could be found, prefer using find_package.
#
# to search for static libs set XXX_STATIC=ON before calling qi_use_lib.
#
# \arg:name The target to add dependencies to
# \argn: dependencies, like the DEPENDS group, argn and DEPENDS will be merged
# \group:DEPENDS The list of dependencies
function(_qi_use_lib_internal name)
  STRING(REGEX MATCH "@" _at_in_name ${name})
  if("${_at_in_name}" STREQUAL "@")
    qi_error("Invalid target name: ${name}.
    Target names must not contain the '@' character
    ")
  endif()
  cmake_parse_arguments(ARG "" "" "DEPENDS" ${ARGN})
  set(ARG_DEPENDS ${ARG_UNPARSED_ARGUMENTS} ${ARG_DEPENDS})
  string(TOUPPER "${name}" _U_name)

  # Compute a key to store the call of this function,
  # using '@' as a separator
  set(_key "_QI_USE_LIB_${_U_name}")
  foreach(_arg ${ARG_DEPENDS})
    set(_key "${_key}@${_arg}")
  endforeach()

  if(DEFINED ${_key})
    # qi_use_lib already put in cache
  else()
    _qi_use_lib_get_deps("${name}" _DEPS ${ARG_DEPENDS})
    qi_set_advanced_cache("${_key}" ${_DEPS})
    # Append the new deps to the list of previous deps:
    set(_new_deps ${${_U_name}_DEPENDS} ${_DEPS})
    # reverse, remove duplicated and reverse again:
    if(_new_deps)
      list(REVERSE _new_deps)
      list(REMOVE_DUPLICATES _new_deps)
      list(REVERSE _new_deps)
    endif()
    qi_set_advanced_cache("${_U_name}_DEPENDS" ${_new_deps})
  endif()

  foreach(_pkg ${${_key}})
    string(TOUPPER ${_pkg} _U_PKG)

    if (DEFINED ${_U_PKG}_INCLUDE_DIRS)
      include_directories(${${_U_PKG}_INCLUDE_DIRS})
    elseif(DEFINED ${_U_PKG}_INCLUDE_DIR)
      include_directories(${${_U_PKG}_INCLUDE_DIR})
    endif()

    if (DEFINED ${_U_PKG}_LIBRARIES)
      target_link_libraries("${name}" ${${_U_PKG}_LIBRARIES})
    elseif (DEFINED ${_U_PKG}_LIBRARY)
      target_link_libraries("${name}" ${${_U_PKG}_LIBRARY})
    endif()

    # local lib are staged with _U_PKG_TARGET = localtargetname, this allow dependencies
    # between local libs
    if ( (DEFINED "${_U_PKG}_TARGET") AND (TARGET "${${_U_PKG}_TARGET}") )
      add_dependencies(${name} "${${_U_PKG}_TARGET}")
    endif()
    if(${_U_PKG}_DEFINITIONS)
      # Append the correct compile definitions to the target
      set(_to_add)
      get_target_property(_compile_defs ${name} COMPILE_DEFINITIONS)
      if(_compile_defs)
        set(_to_add ${_compile_defs})
      endif()
      _qi_list_append_uniq(_to_add "${${_U_PKG}_DEFINITIONS}")
      if(_to_add)
        set_target_properties(${name}
          PROPERTIES
            COMPILE_DEFINITIONS "${_to_add}")
      endif()
    endif()
  endforeach()
endfunction()
