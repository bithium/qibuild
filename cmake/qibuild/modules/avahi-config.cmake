## Copyright (C) 2011 Aldebaran Robotics



#get the root folder of this sdk
get_filename_component(_ROOT_DIR ${CMAKE_CURRENT_LIST_FILE} PATH)
set(TOOLCHAIN_PC_ROOT ${_ROOT_DIR}/../../)


clean(AVAHI)
fpath(AVAHI avahi-client/client.h PATH_SUFFIXES avahi)


flib(AVAHI avahi-common)
flib(AVAHI avahi-client)

export_lib(AVAHI)