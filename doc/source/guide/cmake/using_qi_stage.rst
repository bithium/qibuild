.. _using-qi-stage-lib:

Using qi_stage_lib
===================


Basic usage
------------

Using :cmake:function:`qi_stage_lib`: should "just works" when using a target created
with :cmake:function:`qi_create_lib`, provided that you call
``include_directories`` **before** staging the library:

.. code-block:: cmake


   include_directories(".")
   qi_create_lib(foo foo/foo.cpp foo/foo.hpp)
   qi_stage_lib(foo)

Advanced usage
---------------

As the documentation explains, :cmake:function:`qi_stage_lib` accepts various
argument, but most of them are guessed automatically.

Let us have a look on a few cases where what qibuild guesses can be wrong, and
how to fix it.

Using qi_stage_lib with custom DEPENDS
++++++++++++++++++++++++++++++++++++++

Let us assume you have a library named 'bar', depending on a private library named
'foo'.

Your CMake code may look like this:

.. code-block:: cmake

   qi_create_lib(bar bar/bar.hpp bar/bar.cpp)
   qi_stage_lib(bar)

   qi_create_lib(foo foo/foo.hpp foo/foo.cpp)
   qi_use_lib(foo bar)
   qi_stage_lib(foo)


By default, the generated ``foo-config.cmake`` file will contain
``FOO_DEPENDS=bar``, because of the call to :cmake:function:`qi_use_lib`

But if you really want to hide the ``bar`` dependency, you may build a package
for other people to use where ``bar`` is not even installed.

(The topic of private libraries is covered in the :ref:`qibuild-private-lib` section)

So here you must make sure that ``FOO_DEPENDS`` is empty in the generated
``foo-config.cmake`` file.

To do this, you should set the ``DEPENDS`` argument of :cmake:function`qi_stage_lib`, like this:

.. code-block:: cmake

   qi_stage_lib(foo DEPENDS "")


Using qi_stage_lib with INCLUDE_DIRS
+++++++++++++++++++++++++++++++++++++


This can happen for instance if you generate some headers at compile time, like this:


.. code-block:: cpp

    // -- in foo/config.in.hpp

    // Configured by cmake
    #cmakedefine SPAM

.. code-block:: cpp

    // -- in foo/foo.hpp
    #include <foo/config.hpp>


.. code-block:: cmake

    # Generate a header at configuration time, in the build directory:
    configure_file(config.in.hpp ${CMAKE_CURRENT_BINARY_DIR}/foo/config.hpp)

    # Make sure the generated header can be found:
    include_directories(${CMAKE_CURRENT_BINARY_DIR})

    include_directories(".")

    qi_create_lib(foo foo/foo.cpp foo/foo.hpp)

    qi_stage_lib(foo
      INCLUDE_DIRS ${CMAKE_CURRENT_BINARY_DIR}
                   ${CMAKE_CURRENT_SOURCE_DIR}
    )


From an other project, you may have a file looke like

.. code-block:: cpp

    # include <foo/foo.hpp>

    ...


So here to find ``foo/foo.hpp`` when using the project foo from **sources**, you
need to find ``/path/to/foo/src/libfoo/`` **and** ``/path/to/foo/build/``, because
of the path wehere ``foo/config.hpp`` has been generated.

Note that you have to use **absolute**  paths here, like any other
cmake code generated to be use from sources.



Using qi_stage_lib with PATH_SUFFIXES
+++++++++++++++++++++++++++++++++++++


Contrary to the previous section, this is useful when you want to use
foo from an **installed** package.

So let's assume your CMake looks like this:

.. code-block:: cmake

   qi_create_lib(foo foo/foo.hpp foo/foo.cpp)

   qi_install_header(foo/foo.hpp)

   qi_stage_lib(foo)


As explained in the :ref:`how-to-write-a-library` section, you have chosen
to have the ``foo.hpp`` header inside a nice ``foo/`` subdirectory.

But let's assume some other project uses ``#include <foo.hpp>`` directly.

They may not be willing to change their code just yet, but still be
willing to use the ``qibuild`` cmake framework.

You have several solutions here:

* Install a ``foo.hpp`` in ``<prefix>/include/foo.hpp`` looking like

.. code-block:: cpp

    #warning "Please include foo/foo.hpp instead of foo.hpp"
    #include <foo/foo.hpp>


* Use the ``PATH_SUFFIXES`` argument like this

.. code-block:: cmake

   qi_stage_lib(foo PATH_SUFFIXES foo)



Note that you have to use **relative**  paths here, like any other
cmake code that will end up being installed.
