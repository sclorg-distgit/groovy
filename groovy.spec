%global pkg_name groovy
%{?scl:%scl_package %{pkg_name}}
%{?maven_find_provides_and_requires}

# Note to packagers: When rebasing this to a later version, do not
# forget to ensure that sources 1 and 2 are up to date as well as
# the Requires list.

Name:           %{?scl_prefix}%{pkg_name}
Version:        1.8.9
Release:        7.15%{?dist}
Summary:        Dynamic language for the Java Platform

# Some of the files are licensed under BSD and CPL terms, but the CPL has been superceded
# by the EPL. We include copies of both for completeness.
# groovyConsole uses CC-BY licensed icons
# (see: subprojects/groovy-console/target/tmp/groovydoc/groovy/ui/icons/credits.txt)
License:        ASL 2.0 and BSD and EPL and Public Domain and CC-BY
URL:            http://groovy.codehaus.org/
Source0:        http://dist.groovy.codehaus.org/distributions/%{pkg_name}-src-%{version}.zip
Source1:        groovy-script
Source2:        groovy-starter.conf
Source4:        cpl-v10.txt
Source5:        epl-v10.txt
Source6:        http://www.apache.org/licenses/LICENSE-2.0.txt
# http://jira.codehaus.org/browse/GROOVY-6085
Patch0:         groovy-inner-interface-annotations.patch
BuildArch:      noarch

BuildRequires:  %{?scl_prefix_java_common}ant
BuildRequires:  %{?scl_prefix_java_common}antlr-tool
BuildRequires:  %{?scl_prefix_java_common}ant-antlr
BuildRequires:  %{?scl_prefix_java_common}objectweb-asm
BuildRequires:  %{?scl_prefix_java_common}bsf
BuildRequires:  %{?scl_prefix_java_common}jansi
BuildRequires:  %{?scl_prefix_java_common}tomcat-jsp-2.2-api
BuildRequires:  %{?scl_prefix_java_common}junit
BuildRequires:  %{?scl_prefix_java_common}tomcat-servlet-3.0-api
BuildRequires:  %{?scl_prefix_java_common}javapackages-tools
BuildRequires:  %{?scl_prefix_java_common}apache-commons-cli
BuildRequires:  %{?scl_prefix_java_common}ecj
BuildRequires:  maven30-xstream
BuildRequires:  maven30-jline
BuildRequires:  maven30-apache-ivy
BuildRequires:  unzip

# The are all runtime dependencies of the script
# TODO: Think of splitting them into a separate subpackage
Requires:       %{?scl_prefix_java_common}ant
Requires:       %{?scl_prefix_java_common}ant-junit
Requires:       %{?scl_prefix_java_common}antlr-tool
Requires:       %{?scl_prefix_java_common}objectweb-asm
Requires:       %{?scl_prefix_java_common}bsf
Requires:       %{?scl_prefix_java_common}apache-commons-cli
Requires:       %{?scl_prefix_java_common}apache-commons-logging
Requires:       %{?scl_prefix_java_common}jansi
Requires:       %{?scl_prefix_java_common}tomcat-jsp-2.2-api
Requires:       %{?scl_prefix_java_common}junit
Requires:       %{?scl_prefix_java_common}tomcat-servlet-3.0-api
Requires:       maven30-xstream
Requires:       maven30-jline
Requires:       maven30-apache-ivy


%description
Groovy is an agile and dynamic language for the Java Virtual Machine,
built upon Java with features inspired by languages like Python, Ruby and
Smalltalk.  It seamlessly integrates with all existing Java objects and
libraries and compiles straight to Java bytecode so you can use it anywhere
you can use Java.


%package javadoc
Summary:        API Documentation for %{pkg_name}
Requires:       %{name} = %{version}-%{release}
%description javadoc
JavaDoc documentation for %{pkg_name}


%prep
%setup -q -n %{pkg_name}-%{version}
%{?scl:scl enable maven30 %{scl} - <<"EOF"}
set -e -x
cp %{SOURCE4} %{SOURCE5} %{SOURCE6} .
# Remove bundled JARs and classes
find \( -name *.jar -o -name *.class \) -delete

%patch0 -p1
%{?scl:EOF}

%build
%{?scl:scl enable maven30 %{scl} - <<"EOF"}
set -e -x
mkdir -p target/lib/{compile,tools}

# Construct classpath
build-jar-repository target/lib/compile tomcat-servlet-api tomcat-jsp-api \
        objectweb-asm/asm-tree objectweb-asm/asm \
        objectweb-asm/asm-util objectweb-asm/asm-analysis \
        antlr ant/ant-antlr antlr \
        bsf jline xstream ant junit ivy commons-cli \
        jansi

