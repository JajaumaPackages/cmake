Name:		cmake
Version:	2.4.6
Release:	3%{?dist}
Summary:	Cross-platform make system

Group:		Development/Tools
License:	BSD
URL:		http://www.cmake.org
Source0:	http://www.cmake.org/files/v2.4/cmake-%{version}.tar.gz
Source1:        cmake-init-fedora
Source2:        macros.cmake
Patch0:         cmake-2.4.2-fedora.patch
Patch1:         cmake-2.4.5-xmlrpc.patch
Patch2:         cmake-2.4.6-soexe.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  ncurses-devel, libX11-devel
BuildRequires:  curl-devel, expat-devel, xmlrpc-c-devel, zlib-devel
Requires:       rpm


%description
CMake is used to control the software compilation process using simple 
platform and compiler independent configuration files. CMake generates 
native makefiles and workspaces that can be used in the compiler 
environment of your choice. CMake is quite sophisticated: it is possible 
to support complex environments requiring system configuration, pre-processor 
generation, code generation, and template instantiation.


%prep
%setup -q
%patch -p1 -b .fedora
%patch1 -p1 -b .xmlrpc
%patch2 -p1 -b .soexe


%build
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$RPM_OPT_FLAGS"
./bootstrap --init=%SOURCE1 --prefix=%{_prefix} --datadir=/share/%{name} \
            --docdir=/share/doc/%{name}-%{version} --mandir=/share/man \
            --system-libs
make VERBOSE=1 %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT/%{_datadir}/%{name}/Modules -type f | xargs chmod -x
mkdir -p $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp
cp -a Example $RPM_BUILD_ROOT%{_datadir}/doc/%{name}-%{version}/
install -m 0644 Docs/cmake-mode.el $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp/
# RPM macros
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/rpm
install -m 0644 %{SOURCE2} $RPM_BUILD_ROOT%{_sysconfdir}/rpm/


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/rpm/macros.cmake
%{_datadir}/doc/%{name}-%{version}/
%{_bindir}/ccmake
%{_bindir}/cmake
%{_bindir}/cpack
%{_bindir}/ctest
%{_datadir}/%{name}/
%{_mandir}/man1/*.1*
%{_datadir}/emacs/


%changelog
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
