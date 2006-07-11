Name:		cmake
Version:	2.4.2
Release:	2%{?dist}
Summary:	Cross-platform make system

Group:		Development/Tools
License:	BSD
URL:		http://www.cmake.org
Source0:	http://www.cmake.org/files/v2.4/cmake-%{version}.tar.gz
Source1:        cmake-init-fedora
Patch0:         cmake-2.4.2-fedora.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  ncurses-devel, libX11-devel

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


%build
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$RPM_OPT_FLAGS"
./bootstrap --init=%SOURCE1 --prefix=%{_prefix} --datadir=/share/%{name} \
            --docdir=/share/doc/%{name}-%{version} --mandir=/share/man
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT
find $RPM_BUILD_ROOT/%{_datadir}/%{name}/Modules -type f | xargs chmod -x
mkdir -p $RPM_BUILD_ROOT%{_datadir}/vim/vim70c/syntax
mkdir -p $RPM_BUILD_ROOT%{_datadir}/vim/vim70c/indent
mkdir -p $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp
cp -a Example $RPM_BUILD_ROOT%{_datadir}/doc/%{name}-%{version}/
install -m 0644 Docs/cmake-syntax.vim $RPM_BUILD_ROOT%{_datadir}/vim/vim70c/syntax/cmake.vim
install -m 0644 Docs/cmake-indent.vim $RPM_BUILD_ROOT%{_datadir}/vim/vim70c/indent/cmake.vim
install -m 0644 Docs/cmake-mode.el $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp/


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_datadir}/doc/%{name}-%{version}/
%{_bindir}/ccmake
%{_bindir}/cmake
%{_bindir}/cpack
%{_bindir}/ctest
%{_datadir}/%{name}/
%{_mandir}/man1/*.1*
%{_datadir}/emacs/
%{_datadir}/vim/


%changelog
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