# Use ECJ instead of OpenJDK to compile MethodHandle.  This is a
# workaround for a bug in OpenJDK that causes compilation of
# MethodHandle to take many minutes (15min or even more), while ECJ
# can compile it under five seconds.  See rhbz#971483 and
# http://mail.openjdk.java.net/pipermail/compiler-dev/2013-May/006339.html
ecj -6 -d target/classes `find -name MethodHandle.java -o -name ArrayUtil.java`

# Build
# TODO: Build at least tests, maybe examples
ant -DskipTests=on -DskipExamples=on -DskipFetch=on -DskipEmbeddable=on \
        createJars javadoc
%{?scl:EOF}


%install
%{?scl:scl enable maven30 %{scl} - <<"EOF"}
set -e -x

# Code
install -d $RPM_BUILD_ROOT%{_javadir}
install -p -m644 target/dist/groovy.jar $RPM_BUILD_ROOT%{_javadir}/%{pkg_name}.jar

# Startup scripts
install -d $RPM_BUILD_ROOT%{_bindir}
install -p -m755 %{SOURCE1} $RPM_BUILD_ROOT%{_bindir}/groovy
for TOOL in grape groovyc groovyConsole java2groovy groovysh
do
        ln $RPM_BUILD_ROOT%{_bindir}/groovy \
                $RPM_BUILD_ROOT%{_bindir}/$TOOL
done

# Configuration
install -d $RPM_BUILD_ROOT%{_sysconfdir}
install -p -m644 %{SOURCE2} \
        $RPM_BUILD_ROOT%{_sysconfdir}/groovy-starter.conf

# API Documentation
install -d $RPM_BUILD_ROOT%{_javadocdir}/%{name}
find target -type d |xargs chmod 755
cp -rp target/html/api/. $RPM_BUILD_ROOT%{_javadocdir}/%{name}

# Maven depmap
install -d $RPM_BUILD_ROOT%{_mavenpomdir}
install -p -m644 pom.xml $RPM_BUILD_ROOT/%{_mavenpomdir}/JPP-%{pkg_name}.pom
%add_maven_depmap JPP-%{pkg_name}.pom %{pkg_name}.jar
%{?scl:EOF}

