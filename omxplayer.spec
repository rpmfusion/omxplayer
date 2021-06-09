%global commit_date     20181014
%global commit_long     7f3faf6cadac913013248de759462bcff92f0102
%global commit_short    %(c=%{commit_long}; echo ${c:0:7})

# taken from known-good patch files
%global omx_cflags -std=c++0x -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -DTARGET_POSIX -DTARGET_LINUX -fPIC -DPIC -D_REENTRANT -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -DHAVE_CMAKE_CONFIG -D__VIDEOCORE4__ -U_FORTIFY_SOURCE -Wall -DHAVE_OMXLIB -DUSE_EXTERNAL_FFMPEG  -DHAVE_LIBAVCODEC_AVCODEC_H -DHAVE_LIBAVUTIL_OPT_H -DHAVE_LIBAVUTIL_MEM_H -DHAVE_LIBAVUTIL_AVUTIL_H -DHAVE_LIBAVFORMAT_AVFORMAT_H -DHAVE_LIBAVFILTER_AVFILTER_H -DHAVE_LIBSWRESAMPLE_SWRESAMPLE_H -DOMX -DOMX_SKIP64BIT -ftree-vectorize -DUSE_EXTERNAL_OMX -DTARGET_RASPBERRY_PI -DUSE_EXTERNAL_LIBBCM_HOST
%global omx_ldflags -L./ -L %{_libdir}/vc -lc -lbrcmGLESv2 -lbrcmEGL -lbcm_host -lopenmaxil -lfreetype -lz -lasound
%global omx_includes -I./ -Ilinux -I %{_includedir}/ffmpeg -I %{_includedir}/dbus-1.0 -I %{_libdir}/dbus-1.0/include -I%{_includedir}/freetype2 -isystem%{_includedir}/vc -isystem%{_includedir}/vc/interface/vcos/pthreads

Name:       omxplayer
Version:    %{commit_date}
Release:    3.%{commit_short}%{dist}
Summary:    Raspberry Pi command line OMX player
License:    GPLv2+
URL:        https://github.com/popcornmix/%{name}
Source0:    %{url}/archive/%{commit_long}.tar.gz#/%{name}-%{commit_short}.tar.gz
Source1:    %{name}.desktop
# Refer: https://github.com/fedberry/omxplayer/blob/master/0004-fix-libs-path.patch
Patch1:     0004-fix-libs-path.patch
# Refer https://github.com/fedberry/omxplayer/blob/master/0006-video-group-check.patch
Patch2:     0006-video-group-check.patch
# Refer: https://github.com/popcornmix/omxplayer/issues/649
Patch3:     0007-Fix-keyboard-input.patch
# Refer: https://github.com/popcornmix/omxplayer/pull/670
Patch4:     omxplayer-fix-incorrect-fsf-address.patch
# Refer: https://github.com/popcornmix/omxplayer/pull/671
Patch5:     omxplayer-use-type-p.patch

ExclusiveArch:  %{arm}

BuildRequires:  boost-devel
BuildRequires:  desktop-file-utils
BuildRequires:  raspberrypi-vc-devel
BuildRequires:  raspberrypi-vc-static
BuildRequires:  ffmpeg-devel
BuildRequires:  pkgconfig(alsa)
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(freetype2)
BuildRequires:  pkgconfig(libpcre)
BuildRequires:  pkgconfig(libssh)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(smbclient)
BuildRequires:  findutils
BuildRequires:  coreutils
BuildRequires:  sed
BuildRequires:  gcc-c++
BuildRequires:  rubygem-ronn

Requires:   fbset
Requires:   gnu-free-sans-fonts

%description
OMXPlayer is a video player specifically made for the Raspberry Pi's GPU.
It relies on the OpenMAX hardware acceleration API, which is the Broadcom's
VideoCore officially supported API for GPU video/audio processing.


%package desktop
Summary: OMXPlayer Desktop Entry specification file
Requires: lxterminal
Requires: libnotify


%description desktop
The freedesktop Desktop Entry specification file for OMXPlayer to integrate into
desktop environments.


%prep
%autosetup -p 1 -n %{name}-%{commit_long}

rm -f Makefile.ffmpeg

# Change all paths /opt/vc -> /usr/lib/vc
find ./ -type f | xargs sed -i  's!/opt/vc!%{_libdir}/vc!g'

# gen_version.sh assumes we are in a git repo
sed -i 's!bash gen_version.sh > version.h!!' Makefile

