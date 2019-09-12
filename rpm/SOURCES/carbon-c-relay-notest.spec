# Needed for el5
%{!?_initddir: %global _initddir %{_sysconfdir}/rc.d/init.d}

%global _hardened_build 1

%ifarch %{nodejs_arches}
%global build_manpage 1
%endif

%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:               carbon-c-relay
Version:            %{vers}
Release:            %{rel}%{?dist}
Summary:            Enhanced C implementation of Carbon relay, aggregator and rewriter
License:            ASL 2.0
Group:              System Environment/Daemons
URL:                https://github.com/grobian/carbon-c-relay
Source0:            https://github.com/msaf1980/carbon-c-relay/archive/%{commit}/%{name}-%{version}.%{rel}.tbz
Source1:            carbon-c-relay.service
Source2:            carbon-c-relay.init
Source3:            carbon-c-relay.logrotate
Source4:            carbon-c-relay.sysconfig.sysv
Source5:            carbon-c-relay.conf
Source6:            carbon-c-relay.sysconfig.systemd
Source7:            carbon-c-relay.limits.systemd

BuildRequires:      gcc
BuildRequires:      make
BuildRequires:      bison
BuildRequires:      flex

# use nodejs-ronn instead of ruby ronn because of availability on epel 6 & 7
%if 0%{?build_manpage}
BuildRequires:      nodejs-ronn
%endif

Requires(pre):      shadow-utils

%if 0%{?rhel} && 0%{?rhel} <= 6
Requires(post):     chkconfig
Requires(preun):    chkconfig
Requires(postun):   initscripts
%else
BuildRequires:      systemd
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
%endif

# carbon-c-relay ships a bundled md5 library for which an exception exists
# see: https://fedoraproject.org/wiki/Packaging:No_Bundled_Libraries
Provides:           bundled(md5-peslyak)

# Needed for el5
%{?el5:BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)}

# Does not build on old 32bit architectures (el5)
# https://github.com/grobian/carbon-c-relay/issues/100
ExcludeArch:        i386 ppc


%description
Carbon-like Graphite line mode relay. This project aims to be a replacement of 
the original Carbon relay. The main reason to build a replacement is 
performance and configurability. Carbon is single threaded, and sending 
metrics to multiple consistent-hash clusters requires chaining of relays. This 
project provides a multithreaded relay which can address multiple targets and 
clusters for each and every metric based on pattern matches.


%prep
%autosetup -n %{name}
rm conffile.tab.c conffile.tab.h conffile.yy.c


%build
%configure
%make_build LDFLAGS="%{?__global_ldflags}" CFLAGS="%{optflags}"

%if 0%{?build_manpage}
ronn-nodejs --roff carbon-c-relay.md > carbon-c-relay.1
%endif


%install
%if 0%{?el5}
rm -rf %{buildroot}
%endif

install -Dp -m0755 relay %{buildroot}%{_bindir}/%{name}
install -Dp -m0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/%{name}.conf

%if 0%{?build_manpage}
install -Dp -m0644 carbon-c-relay.1 %{buildroot}%{_mandir}/man1/carbon-c-relay.1
%endif

%if 0%{?rhel} && 0%{?rhel} <= 6
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -Dp -m0755 %{SOURCE2} %{buildroot}%{_initddir}/%{name}
install -Dp -m0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -Dp -m0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%else
install -Dp -m0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -Dp -m0644 %{SOURCE6} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -Dp -m0644 %{SOURCE7} %{buildroot}%{_sysconfdir}/systemd/system/%{name}.service.d/limits.conf
%endif

%if 0%{?el5}
%clean
rm -rf %{buildroot}
%endif


%pre
getent group carbon-c-relay >/dev/null || groupadd -r carbon-c-relay
getent passwd carbon-c-relay >/dev/null || \
    useradd -r -g carbon-c-relay -d / -s /sbin/nologin \
    -c "Carbon C Relay Daemon" carbon-c-relay
exit 0


%post
%if 0%{?rhel} && 0%{?rhel} <= 6
/sbin/chkconfig --add %{name}
%else
%systemd_post %{name}.service
%endif


%preun
%if 0%{?rhel} && 0%{?rhel} <= 6
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
%else
%systemd_preun %{name}.service
%endif


%postun
%if 0%{?rhel} && 0%{?rhel} <= 6
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
%else
%systemd_postun_with_restart %{name}.service
%endif


%files
%{!?_licensedir:%global license %%doc}
%license LICENSE.md
%doc carbon-c-relay.md ChangeLog.md

%if 0%{?build_manpage}
%{_mandir}/man1/carbon-c-relay.1*
%endif

%{_bindir}/carbon-c-relay
%config(noreplace) %{_sysconfdir}/carbon-c-relay.conf
%config(noreplace) %{_sysconfdir}/sysconfig/carbon-c-relay


%if 0%{?rhel} && 0%{?rhel} <= 6
%{_initddir}/%{name}
%attr(0755,carbon-c-relay,carbon-c-relay) %dir %{_localstatedir}/log/%{name}
%attr(0755,carbon-c-relay,carbon-c-relay) %dir %{_localstatedir}/run/%{name}
%{_sysconfdir}/logrotate.d/%{name}
%else
%{_unitdir}/%{name}.service
%dir %{_sysconfdir}/systemd/system/%{name}.service.d
%config(noreplace) %{_sysconfdir}/systemd/system/%{name}.service.d/limits.conf
%endif


