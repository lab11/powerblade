# Install script for directory: /home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils

# Set the install prefix
IF(NOT DEFINED CMAKE_INSTALL_PREFIX)
  SET(CMAKE_INSTALL_PREFIX "/usr/local")
ENDIF(NOT DEFINED CMAKE_INSTALL_PREFIX)
STRING(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
IF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  IF(BUILD_TYPE)
    STRING(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  ELSE(BUILD_TYPE)
    SET(CMAKE_INSTALL_CONFIG_NAME "Release")
  ENDIF(BUILD_TYPE)
  MESSAGE(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
ENDIF(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)

# Set the component getting installed.
IF(NOT CMAKE_INSTALL_COMPONENT)
  IF(COMPONENT)
    MESSAGE(STATUS "Install component: \"${COMPONENT}\"")
    SET(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  ELSE(COMPONENT)
    SET(CMAKE_INSTALL_COMPONENT)
  ENDIF(COMPONENT)
ENDIF(NOT CMAKE_INSTALL_COMPONENT)

# Install shared libraries without execute permission?
IF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  SET(CMAKE_INSTALL_SO_NO_EXE "1")
ENDIF(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)

IF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")
  FILE(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/cmake/PowerBlade_Utils" TYPE FILE FILES "/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/cmake/Modules/PowerBlade_UtilsConfig.cmake")
ENDIF(NOT CMAKE_INSTALL_COMPONENT OR "${CMAKE_INSTALL_COMPONENT}" STREQUAL "Unspecified")

IF(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/include/PowerBlade_Utils/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/lib/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/swig/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/python/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/grc/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/apps/cmake_install.cmake")
  INCLUDE("/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/docs/cmake_install.cmake")

ENDIF(NOT CMAKE_INSTALL_LOCAL_ONLY)

IF(CMAKE_INSTALL_COMPONENT)
  SET(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
ELSE(CMAKE_INSTALL_COMPONENT)
  SET(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
ENDIF(CMAKE_INSTALL_COMPONENT)

FILE(WRITE "/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/${CMAKE_INSTALL_MANIFEST}" "")
FOREACH(file ${CMAKE_INSTALL_MANIFEST_FILES})
  FILE(APPEND "/home/rohit507/Workspace/PowerBlade/software/GNURadio/gr-PowerBlade_Utils/build/${CMAKE_INSTALL_MANIFEST}" "${file}\n")
ENDFOREACH(file)
