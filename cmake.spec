# Set to bcond_without or use --with bootstrap if bootstrapping a new release
# or architecture
%bcond_with bootstrap
# Set to bcond_with or use --without gui to disable qt4 gui build
%bcond_without gui
# Set to RC version if building RC, else %{nil}
%define rcver %{nil}

%define rpm_macros_dir %{_sysconfdir}/rpm
%if 0%{?fedora} || 0%{?rhel} >= 7
%define rpm_macros_dir %{_rpmconfigdir}/macros.d
%endif

%if 0%{?fedora} < 23
%bcond_with python3
%else
%bcond_without python3
%endif

Name:           cmake
Version:        3.4.2
Release:        1%{?dist}
Summary:        Cross-platform make system

Group:          Development/Tools
# most sources are BSD
# Source/CursesDialog/form/ a bunch is MIT 
# Source/kwsys/MD5.c is zlib 
# some GPL-licensed bison-generated files, these all include an exception granting redistribution under terms of your choice
License:        BSD and MIT and zlib
URL:            http://www.cmake.org
Source0:        http://www.cmake.org/files/v3.4/cmake-%{version}%{?rcver}.tar.gz
Source1:        cmake-init.el
Source2:        macros.cmake
# See https://bugzilla.redhat.com/show_bug.cgi?id=1202899
Source3:        cmake.attr
Source4:        cmake.prov
# Patch to find DCMTK in Fedora (bug #720140)
Patch0:         cmake-dcmtk.patch
# Patch to fix RindRuby vendor settings
# http://public.kitware.com/Bug/view.php?id=12965
# https://bugzilla.redhat.com/show_bug.cgi?id=822796
Patch2:         cmake-findruby.patch

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  gcc-gfortran
BuildRequires:  ncurses-devel, libX11-devel
BuildRequires:  bzip2-devel
BuildRequires:  curl-devel
BuildRequires:  expat-devel
BuildRequires:  jsoncpp-devel
BuildRequires:  libarchive-devel
BuildRequires:  /usr/bin/sphinx-build
BuildRequires:  xz-devel
BuildRequires:  zlib-devel
BuildRequires:  emacs
%if %{with python3}
%{!?python3_pkgversion: %global python3_pkgversion 3}
BuildRequires:  python%{python3_pkgversion}-devel
%else
BuildRequires:  python2-devel
%endif
%if %{without bootstrap}
#BuildRequires: xmlrpc-c-devel
%endif
%if %{with gui}
BuildRequires: pkgconfig(Qt5)
BuildRequires: desktop-file-utils
%define qt_gui --qt-gui
%endif

Requires:       rpm

%if 0%{?fedora} || 0%{?rhel} >= 7
Requires: emacs-filesystem >= %{_emacs_version}
%endif

# Source/kwsys/MD5.c
# see https://fedoraproject.org/wiki/Packaging:No_Bundled_Libraries
Provides: bundled(md5-deutsch)

# https://fedorahosted.org/fpc/ticket/555
Provides: bundled(kwsys)

%description
CMake is used to control the software compilation process using simple 
platform and compiler independent configuration files. CMake generates 
native makefiles and workspaces that can be used in the compiler 
environment of your choice. CMake is quite sophisticated: it is possible 
to support complex environments requiring system configuration, preprocessor
generation, code generation, and template instantiation.


%package        doc
Summary:        Documentation for %{name}
Group:          Development/Tools
Requires:       %{name} = %{version}-%{release}

%description    doc
This package contains documentation for CMake.


%package        gui
Summary:        Qt GUI for %{name}
Group:          Development/Tools
Requires:       %{name} = %{version}-%{release}

%description    gui
The %{name}-gui package contains the Qt based GUI for CMake.


%prep
%setup -q -n %{name}-%{version}%{?rcver}
# We cannot use backups with patches to Modules as they end up being installed
%patch0 -p1
%patch2 -p1

%if %{with python3}
echo '#!%{__python3}' > cmake.prov
%else
echo '#!%{__python2}' > cmake.prov
%endif
tail -n +2 %{SOURCE4} >> cmake.prov


%build
export CFLAGS="%{optflags}"
export CXXFLAGS="%{optflags}"
export LDFLAGS="%{__global_ldflags}"
mkdir build
pushd build
../bootstrap --prefix=%{_prefix} --datadir=/share/%{name} \
             --docdir=/share/doc/%{name} --mandir=/share/man \
             --%{?with_bootstrap:no-}system-libs \
             --parallel=`/usr/bin/getconf _NPROCESSORS_ONLN` \
             --sphinx-man \
             %{?qt_gui}
