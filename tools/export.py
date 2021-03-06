#!/usr/bin/env python
# encoding: utf-8

"""
Second attempt to make our export script more portable than export.sh

"""

import fileinput
from subprocess import Popen, PIPE
import sys
# This will need to be replaced with argsparse when we make a 2.7+/3.2+ version
import optparse
import datetime

# py3k compatibility
try:
    from email.Utils import formatdate
except ImportError:
    from email.utils import formatdate

# In lieu of a config file
help_message = \
    """This script creates a tag in the Bcfg2 git repo and exports
a tar file of the code at that tag.

This script must be run at the top of your git repository.
"""


pkgname = 'bcfg2'
ftphost = 'terra.mcs.anl.gov'
ftpdir = '/mcs/ftp/pub/bcfg'


def run(command):
    return Popen(command, shell=True, stdout=PIPE).communicate()


def find_and_replace(f, iftest, rline, startswith=False, dryrun=False):
    if dryrun:
        inplace = 0
        print("*** dry-run: New '%s' will look like this:" % f)
    else:
        inplace = 1
    for line in fileinput.input(f, inplace):
        if startswith:
            if line.startswith(iftest):
                line = line.replace(line, rline)
            sys.stdout.write(line)
        else:
            if iftest in line and line != "Version: %{version}\n":
                line = line.replace(line, rline)
            sys.stdout.write(line)
    if dryrun:
        print("*** End '%s'" % f)