cat > version.h << EOF
#ifndef __VERSION_H__
#define __VERSION_H__
#define VERSION_DATE "%{commit_date}"
#define VERSION_HASH "%{commit_short}"
#define VERSION_BRANCH "master"
#define VERSION_REPO "%{url}"
#endif
EOF

# Now update the Makefile with the flags we just set
sed -ri 's!^CFLAGS=.*!CFLAGS=%{optflags}!' Makefile
sed -ri 's!^CFLAGS\+=.*!CFLAGS\+=%{omx_cflags}!' Makefile
sed -ri 's!^LDFLAGS=.*!LDFLAGS=%{omx_ldflags}!' Makefile
sed -ri 's!^LDFLAGS\+=.*!LDFLAGS\+=%{__global_ldflags}!' Makefile
sed -ri 's!^INCLUDES\+=.*!INCLUDES\+=%{omx_includes}!' Makefile

# Fix the font path
sed -i 's!/usr/share/fonts/truetype/freefont!%{_datadir}/fonts/gnu-free!g' omxplayer.cpp

# Fix the bash shebang
sed -i 's~^#!/bin/bash~#!%{_bindir}/bash~' *.sh omxplayer

%build
%{make_build} omxplayer.bin STRIP=/bin/true
# build the manpage with ronn instead of using http://mantastic.herokuapp.com/
ronn < README.md > omxplayer.1

%install
%{__install} -d %{buildroot}/%{_bindir}
%{__install} -p %{name} %{buildroot}/%{_bindir}
%{__install} -p %{name}.bin %{buildroot}/%{_bindir}
%{__install} -d %{buildroot}/%{_mandir}/man1
%{__install} -pm 644 %{name}.1 %{buildroot}/%{_mandir}/man1
%{__install} -d %{buildroot}/%{_libdir}/%{name}
%{__install} -d %{buildroot}/%{_datadir}/applications
%{__install} -p %{SOURCE1} %{buildroot}/%{_datadir}/applications

desktop-file-install                                    \
        --dir %{buildroot}%{_datadir}/applications      \
        --delete-original                               \
        --mode 644                                      \
        %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%license COPYING
%doc README.md
%{_bindir}/%{name}
%{_bindir}/%{name}.bin
%{_mandir}/man1/%{name}.1.*

%files desktop
%{_datadir}/applications/*.desktop


%changelog
* Sat Dec 22 2018 Andrew Bauer <zonexpertconsulting@outlook.com> 20181014-3.7f3faf6
- Modify file paths in the specfile rather than via patch files
- Build against ffmpeg pacakge, rather than bundled
- use ronn to generate man page
- fix shebang
- generate version.h
- use autosetup
- add patches to fix fsf-address and non-fatal errors shown on the cmdline

* Thu Nov 01 2018 Vaughan Agrez <devel at agrez dot net> 20181014-2.7f3faf6
- Fix keyboard input for Fedberry 29
- Re-enable man file generation for f27 & f29
- Update Requires

* Sun Oct 14 2018 Vaughan Agrez <devel at agrez dot net> 20181014-1.7f3faf6
- Update to git commit: 7f3faf6cadac913013248de759462bcff92f0102
- Bump ffmpeg release to 4.0.2
- Refactor Makefile / Makefile.ffmpeg patches
- Drop makefile.include patch
- Disable generation of man file
- Fix BuildRequires

* Thu Apr 05 2018 Vaughan Agrez <devel at agrez dot net> 20170908-2.037c3c1
- Bump ffmpeg release to 3.3.6
- Add desktop file
- Add video group check (Patch 5)

* Thu Nov 23 2017 Vaughan Agrez <devel at agrez dot net> 20170908-1.037c3c1
- Update to git commit: 037c3c1eab2601dc1e8fb329c2290eb2380acb3c
- Bump ffmpeg release to 3.3.5
- Drop ffmpeg openssl build fixes (merged upstream)

* Tue Jul 25 2017 Vaughan Agrez <devel at agrez dot net> 20170330-3.061425a5
- Fix building against openssl >= 1.1.0 (Patches 5 & 6)
- Bump ffmpeg release to 3.1.9
- Exclude Requires/Provides for bundled libs
- Use %%{make_build} to build ffmpeg
- Drop %%post & %%postun sections

* Mon Apr 24 2017 Vaughan Agrez <devel at agrez dot net> 20170330-2.061425a5
- Add requires for fbset

* Thu Apr 20 2017 Vaughan Agrez <devel at agrez dot net> 20170330-1.061425a5
- Initial package