make VERBOSE=1 %{?_smp_mflags}


%install
pushd build
make install DESTDIR=%{buildroot}
find %{buildroot}/%{_datadir}/%{name}/Modules -type f | xargs chmod -x
[ -n "$(find %{buildroot}/%{_datadir}/%{name}/Modules -name \*.orig)" ] &&
  echo "Found .orig files in %{_datadir}/%{name}/Modules, rebase patches" &&
  exit 1
popd
# Install bash completion symlinks
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
for f in %{buildroot}%{_datadir}/%{name}/completions/*
do
  ln -s ../../%{name}/completions/$(basename $f) %{buildroot}%{_datadir}/bash-completion/completions/
done
# Install emacs cmake mode
mkdir -p %{buildroot}%{_emacs_sitelispdir}/%{name}
install -p -m 0644 Auxiliary/cmake-mode.el %{buildroot}%{_emacs_sitelispdir}/%{name}/
%{_emacs_bytecompile} %{buildroot}%{_emacs_sitelispdir}/%{name}/cmake-mode.el
mkdir -p %{buildroot}%{_emacs_sitestartdir}
install -p -m 0644 %SOURCE1 %{buildroot}%{_emacs_sitestartdir}/
# RPM macros
install -p -m0644 -D %{SOURCE2} %{buildroot}%{rpm_macros_dir}/macros.cmake
sed -i -e "s|@@CMAKE_VERSION@@|%{version}|" %{buildroot}%{rpm_macros_dir}/macros.cmake
touch -r %{SOURCE2} %{buildroot}%{rpm_macros_dir}/macros.cmake
%if 0%{?_rpmconfigdir:1}
# RPM auto provides
install -p -m0644 -D %{SOURCE3} %{buildroot}%{_prefix}/lib/rpm/fileattrs/cmake.attr
install -p -m0755 -D cmake.prov %{buildroot}%{_prefix}/lib/rpm/cmake.prov
%endif
mkdir -p %{buildroot}%{_libdir}/%{name}
# Install copyright files for main package
cp -p Copyright.txt %{buildroot}/%{_docdir}/%{name}/
find Source Utilities -type f -iname copy\* | while read f
do
  fname=$(basename $f)
  dir=$(dirname $f)
  dname=$(basename $dir)
  cp -p $f %{buildroot}/%{_docdir}/%{name}/${fname}_${dname}
done

%if %{with gui}
# Desktop file
desktop-file-install --delete-original \
  --dir=%{buildroot}%{_datadir}/applications \
  %{buildroot}/%{_datadir}/applications/CMake.desktop

# Register as an application to be visible in the software center
#
# NOTE: It would be *awesome* if this file was maintained by the upstream
# project, translated and installed into the right place during `make install`.
#
# See http://www.freedesktop.org/software/appstream/docs/ for more details.
#
mkdir -p %{buildroot}%{_datadir}/appdata
cat > %{buildroot}%{_datadir}/appdata/CMake.appdata.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!-- Copyright 2014 Ryan Lerch <rlerch@redhat.com> -->
<!--
EmailAddress: kitware@kitware.com
SentUpstream: 2014-09-17
-->
<application>
  <id type="desktop">CMake.desktop</id>
  <metadata_license>CC0-1.0</metadata_license>
  <name>CMake GUI</name>
  <summary>Create new CMake projects</summary>
  <description>
    <p>
      CMake is an open source, cross platform build system that can build, test,
      and package software. CMake GUI is a graphical user interface that can
      create and edit CMake projects.
    </p>
  </description>
  <url type="homepage">http://www.cmake.org</url>
  <screenshots>
    <screenshot type="default">https://raw.githubusercontent.com/hughsie/fedora-appstream/master/screenshots-extra/CMake/a.png</screenshot>
  </screenshots>
  <!-- FIXME: change this to an upstream email address for spec updates
  <updatecontact>someone_who_cares@upstream_project.org</updatecontact>
   -->
</application>
EOF

%endif


%check
unset DISPLAY
pushd build
#CMake.FileDownload, and CTestTestUpload require internet access
bin/ctest -V -E 'CMake.FileDownload|CTestTestUpload' %{?_smp_mflags}
popd


%if %{with gui}
%post gui
update-desktop-database &> /dev/null || :
/bin/touch --no-create %{_datadir}/mime || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun gui
update-desktop-database &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/mime || :
    update-mime-database %{?fedora:-n} %{_datadir}/mime &> /dev/null || :
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans gui
update-mime-database %{?fedora:-n} %{_datadir}/mime &> /dev/null || :
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
%endif


%files
%dir %{_docdir}/%{name}
%{_docdir}/%{name}/Copyright.txt*
%{_docdir}/%{name}/COPYING*
%{rpm_macros_dir}/macros.cmake
%if 0%{?_rpmconfigdir:1}
%{_prefix}/lib/rpm/fileattrs/cmake.attr
%{_prefix}/lib/rpm/cmake.prov
%endif
%{_bindir}/ccmake
%{_bindir}/cmake
%{_bindir}/cpack
%{_bindir}/ctest
%{_datadir}/aclocal/cmake.m4
%{_datadir}/bash-completion/
%{_datadir}/%{name}/
%{_mandir}/man1/ccmake.1.gz
%{_mandir}/man1/cmake.1.gz
%{_mandir}/man1/cpack.1.gz
%{_mandir}/man1/ctest.1.gz
%{_mandir}/man7/*.7.gz
%{_emacs_sitelispdir}/%{name}
%{_emacs_sitestartdir}/%{name}-init.el
%{_libdir}/%{name}/

%files doc
%{_docdir}/%{name}/

%if %{with gui}
%files gui
%{_bindir}/cmake-gui
%{_datadir}/appdata/*.appdata.xml
%{_datadir}/applications/CMake.desktop
%{_datadir}/mime/packages/cmakecache.xml
%{_datadir}/icons/hicolor/*/apps/CMakeSetup.png
%{_mandir}/man1/cmake-gui.1.gz
%endif


