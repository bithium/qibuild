## Copyright (C) 2011 Aldebaran Robotics

#get the root folder of this sdk
get_filename_component(_ROOT_DIR ${CMAKE_CURRENT_LIST_FILE} PATH)
include("${_ROOT_DIR}/../boostutils.cmake")

set(_libname "date_time")
set(_suffix "DATE_TIME")

clean(BOOST_${_suffix}-STATIC)
fpath(BOOST_${_suffix}-STATIC boost)

boost_flib_static(${_suffix}-STATIC ${_libname})
boost_flib_static(${_suffix}-STATIC "system")

export_lib(BOOST_${_suffix}-STATIC)