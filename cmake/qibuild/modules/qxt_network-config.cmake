##
## Copyright (C) 2011 Aldebaran Robotics
##

clean(QXT_NETWORK)
fpath(QXT_NETWORK qxtnetwork.h PATH_SUFFIXES qxt/QxtNetwork QxtNetwork)
fpath(QXT_NETWORK QxtNetwork PATH_SUFFIXES qxt)
flib(QXT_NETWORK QxtNetwork)
export_lib(QXT_NETWORK)
qi_set_global(QXT_NETWORK_DEPENDS "QXT_CORE" "QT_QTNETWORK")
