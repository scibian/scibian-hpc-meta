#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Scibian Project <legal@scibian.org>
#
# This file is part of scibian-hpc-meta.
#
# scibian-hpc-meta is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# scibian-hpc-meta is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License
# along with scibian-hpc-meta.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import tempfile
import shutil
import subprocess
from debian import deb822

REPOS = [ 'deb http://deb.debian.org/debian jessie main contrib non-free',
          'deb http://scibian.org/repo/ scibian8 main' ]

DIFF_PACKAGES = [ 'scibian-hpc-graphical', 'scibian-hpc-frontend' ]

class Dep(object):

    def __init__(self, pkg, name):
        self.pkg = pkg
        self.name = name

    def __str__(self):
        return "%s [pkg: %s]" % (self.name, self.pkg)


def get_deps():

    print("parsing deps...")
    with open('debian/control') as fh_ctl:
        control = fh_ctl.readlines()

    deps = []

    for paragraph in deb822.Deb822.iter_paragraphs(control):
        pkg_name = paragraph.get('Package')
        deps_s = paragraph.get('Depends')
        if deps_s is not None:
            for dep in deps_s.split(','):
                dep_name = dep.strip().split(' ')[0].split(':')[0]
                if len(dep_name) and not dep_name.startswith('scibian-hpc-'):
                    found = False
                    for dep in deps:
                        if dep.name == dep_name:
                            if dep.pkg in DIFF_PACKAGES and pkg_name in DIFF_PACKAGES:
                                result = '[fair]'
                            else:
                                result = '[check required]'
                            print("pkg %s in deps of %s and %s %s" % (dep_name, dep.pkg, pkg_name, result))
                            found = True
                    if not found:
                        deps.append(Dep(pkg_name, dep_name))

    return deps 

def dl_pkgs_list(proxy):

    print("downloading pkg list...")
    tmp_dir = tempfile.mkdtemp()

    src_file = os.path.join(tmp_dir, 'sources.list')
    with open(src_file, 'w+') as src_fh:
        src_fh.write('\n'.join(REPOS))

    os.makedirs(os.path.join(tmp_dir, 'var', 'lib', 'apt', 'lists', 'partial'))
    os.makedirs(os.path.join(tmp_dir, 'cache', 'archives', 'partial'))

    cmd = ['apt-get', '-o', 'Debug::NoLocking=true',
                      '-o', 'Dir=%s' % (tmp_dir),
                      '-o', 'Dir::Cache=cache',
                      '-o', "Dir::Etc=%s" % (tmp_dir),
                      '-o', 'Acquire::AllowInsecureRepositories=true',
                      'update']
    
    if proxy is not None:
        cmd.insert(11, '-o')
        cmd.insert(12, "Acquire::http::Proxy=%s" % (proxy))

    print("running cmd: %s" % (' '.join(cmd)))
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    print ("output : %s" % (output))
    return tmp_dir


def parse_pkg_file(path):

    with open(path) as fh:
        packages = fh.readlines()

    pkgs = []

    for paragraph in deb822.Deb822.iter_paragraphs(packages):
        pkg = paragraph.get('Package')
        if pkg is not None:
            pkgs.append(pkg)

    return pkgs


def get_pkgs(tmp_dir):

    print("parsing pkg list...")
    pkgs = []

    list_dir = os.path.join(tmp_dir, 'var', 'lib', 'apt', 'lists')
    for pkg_file in os.listdir(list_dir):
        if pkg_file.endswith('amd64_Packages'):
            pkg_file_path = os.path.join(list_dir, pkg_file)
            pkgs.extend(parse_pkg_file(pkg_file_path))

    print("removing tmp dir %s" % (tmp_dir))
    shutil.rmtree(tmp_dir)
    return pkgs

def main():

    # get optional proxy arg
    proxy = None
    if len(sys.argv) > 2:
        print("usage: python3 %s [proxy]" % (__file__))
        sys.exit(1)
    elif len(sys.argv) == 2:
        proxy = sys.argv[1]

    deps = get_deps()
    tmp_dir = dl_pkgs_list(proxy)
    pkgs = get_pkgs(tmp_dir)
    for dep in deps:
        if dep.name not in pkgs:
            print("pkg %s not found in debian/scibian repositories" % (dep))
 
if __name__ == '__main__':
    main()