def main():
    # This is where the options are set up
    p = optparse.OptionParser(description=help_message,
                              prog=sys.argv[0],
                              version='0.1',
                              usage='%prog [-h|--help] [-v|--version] '
                                    '[-n|--dry-run] [-d|--debug]')
    p.add_option('--verbose', '-v',
                 action='store_true',
                 help='turns on verbose mode',
                 default=False,
                 dest='verbose')
    p.add_option('--dry-run', '-n',
                 action='store_true',
                 help='run in dry-run mode; '
                      'no changes will be made to the system',
                 default=False,
                 dest='dryrun')
    p.add_option('--debug', '-d',
                 action='store_true',
                 help='run in debun mode',
                 default=False,
                 dest='debug')
    p.add_option('--paranoid', '-P',
                 action='store_true',
                 help='run in paranoid mode, '
                      'make changes but do not commit to repository',
                 default=False,
                 dest='paranoid')
    options = p.parse_args()[0]

    if options.debug:
        print(options)
        print("What should debug mode do?")

    # py3k compatibility
    try:
        version = raw_input("Please enter the Bcfg2 version "
                            "you are tagging (e.g. 1.0.0): ")
        name = raw_input("Your name: ")
        email = raw_input("Your email: ")
    except NameError:
        version = input("Please enter the Bcfg2 version "
                        "you are tagging (e.g. 1.0.0): ")
        name = input("Your name: ")
        email = input("Your email: ")

    # parse version into Major.Minor.MicroBuild and validate
    vkeys = ["major", "minor", "microbuild"]
    try:
        version_info = dict(zip(vkeys, version.split(".")))
        version_info["micro"] = version_info["microbuild"][0:1]
        version_info["build"] = version_info["microbuild"][1:]
        version_release = "%s.%s.%s" % (version_info['major'],
                                        version_info['minor'],
                                        version_info['micro'])

        if options.debug:
            print("version is %s" % version)
            print("version_info is %s" % version_info)
            print("version_release is %s" % version_release)

        if not version_info["major"].isdigit() \
           or not version_info["minor"].isdigit() \
           or not version_info["micro"]:
            raise VersionError('isdigit() test failed')
        if len(version_info["micro"]) > 1:
            raise VersionError('micro must be single digit because '
                               'IFMinorVersion restrictions in '
                               'Mac OS X Packaging')
    except:
        print("""Version must be of the form Major.Minor.MicroBuild,
where Major and Minor are integers and
Micro is a single digit optionally followed by Build (i.e. pre##)
E.G. 1.2.0pre1 is a valid version.
""")
        quit()

    tarname = '/tmp/%s-%s.tar.gz' % (pkgname, version)

    newchangelog = """bcfg2 (%s-0.0) unstable; urgency=low

  * New upstream release

 -- %s <%s>  %s

""" % (version,
       name,
       email,
       formatdate(localtime=True))

    # write out the new debian changelog
    if options.dryrun:
        print("*** Add the following to the top of debian/changelog:\n%s\n"
              % newchangelog)
    else:
        try:
            with open('debian/changelog', 'r+') as f:
                old = f.read()
                f.seek(0)
                f.write(newchangelog + old)
            f.close()
        except:
            print("Problem opening debian/changelog")
            print(help_message)
            quit()

    # update solaris version
    find_and_replace('solaris/Makefile', 'VERS=',
                     'VERS=%s-1\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris/pkginfo.bcfg2', 'VERSION=',
                     'VERSION="%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris/pkginfo.bcfg2-server', 'VERSION=',
                     'VERSION="%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    # update solaris IPS version
    find_and_replace('solaris-ips/Makefile', 'VERS=',
                     'VERS=%s-1\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris-ips/MANIFEST.bcfg2.header',
                     'set name=pkg.fmri value="pkg://bcfg2/bcfg2@',
                     'set name=pkg.fmri value="pkg://bcfg2/bcfg2@%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris-ips/MANIFEST.bcfg2-server.header',
                     'set name=pkg.fmri value="pkg://bcfg2/bcfg2-server@',
                     'set name=pkg.fmri value="pkg://bcfg2/bcfg2-server@%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris-ips/pkginfo.bcfg2', 'VERSION=',
                     'VERSION="%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('solaris-ips/pkginfo.bcfg2-server', 'VERSION=',
                     'VERSION="%s"\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)
    # set new version in Bcfg2/version.py
    find_and_replace('src/lib/Bcfg2/version.py',
                     '__version__ =',
                     '__version__ = "%s"\n' % version,
                     dryrun=options.dryrun)
    # replace version in misc/bcfg2.spec and misc/bcfg2-selinux.spec
    find_and_replace('misc/bcfg2.spec', 'Version:',
                     'Version:          %s\n' % version_release,
                     dryrun=options.dryrun)
    find_and_replace('misc/bcfg2-selinux.spec', 'Version:',
                     'Version:          %s\n' % version_release,
                     dryrun=options.dryrun)
    if version_info['build'].startswith('rc'):
        find_and_replace('misc/bcfg2.spec', 'global _rc ',
                         '%%global _rc %s\n' % version_info['build'],
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2-selinux.spec', 'global _rc ',
                         '%%global _rc %s\n' % version_info['build'],
                         dryrun=options.dryrun)
    elif version_info['build'].startswith('pre'):
        find_and_replace('misc/bcfg2.spec', 'global _pre ',
                         '%%global _pre %s\n' % version_info['build'],
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2-selinux.spec', 'global _pre ',
                         '%%global _pre %s\n' % version_info['build'],
                         dryrun=options.dryrun)
    else:
        # comment out pre/rc
        find_and_replace('misc/bcfg2.spec', 'global _pre ',
                         '#%%global _pre 2\n',
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2-selinux.spec', 'global _pre ',
                         '#%%global _pre 2\n',
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2.spec', 'global _rc ',
                         '#%%global _rc 1\n',
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2-selinux.spec', 'global _rc ',
                         '#%%global _rc 1\n',
                         dryrun=options.dryrun)

        find_and_replace('misc/bcfg2.spec', 'Release: ',
                         'Release:          1%{?_pre_rc}%{?dist}\n',
                         startswith=True,
                         dryrun=options.dryrun)
        find_and_replace('misc/bcfg2-selinux.spec', 'Release: ',
                         'Release:          1%{?_pre_rc}%{?dist}\n',
                         startswith=True,
                         dryrun=options.dryrun)
    find_and_replace('misc/bcfg2.spec', '%setup',
                     '%setup -q -n %{name}-%{version}%{?_pre_rc}\n',
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('misc/bcfg2-selinux.spec', '%setup',
                     '%setup -q -n %{name}-%{version}%{?_pre_rc}\n',
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('misc/bcfg2.spec', 'BuildRoot',
                     'BuildRoot:        %{_tmppath}/%{name}-%{version}%{?_pre_rc}-%{release}-root-%(%{__id_u} -n)\n',
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('misc/bcfg2-selinux.spec', 'BuildRoot',
                     'BuildRoot:        %{_tmppath}/%{name}-%{version}%{?_pre_rc}-%{release}-root-%(%{__id_u} -n)\n',
                     startswith=True,
                     dryrun=options.dryrun)
    # fix pre problem noted in
    # http://trac.mcs.anl.gov/projects/bcfg2/ticket/1129
    find_and_replace('misc/bcfg2.spec',
                     'Source0',
                     'Source0:          ftp://ftp.mcs.anl.gov/pub/bcfg/%{name}-%{version}%{?_pre_rc}.tar.gz\n',
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('misc/bcfg2-selinux.spec',
                     'Source0',
                     'Source0:          ftp://ftp.mcs.anl.gov/pub/bcfg/%{name}-%{version}%{?_pre_rc}.tar.gz\n',
                     startswith=True,
                     dryrun=options.dryrun)
    # update the version in reports
    find_and_replace('src/lib/Bcfg2/Reporting/templates/base.html',
                     'Bcfg2 Version',
                     '    <span>Bcfg2 Version %s</span>\n' % version,
                     dryrun=options.dryrun)
    # update the version in the docs
    find_and_replace('doc/conf.py', 'version =',
                     'version = \'%s.%s\'\n' % (version_info['major'],
                                                version_info['minor']),
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('doc/conf.py', 'release =',
                     'release = \'%s\'\n' % (version_release),
                     startswith=True,
                     dryrun=options.dryrun)
    # update osx Makefile
    find_and_replace('osx/Makefile', 'BCFGVER =',
                     'BCFGVER = %s\n' % (version),
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('osx/Makefile', 'MAJOR =',
                     'MAJOR = %s\n' % (version_info['major']),
                     startswith=True,
                     dryrun=options.dryrun)
    find_and_replace('osx/Makefile', 'MINOR =',
                     'MINOR = %s%s\n' % (version_info['minor'],
                                         version_info['micro']),
                     startswith=True,
                     dryrun=options.dryrun)
    # update osx Portfile
    find_and_replace('osx/macports/Portfile', 'version ',
                     'version             %s\n' % version,
                     startswith=True,
                     dryrun=options.dryrun)

    # tag the release
    #FIXME: do this using python-dulwich
    commando = {}

    commando["vcs_diff"] = "git diff"

    commando["vcs_commit"] = "git commit -asm 'Version bump to %s'" % version

    # NOTE: This will use the default email address key. If you want to sign
    #       the tag using a different key, you will need to set 'signingkey'
    #       to the proper value in the [user] section of your git
    #       configuration.
    commando["vcs_tag"] = "git tag -s v%s -m 'tagged %s release'" % (version,
                                                                     version)

    commando["create_archive"] = \
            "git archive --format=tar --prefix=%s-%s/ v%s | gzip > %s" \
            % (pkgname, version, version, tarname)

    commando["gpg_encrypt"] = "gpg --armor --output %s.gpg --detach-sig  %s" \
            % (tarname, tarname)

    # upload release to ftp
    commando["scp_archive"] = "scp %s* terra.mcs.anl.gov:/mcs/ftp/pub/bcfg/" \
            % tarname

    # Execute the commands
    if options.paranoid:
        commando_orders = ["vcs_diff"]
    else:
        commando_orders = ["vcs_commit",
                           "vcs_tag",
                           "create_archive",
                           "gpg_encrypt",
                           "scp_archive"]

    if options.dryrun:
        for cmd in commando_orders:
            print("*** dry-run: %s" % commando[cmd])
    else:
        for cmd in commando_orders:
            output = run(commando[cmd])[0].strip()
            if options.verbose:
                print(output)
                print("Ran '%s' with above output." % cmd)

if __name__ == '__main__':
    sys.exit(main())