%files -f .mfiles
%defattr(-,root,root,-)
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/*
%doc README.md
%doc LICENSE.txt LICENSE-2.0.txt NOTICE.txt cpl-v10.txt epl-v10.txt


%files javadoc
%{_javadocdir}/*
%doc LICENSE.txt LICENSE-2.0.txt NOTICE.txt cpl-v10.txt epl-v10.txt

%changelog
* Sat Jan 09 2016 Michal Srb <msrb@redhat.com> - 1.8.9-7.15
- maven33 rebuild

* Tue Jul 21 2015 Michal Srb <msrb@redhat.com> - 1.8.9-7.14
- Fix paths in groovy-script
- Resolves: rhbz#1223655

* Tue Jul 07 2015 Michael Simacek <msimacek@redhat.com> - 1.8.9-7.13
- Bump release once more

* Tue Jul 07 2015 Michael Simacek <msimacek@redhat.com> - 1.8.9-7.12
- Set source level 6 when invoking ecj

* Tue Jan 13 2015 Michael Simacek <msimacek@redhat.com> - 1.8.9-7.11
- Mass rebuild 2015-01-13

* Mon Jan 12 2015 Michael Simacek <msimacek@redhat.com> - 1.8.9-7.10
- BR/R on packages from rh-java-common

* Wed Jan 07 2015 Michal Srb <msrb@redhat.com> - 1.8.9-7.9
- Migrate to .mfiles

* Tue Jan 06 2015 Michael Simacek <msimacek@redhat.com> - 1.8.9-7.8
- Mass rebuild 2015-01-06

* Mon May 26 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.7
- Mass rebuild 2014-05-26

* Wed Feb 19 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.6
- Mass rebuild 2014-02-19

* Tue Feb 18 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.5
- Mass rebuild 2014-02-18

* Tue Feb 18 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.4
- Remove requires on java

* Mon Feb 17 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.3
- SCL-ize build-requires

* Thu Feb 13 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.2
- Rebuild to regenerate auto-requires

* Tue Feb 11 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7.1
- First maven30 software collection build

* Mon Jan 13 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-7
- Add Requires on java-devel
- Resolves: rhbz#1052291

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 1.8.9-6
- Mass rebuild 2013-12-27

* Thu Oct 24 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-5
- Remove desktop files

* Fri Jun 28 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-4
- Rebuild to regenerate API documentation
- Resolves: CVE-2013-1571

* Mon Jun 10 2013 Michal Srb <msrb@redhat.com> - 1.8.9-3
- Fix license tag (+CC-BY)

* Thu Jun  6 2013 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.8.9-2
- Remove bundled JARs and classes
- Add workaround for rhbz#971483
- Add Public Domain to licenses
- Install ASL 2.0 license text, resolves: rhbz#858257

* Sat Apr 20 2013 gil cattaneo <puntogil@libero.it> - 1.8.9-1
- Update to 1.8.9

* Thu Apr 11 2013 Matt Spaulding <mspaulding06@gmail.com> - 1.8.8-4
- Now accepts classpath argument (RHBZ #810885)

* Mon Apr  8 2013 Andy Grimm <agrimm@gmail.com> - 1.8.8-3
- Apply patch for GROOVY-6085 (RHBZ #949352) 

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.8-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Nov 27 2012 Tom Callaway <spot@fedoraproject.org> - 1.8.8-1
- Update to 1.8.8
- Fix licensing issues

* Wed Jul 25 2012 Johannes Lips <hannes@fedoraproject.org> - 1.8.7-1
- Update to 1.8.7

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.8.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Mar 21 2012 Alexander Kurtakov <akurtako@redhat.com> 1.8.6-4
- Move to tomcat v7 apis.
- Guideline fixes.

* Fri Mar 09 2012 Johannes Lips <hannes@fedoraproject.org> - 1.8.6-3
- fixed the path of jvm in the startup script 

* Sat Mar 03 2012 Johannes Lips <hannes@fedoraproject.org> - 1.8.6-2
- fixed the startup script by adding jansi as dep

* Wed Feb 22 2012 Johannes Lips <hannes@fedoraproject.org> - 1.8.6-1
- Update to 1.8.6

* Tue Jan 03 2012 Johannes Lips <hannes@fedoraproject.org> - 1.8.5-1
- Update to 1.8.5

* Sun Nov 20 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.4-1
- Update to 1.8.4

* Thu Oct 13 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.3-2
- remove the nojansi patch since jansi is in fedora

* Thu Oct 13 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.3-1
- Update to 1.8.3

* Tue Sep 06 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.2-1
- Update to 1.8.2

* Sat Aug 13 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.1-3
- adjusted the maven pom dir

* Sat Aug 13 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.1-2
- updated the nojansi patch

* Sat Aug 13 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.1-1
- Update to 1.8.1

* Wed May 04 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.0-2
- Minor changes to reflect changes to packaging guidelines

* Fri Apr 29 2011 Johannes Lips <hannes@fedoraproject.org> - 1.8.0-1
- Update to 1.8.0

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Nov 6 2010 Alexander Kurtakov <akurtako@redhat.com> 1.7.2-3
- Build with servlet and jsp apis from tomcat6.

* Thu Jun 17 2010 Lubomir Rintel <lkundrak@v3.sk> - 1.7.2-2
- Fix a typo

* Tue Apr 20 2010 Lubomir Rintel <lkundrak@v3.sk> - 1.7.2-1
- Bump version

* Fri Apr 02 2010 Lubomir Rintel <lkundrak@v3.sk> - 1.7.1-1
- Bump version
- Revert addition of jansi dependency

* Fri Apr 02 2010 Lubomir Rintel <lkundrak@v3.sk> - 1.7.0-2
- Add maven depmap

* Wed Feb 17 2010 Lubomir Rintel <lkundrak@v3.sk> - 1.7.0-1
- New upstream version
- Use asm 3.1 instead of asm2

* Wed Dec 04 2009 Lubomir Rintel <lkundrak@v3.sk> - 1.6.7-1
- New upstream version
- Make Jochen happy

* Thu Dec 03 2009 Lubomir Rintel <lkundrak@v3.sk> - 1.6.6-2
- Build with OpenJDK

* Mon Nov 30 2009 Lubomir Rintel <lkundrak@v3.sk> - 1.6.6-1
- Bump to 1.6.6
- Don't mistakenly require itself (Jochen Schmitt, #534168#c3)

* Fri Nov 27 2009 Lubomir Rintel <lkundrak@v3.sk> - 1.6.5-2
- Hopefully fix mockbuild

* Mon Nov 09 2009 Lubomir Rintel <lkundrak@v3.sk> - 1.6.5-1
- Initial Fedora packaging
