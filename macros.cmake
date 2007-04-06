#
# Macros for cmake
#
%_cmake_lib_suffix64 -DLIB_SUFFIX=64
%__cmake %{_bindir}/cmake

%cmake \
  CFLAGS="${CFLAGS:-%optflags}" ; export CFLAGS ; \
  CXXFLAGS="${CXXFLAGS:-%optflags}" ; export CXXFLAGS ; \
  FFLAGS="${FFLAGS:-%optflags}" ; export FFLAGS ; \
  %__cmake \\\
%if "%{?_lib}" == "lib64" \
        %{?_cmake_lib_suffix64} \\\
%endif \
        -DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} \\\
        -DBUILD_SHARED_LIBS:BOOL=ON