%changelog
* Fri Mar 23 2018 Piotr Popieluch <piotr1212@gmail.com> - 3.3-1
- Update to 3.3

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.2-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Oct 27 2017 Piotr Popieluch <piotr1212@gmail.com> - 3.2-3
- Ship pregenerated Makefile.in (automake fails on epel7)

* Fri Oct 27 2017 Piotr Popieluch <piotr1212@gmail.com> - 3.2-2
- Update dependencies in Makefile.am to fix parallell builds

* Mon Oct 23 2017 Piotr Popieluch <piotr1212@gmail.com> - 3.2-1
- Update to 3.2

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Florian Weimer <fweimer@redhat.com> - 3.1-3
- Rebuild with binutils fix for ppc64le (#1475636)

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue May 02 2017 Piotr Popieluch <piotr1212@gmail.com> - 3.1-1
- Update to 3.1
- run ./configure in %%build

* Thu Apr 13 2017 Piotr Popieluch <piotr1212@gmail.com> - 3.0-1
- Update to 3.0

* Tue Feb 07 2017 <piotrp@fedoraproject.org> - 2.6-2
- Add example systemd limits configuration

* Thu Jan 26 2017 piotr1212@gmail.com - 2.6-1
- Update to 2.6

* Wed Jan 11 2017 piotr1212@gmail.com - 2.5-1
- Update to 2.5

* Tue Nov 08 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.3-1
- Update to 2.3

* Fri Sep 16 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.2-2
- Remove braces from systemd service file to correctly interpret arguments

* Sun Sep 11 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.2-1
- Update to 2.2

* Thu Jul 07 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.1-2
- Add ExecReload SIGHUP to systemd unit

* Mon Jun 20 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.1-1
- Update to 2.1

* Wed Jun 15 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.0-2
- Disable manpage creation for systems which don't have nodejs

* Mon Jun 06 2016 Piotr Popieluch <piotr1212@gmail.com> - - 2.0-1
- Update to upstream 2.0
- Generate man file

* Fri Apr 22 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.11-2
- Set correct user in systemd unit file
- Remove logfile in sysconfig on systemd releases

* Wed Mar 23 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.11-1
- Update to upstream 1.11

* Thu Mar 10 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.10-1
- Update to upstream 1.10
- el5/el6: Use new daemon mode in non systemd systems

* Tue Feb 23 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.8-1
- Update to upstream 1.8
- el5: add clean section and conditionalize all el5 specifics

* Fri Feb 19 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.7-3
- Add BR gcc and make https://fedorahosted.org/fpc/ticket/540

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sun Jan 31 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.7-1
- Update to upstream 1.7

* Thu Jan 14 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.5-1
- Update to upstream 1.5

* Mon Jan 04 2016 Piotr Popieluch <piotr1212@gmail.com> - 1.4-1
- Update to upstream 1.4

* Wed Dec 16 2015 Piotr Popieluch <piotr1212@gmail.com> - 1.3-1
- Update to upstream 1.3

* Fri Dec 11 2015 Piotr Popieluch <piotr1212@gmail.com> - 1.2-1
- Update to upstream 1.2

* Wed Nov 25 2015 Piotr Popieluch <piotr1212@gmail.com> - 1.1-1
- Update to upstream 1.1

* Sat Nov 07 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.45-1
- Update to new version
- Set LDFLAGS to build with PIE
- Update Source to follow github source guidelines

* Mon Aug 31 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.44-3
- Exclude 32 bit arches

* Sun Aug 30 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.44-2
- Add el5 support

* Fri Aug 14 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.44-1
- Update to upstream 0.44
- Use own relay.conf

* Mon Jul 27 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.43-2
- specify copylib 'Provides: bundled(md5-peslyak)'

* Mon Jul 27 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.43-1
- Update to upstream 0.43

* Mon Jul 27 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.42-2
- Removed obsoleted BR: openssl-devel

* Fri Jul 24 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.42-1
- Update to upstream 0.42
- Remove allow-percent patch, characters are now configurable
- Make characters to allow configurable in sysconfig

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.40-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue May 12 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.40-1
- update to upstream 0.40
- add logfile to sysconfig

* Fri May 01 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.39-3
- update to later commit to fix closed udp sockets
- logrotate sighup instead of restart
- allow percent characters in metric names

* Thu Apr 02 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.39-2
- fix filepath in logrotate

* Sat Mar 28 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.39-1
- update to latest upsream 0.39

* Wed Feb  4 2015 Piotr Popieluch <piotr1212@gmail.com> - 0.37-1
- update to upstream 0.37
- rewritten for Fedora and comply with Fedora package guidelines

* Mon Sep 8 2014 Matthew Hollick <matthew@mayan-it.co.uk>
- tidy up for github
- reverted site specific changes

* Fri Aug 8 2014 Matthew Hollick <matthew@mayan-it.co.uk>
- packaged as part of twiki

* Tue Jul 1 2014 Matthew Hollick <matthew@mayan-it.co.uk>
- packaged as part of mdr
- binary renamed from 'relay' to 'cc_relay'
- pagage renamed to reflect function rather than component
- user / group named by function

* Tue May 6 2014 Matthew Hollick <matthew@mayan-it.co.uk>
- Initial package for the BBC