%changelog
* Tue Jan 19 2016 Orion Poplawski <orion@cora.nwra.com> - 3.4.2-1
- Update to 3.4.2

* Sat Dec 12 2015 Ville Skyttä <ville.skytta@iki.fi> - 3.4.1-4
- Use Python 3 on F-23+

* Tue Dec 8 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.1-3
- Use Qt5 for gui

* Mon Dec 7 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.1-2
- Fixup some conditionals for RHEL7

* Wed Dec 2 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.1-1
- Update to 3.4.1

* Wed Nov 25 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.0-2
- BR /usr/bin/sphinx-build instead of python-sphinx

* Tue Nov 17 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.0-1
- Update to 3.4.0 final

* Thu Nov 5 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.0-0.3.rc3
- Update to 3.4.0-rc3

* Wed Oct 21 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.0-0.2.rc2
- Update to 3.4.0-rc2

* Tue Oct 6 2015 Orion Poplawski <orion@cora.nwra.com> - 3.4.0-0.1.rc1
- Update to 3.4.0-rc1

* Tue Oct 6 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.2-2
- Add upstream patch to find python 3.5 (bug #1269095)

* Thu Sep 17 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.2-1
- Update to 3.3.2
- Use %%{__global_ldflags}
- Fix test exclusion

* Fri Sep 11 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.1-5
- Apply upstream patch to fix Fortran linker detection with redhat-hardened-ld
  (bug #1260490)

* Wed Sep 9 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.1-4
- Apply upstream patch to fix trycompile output (bug #1260490)

* Tue Aug 25 2015 Rex Dieter <rdieter@fedoraproject.org> 3.3.1-3
- pull in some upstream fixes (FindPkgConfig,boost-1.59)

* Fri Aug 21 2015 Rex Dieter <rdieter@fedoraproject.org> 3.3.1-2
- Provides: bundled(kwsys)

* Thu Aug 13 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.1-1
- Update to 3.3.1

* Thu Jul 23 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.0-1
- Update to 3.3.0

* Thu Jul 9 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.0-0.4.rc3
- Update to 3.3.0-rc3
- Fix cmake.attr to handle 32-bit libraries

* Tue Jun 23 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.0-0.3.rc2
- Update to 3.3.0-rc2

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.3.0-0.2.rc1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jun 8 2015 Orion Poplawski <orion@cora.nwra.com> - 3.3.0-0.1.rc1
- Update to 3.3.0-rc1

* Mon Jun 8 2015 Orion Poplawski <orion@cora.nwra.com> - 3.2.3-1
- Update to 3.2.3

* Wed Apr 15 2015 Orion Poplawski <orion@cora.nwra.com> - 3.2.2-1
- Update to 3.2.2

* Thu Mar 26 2015 Richard Hughes <rhughes@redhat.com> - 3.2.1-5
- Add an AppData file for the software center

* Mon Mar 23 2015 Daniel Vrátil <dvratil@redhat.com> - 3.2.1-4
- cmake.prov: handle exceptions

* Wed Mar 18 2015 Rex Dieter <rdieter@fedoraproject.org> 3.2.1-3
- cmake.prov: use /usr/bin/python (instead of /bin/python)

* Tue Mar 17 2015 Rex Dieter <rdieter@fedoraproject.org> 3.2.1-2
- RFE: CMake automatic RPM provides  (#1202899)

* Wed Mar 11 2015 Orion Poplawski <orion@cora.nwra.com> - 3.2.1-1
- Update to 3.2.1

* Thu Feb 26 2015 Orion Poplawski <orion@cora.nwra.com> - 3.2.0-0.2.rc2
- Update to 3.2.0-rc2
- Drop C++11 ABI workaround, fixed in gcc
- Drop strict_aliasing patch fixed upstream long ago
- Drop FindLua52, FindLua should work now for 5.1-5.3

* Sun Feb 15 2015 Orion Poplawski <orion@cora.nwra.com> - 3.2.0-0.1.rc1
- Update to 3.2.0-rc1
- Drop ninja patch fixed upstream
- Upstream now ships icons, add icon-cache scriptlets

* Fri Feb 13 2015 Orion Poplawski <orion@cora.nwra.com> - 3.1.3-1
- Update to 3.1.3

* Sat Feb 7 2015 Orion Poplawski <orion@cora.nwra.com> - 3.1.2-1
- Update to 3.1.2

* Fri Jan 23 2015 Orion Poplawski <orion@cora.nwra.com> - 3.1.1-1
- Update to 3.1.1
- Drop ruby patch applied upstream

* Sat Jan 17 2015 Mamoru TASAKA <mtasaka@fedoraproject.org> - 3.1.0-2
- Fix ruby 2.2.0 teeny (0) detection

* Wed Dec 17 2014 Orion Poplawski <orion@cora.nwra.com> - 3.1.0-1
- Update to 3.1.0 final

* Sat Nov 15 2014 Orion Poplawski <orion@cora.nwra.com> - 3.1.0-0.2.rc2
- Update to 3.1.0-rc2

* Wed Oct 29 2014 Orion Poplawski <orion@cora.nwra.com> - 3.1.0-0.1.rc1
- Update to 3.1.0-rc1

* Mon Sep 15 2014 Dan Horák <dan[at]danny.cz> - 3.0.2-2
- fix FindJNI for ppc64le (#1141782)

* Sun Sep 14 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.2-1
- Update to 3.0.2

* Mon Aug 25 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.1-3
- Update wxWidgets patches

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Wed Aug 6 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.1-1
- Update to 3.0.1

* Thu Jul 03 2014 Rex Dieter <rdieter@fedoraproject.org> 3.0.0-2
- optimize mimeinfo scriptlet

* Sat Jun 14 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-1
- Update to 3.0.0 final

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.0.0-0.11.rc6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue May 27 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.10.rc6
- Update to 3.0.0-rc6

* Wed May 14 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.9.rc5
- Update to 3.0.0-rc5
- Drop icon patch applied upstream

* Tue Apr 22 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.8.rc4
- Update to 3.0.0-rc4

* Thu Apr 10 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.7.rc3
- Fix doc duplication

* Fri Apr 4 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.6.rc3
- Rebase patches to prevent .orig files in Modules
- Add install check for .orig files

* Wed Mar 26 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.5.rc3
- Update to 3.0.0-rc3
- Add patch to fix FindwxWidgets when cross-compiling for Windows (bug #1081207)

* Wed Mar 5 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.4.rc1
- Add additional FindPythonLibs patch from upstream (bug #1072964)

* Mon Mar 3 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.3.rc1
- Update to upstreams version of FindPythonLibs patch

* Mon Mar 3 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.2.rc1
- Use symlinks for bash completions

* Fri Feb 28 2014 Orion Poplawski <orion@cora.nwra.com> - 3.0.0-0.1.rc1
- Update to 3.0.0-rc1
- Update qtdeps patch to upstreamed version
- Install bash completions

* Tue Feb 11 2014 Orion Poplawski <orion@cora.nwra.com> - 2.8.12.2-2
- Add upstream patch to find Boost MPI library (bug #756141)

* Tue Jan 28 2014 Orion Poplawski <orion@cora.nwra.com> - 2.8.12.2-1
- Update to 2.8.12.2

* Wed Jan 22 2014 Orion Poplawski <orion@cora.nwra.com> - 2.8.12.1-2
- Fix FindFreetype for 2.5.1+

* Wed Nov 6 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12.1-1
- Update to 2.8.12.1

* Wed Oct 23 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-3
- Remove UseQt4 automatic dependency adding

* Thu Oct 10 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-2
- Autoload cmake-mode in emacs (bug #1017779)

* Tue Oct 8 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-1
- Update to 2.8.12 final

* Tue Oct 1 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.6.rc4
- Update to 2.8.12-rc4
- Drop upstreamed FindHD5 patch

* Thu Sep 19 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.5.rc3
- Add patch to fix FindHDF5

* Tue Sep 17 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.4.rc3
- Update to 2.8.12-rc3

* Wed Sep 4 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.3.rc2
- Update to 2.8.12-rc2

* Wed Aug 28 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.2.rc1
- Add patch to fix FindPythonLibs issues (bug #876118)
- Split docs into separate -doc sub-package

* Mon Aug 26 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.12-0.1.rc1
- Update to 2.8.12-rc1
- Drop ImageMagick patch - not needed

* Fri Jul 26 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11.2-4
- Use version-less docdir

* Thu Jul 25 2013 Petr Machata <pmachata@redhat.com> - 2.8.11.2-3
- Icon name in desktop file should be sans .png extension.

* Thu Jul 25 2013 Petr Machata <pmachata@redhat.com> - 2.8.11.2-2
- Pass -fno-strict-aliasing to cm_sha2.c to avoid strict aliasing
  problems that GCC warns about.

* Tue Jul 9 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11.2-1
- Update to 2.8.11.2 release

* Mon Jun 10 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11.1-1
- Update to 2.8.11.1 release

* Sat May 18 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-1
- Update to 2.8.11 release

* Mon May 13 2013 Tom Callaway <spot@fedoraproject.org> - 2.8.11-0.9.rc4
- add FindLua52.cmake

* Thu May 9 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-0.8.rc4
- Update to 2.8.11-rc4

* Fri Apr 19 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-0.7.rc3
- Update to 2.8.11-rc3

* Thu Apr 18 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-0.6.rc2
- Drop -O3 from default release build type flags in cmake rpm macro (bug 875954)

* Wed Apr 17 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-0.5.rc2
- Update to 2.8.11-rc2
- Rebase ImageMagick patch

* Mon Mar 18 2013 Rex Dieter <rdieter@fedoraproject.org> 2.8.11-0.4.rc1
- respin cmake-2.8.11-rc1-IM_pkgconfig_hints.patch
- drop/omit backup files when applying patches

* Sat Mar 16 2013 Rex Dieter <rdieter@fedoraproject.org> 2.8.11-0.3.rc1
- Patch FindImageMagick.cmake for newer ImageMagick versions

* Sat Mar 16 2013 Rex Dieter <rdieter@fedoraproject.org> 2.8.11-0.2.rc1
- use %%{_rpmconfigdir}/macros.d on f19+

* Fri Mar 15 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.11-0.1.rc1
- Update to 2.8.11-rc1
- Drop upstream ccmake and usrmove patches

* Wed Mar 13 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.10.2-5
- Add patch from upstream to fix UsrMove handling (bug #917407)
- Drop %%config from rpm macros
- Define FCFLAGS in cmake macro

* Fri Feb 8 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.10.2-4
- Add patch to use ninja-build (bug #886184)

* Thu Jan 24 2013 Orion Poplawski <orion@cora.nwra.com> - 2.8.10.2-3
- Update FindPostgreSQL patch to use PostgreSQL_LIBRARY (bug #903757)

* Thu Jan 17 2013 Tomas Bzatek <tbzatek@redhat.com> - 2.8.10.2-2
- Rebuilt for new libarchive

* Tue Nov 27 2012 Rex Dieter <rdieter@fedoraproject.org> 2.8.10.2-1
- 2.8.10.2

* Thu Nov 8 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.10.1-1
- Update to 2.8.10.1

* Thu Nov 1 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.10-1
- Update to 2.8.10 final

* Thu Oct 25 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.10-0.2.rc3
- Add patch to fix DEL key in ccmake (bug 869769)

* Wed Oct 24 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.10-0.1.rc3
- Update to 2.8.10 RC 3
- Rebase FindRuby and FindPostgreSQL patches

* Thu Aug 9 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.9-1
- Update to 2.8.9 final

* Fri Jul 27 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.9-0.4.rc3
- Update to 2.8.9 RC 3

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.9-0.3.rc2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 16 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.9-0.2.rc2
- Update to 2.8.9 RC 2

* Tue Jul 10 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.9-0.1.rc1
- Update to 2.8.9 RC 1
- Drop pkgconfig patch

* Thu Jul 5 2012 Orion Poplawski <orion@cora.nwra.com> 2.8.8-5
- Add patch to fix FindPostgreSQL (bug 828467)

* Mon May 21 2012 Orion Poplawski <orion@cora.nwra.com> 2.8.8-4
- Add patch to fix FindRuby (bug 822796)

* Thu May 10 2012 Rex Dieter <rdieter@fedoraproject.org> 2.8.8-3
- Incorrect license tag in spec file (#820334)

* Thu May 3 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.8-2
- Comply with Emacs packaging guidlines (bug #818658)

* Thu Apr 19 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.8-1
- Update to 2.8.8 final

* Sat Apr 14 2012 Rex Dieter <rdieter@fedoraproject.org> 2.8.8-0.4.rc2
- adjust pkgconfig patch (#812188)

* Fri Apr 13 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.8-0.3.rc2
- Add upstream patch to set PKG_CONFIG_FOUND (bug #812188)

* Mon Apr 9 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.8-0.2.rc2
- Update to 2.8.8 RC 2

* Fri Mar 23 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.8-0.1.rc1
- Update to 2.8.8 RC 1

* Tue Feb 21 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.7-6
- Just strip CMAKE_INSTALL_LIBDIR from %%cmake macro

* Tue Feb 21 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.7-5
- Strip CMAKE_INSTALL_LIBDIR and others from %%cmake macro (bug 795542)

* Thu Jan 26 2012 Tomas Bzatek <tbzatek@redhat.com> - 2.8.7-4
- Rebuilt for new libarchive

* Wed Jan 18 2012 Jaroslav Reznik <jreznik@redhat.com> - 2.8.7-3
- Rebuild for libarchive

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Sun Jan 1 2012 Orion Poplawski <orion@cora.nwra.com> - 2.8.7-1
- Update to 2.8.7 final

* Tue Dec 27 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.7-0.2.rc2
- Update to 2.8.7 RC 2

* Tue Dec 13 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.7-0.1.rc1
- Update to 2.8.7 RC 1

* Tue Nov 15 2011 Daniel Drake <dsd@laptop.org> - 2.8.6-2
- Rebuild for libarchive.so.11

* Wed Oct 5 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.6-1
- Update to 2.8.6 final

* Thu Sep 22 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.6-0.5.rc4
- Update to 2.8.6 RC 4

* Tue Sep 13 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.6-0.4.rc3
- Update to 2.8.6 RC 3

* Sun Sep 11 2011 Ville Skyttä <ville.skytta@iki.fi> - 2.8.6-0.3.rc2
- Sync FFLAGS and LDFLAGS in the %%cmake macro with redhat-rpm-config.

* Tue Sep 6 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.6-0.2.rc2
- Update to 2.8.6 RC 2
- Drop aclocal patch

* Mon Aug 29 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.6-0.1.rc1
- Update to 2.8.6 RC 1
- Update dcmtk patch
- Add upstream patch to fix aclocal install location

* Thu Jul 28 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-3
- Updated patch to find dcmtk in Fedora (Bug #720140)

* Fri Jul 22 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-2
- Add patch to find dcmtk in Fedora (Bug #720140)

* Fri Jul 22 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-1
- Update to 2.8.5 final
- Drop issue 12307 patch

* Thu Jul 21 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-0.3.rc3
- Update to 2.8.5 RC 3
- Drop upstreamed swig patch
- Apply upstream fix for issue 12307 (bug #723652)

* Mon Jun 20 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-0.2.rc2
- Update to 2.8.5 RC 2
- Add patch from upstream to fix FindSWIG

* Tue May 31 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.5-0.1.rc1
- Update to 2.8.5 RC 1
- Disable CTestTestUpload test, needs internet access

* Thu Feb 17 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.4-1
- Update to 2.8.4 final

* Wed Feb 2 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.4-0.2.rc2
- Update to 2.8.4 RC 2

* Tue Jan 18 2011 Orion Poplawski <orion@cora.nwra.com> - 2.8.4-0.1.rc1
- Update to 2.8.4 RC 1
- Drop qt4 patch

* Thu Dec 16 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.3-2
- Add patch from upstream git to fix bug 652886 (qt3/qt4 detection)

* Thu Nov 4 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.3-1
- Update to 2.8.3 final

* Mon Nov 1 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.3-0.3.rc4
- Update to 2.8.3 RC 4
- Drop python 2.7 patch fixed upstream
- No need to fixup source file permissions anymore

* Fri Oct 22 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.3-0.2.rc3
- Update to 2.8.3 RC 3

* Thu Sep 16 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.3-0.1.rc1
- Update to 2.8.3 RC 1
- Add BR bzip2-devel and libarchive-devel

* Fri Jul 23 2010 Kevin Kofler <Kevin@tigcc.ticalc.org> - 2.8.2-2
- add support for Python 2.7 to FindPythonLibs.cmake (Orcan Ogetbil)

* Tue Jul 6 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.2-1
- Update to 2.8.2 final

* Thu Jun 24 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.2-0.3.rc4
- Update to 2.8.2 RC 4

* Wed Jun 23 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.2-0.2.rc3
- Update to 2.8.2 RC 3

* Mon Jun 21 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.2-0.1.rc2
- Update to 2.8.2 RC 2

* Thu Jun 3 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-5
- Upstream published a newer 2.8.1 tar ball

* Wed Jun 2 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-4
- Add BR gcc-gfortran so Fortran support is built

* Wed Apr 21 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-3
- Disable ModuleNotices test, re-enable parallel ctest

* Tue Mar 30 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-2
- Disable parallel ctest checks for now

* Tue Mar 23 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-1
- Update to 2.8.1 final

* Tue Mar 23 2010 Kevin Kofler <Kevin@tigcc.ticalc.org> - 2.8.1-0.3.rc5
- Own /usr/lib(64)/cmake/

* Fri Mar 12 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-0.2.rc5
- Update to 2.8.1 RC 5

* Fri Feb 19 2010 Orion Poplawski <orion@cora.nwra.com> - 2.8.1-0.1.rc3
- Update to 2.8.1 RC 3

* Thu Jan 14 2010 Rex Dieter <rdieter@fedorproject.org> - 2.8.0-2
- macros.cmake: drop -DCMAKE_SKIP_RPATH:BOOL=ON from %%cmake

* Wed Nov 18 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-1
- Update to 2.8.0 final

* Wed Nov 18 2009 Rex Dieter <rdieter@fedoraproject.org> - 2.8.0-0.8.rc7
- rebuild (for qt-4.6.0-rc1)

* Wed Nov 11 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.7.rc7
- Update to 2.8.0 RC 7

* Tue Nov 10 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.7.rc6
- Update to 2.8.0 RC 6

* Wed Nov 4 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.6.rc5
- Update to 2.8.0 RC 5
- Drop patches fixed upstream

* Fri Oct 30 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.5.rc4
- Update to 2.8.0 RC 4
- Add FindJNI patch
- Add test patch from cvs to fix Fedora build test build error

* Tue Oct 13 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.4.rc3
- Update to 2.8.0 RC 3
- Drop vtk64 patch fixed upstream

* Fri Oct 9 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.3.rc2
- Do out of tree build, needed for ExternalProject test

* Thu Oct 8 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.2.rc2
- Update to 2.8.0 RC 2
- Use parallel ctest in %%check

* Tue Sep 29 2009 Orion Poplawski <orion@cora.nwra.com> - 2.8.0-0.1.rc1
- Update to 2.8.0 RC 1

* Thu Sep 17 2009 Rex Dieter <rdieter@fedoraproject.org> - 2.6.4-4
- macro.cmake: prefixes cmake with the package being builts bindir (#523878)

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Jun 3 2009 Orion Poplawski <orion@cora.nwra.com> - 2.6.4-2
- Add patch to find VTK on 64-bit machines (bug #503945)

* Wed Apr 29 2009 Orion Poplawski <orion@cora.nwra.com> - 2.6.4-1
- Update to 2.6.4
- Drop patch for bug #475876 fixed upstream

* Mon Mar 16 2009 Rex Dieter <rdieter@fedoraproject.org> - 2.6.3-3
- macros.cmake: +%%_cmake_version

* Mon Mar 09 2009 Kevin Kofler <Kevin@tigcc.ticalc.org> - 2.6.3-2
- Fix crash during kdepimlibs build (#475876)

* Mon Feb 23 2009 Orion Poplawski <orion@cora.nwra.com> - 2.6.3-1
- Update to 2.6.3 final

* Tue Feb 17 2009 Orion Poplawski <orion@cora.nwra.com> - 2.6.3-0.4.rc13
- Update to 2.6.3-RC-13

* Tue Jan 13 2009 Orion Poplawski <orion@cora.nwra.com> - 2.6.3-0.3.rc8
- Update to 2.6.3-RC-8

* Sun Jan 04 2009 Rex Dieter <rdieter@fedoraproject.org> - 2.6.3-0.2.rc5
- macros.cmake: add -DCMAKE_SKIP_RPATH:BOOL=ON
- fix Release tag

* Wed Dec 10 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.3-0.rc5.1
- Update to 2.6.3-RC-5

* Tue Dec 2 2008 Rex Dieter <rdieter@fedoraproject.org> - 2.6.2-3
- Add -DCMAKE_VERBOSE_MAKEFILE=ON to %%cmake (#474053)
- preserve timestamp of macros.cmake
- cosmetics

* Tue Oct 21 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.2-2
- Allow conditional build of gui

* Mon Sep 29 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.2-1
- Update to 2.6.2

* Mon Sep 8 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.2-0.rc3.1
- Update to 2.6.2-RC-2
- Drop parens patch fixed upstream

* Tue Sep 2 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.1-3
- Drop jni patch, applied upstream.

* Tue Aug 26 2008 Rex Dieter <rdieter@fedoraproject.org> - 2.6.1-2
- attempt to patch logic error, crasher

* Tue Aug 5 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.1-1
- Update to 2.6.1

* Mon Jul 14 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.1-0.rc8.1
- Update to 2.6.1-RC-8
- Drop xmlrpc patch fixed upstream

* Tue May 6 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-1
- Update to 2.6.0

* Mon May 5 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-0.rc10.1
- Update to 2.6.0-RC-10

* Thu Apr 24 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-0.rc9.1
- Update to 2.6.0-RC-9

* Fri Apr 11 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-0.rc8.1
- Update to 2.6.0-RC-8

* Thu Apr 3 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-0.rc6.1
- Update to 2.6.0-RC-6

* Fri Mar 28 2008 Orion Poplawski <orion@cora.nwra.com> - 2.6.0-0.rc5.1
- Update to 2.6.0-RC-5
- Add gui sub-package for Qt frontend

* Fri Mar 7 2008 Orion Poplawski <orion@cora.nwra.com> - 2.4.8-3
- Add macro for bootstrapping new release/architecture
- Add %%check section

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.4.8-2
- Autorebuild for GCC 4.3

* Tue Jan 22 2008 Orion Poplawski <orion@cora.nwra.com> - 2.4.8-1
- Update to 2.4.8

* Wed Jan 16 2008 Orion Poplawski <orion@cora.nwra.com> - 2.4.8-0.rc12
- Update to 2.4.8 RC-12

* Fri Dec 14 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.8-0.rc4
- Update to 2.4.8 RC-4

* Mon Nov 12 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.7-4
- No longer set CMAKE_SKIP_RPATH

* Tue Aug 28 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.7-3
- Rebuild for new expat

* Wed Aug 22 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.7-2
- Rebuild for BuildID

* Mon Jul 23 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.7-1
- Update to 2.4.7

* Fri Jun 29 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.7-0.rc11
- Update to 2.4.7 RC-11

* Wed Jun 27 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.6-4
- Update macros.cmake to add CMAKE_INSTALL_LIBDIR, INCLUDE_INSTALL_DIR,
  LIB_INSTALL_DIR, SYSCONF_INSTALL_DIR, and SHARE_INSTALL_PREFIX

* Mon Apr 16 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.6-3
- Apply patch from upstream CVS to fix .so install permissions (bug #235673)

* Fri Apr 06 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.6-2
- Add rpm macros

* Thu Jan 11 2007 Orion Poplawski <orion@cora.nwra.com> - 2.4.6-1
- Update to 2.4.6

* Mon Dec 18 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.5-2
- Use system libraries (bootstrap --system-libs)

* Tue Dec  5 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.5-1
- Update to 2.4.5

* Tue Nov 21 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.4-1
- Update to 2.4.4

* Tue Oct 31 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.3-4
- Add /usr/lib/jvm/java to FindJNI search paths

* Tue Aug 29 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.3-3
- Rebuild for FC6

* Wed Aug  2 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.3-2
- vim 7.0 now ships cmake files, so don't ship ours (bug #201018)
- Add patch to Linux.cmake for Fortran soname support for plplot

* Tue Aug  1 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.3-1
- Update to 2.4.3

* Mon Jul 31 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.2-3
- Update for vim 7.0

* Tue Jul 11 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.2-2
- Patch FindRuby and FindSWIG to work on Fedora (bug #198103)

* Fri Jun 30 2006 Orion Poplawski <orion@cora.nwra.com> - 2.4.2-1
- Update to 2.4.2

* Thu Apr  6 2006 Orion Poplawski <orion@cora.nwra.com> - 2.2.3-4
- Update for vim 7.0c

* Tue Mar 28 2006 Orion Poplawski <orion@cora.nwra.com> - 2.2.3-3
- No subpackages, just own the emacs and vim dirs.

* Tue Mar 21 2006 Orion Poplawski <orion@cora.nwra.com> - 2.2.3-2
- Add emacs and vim support
- Include Example in docs

* Wed Mar  8 2006 Orion Poplawski <orion@cora.nwra.com> - 2.2.3-1
- Fedora Extras version
