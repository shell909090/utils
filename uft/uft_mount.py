#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
@date: 2016-10-29
@author: Shell.Xu
@copyright: 2016, Shell.Xu <shell909090@gmail.com>
@license: BSD-3-clause
'''
import os
import gzip
import json
import time
import stat
import errno
from os import path

from fusepy import FUSE, FuseOSError, Operations, LoggingMixIn
import uft

class UnionFSFile(object):

    def __init__(self, st=None):
        if st is None:
            now = time.time()
            st = {
                'st_mode': 0o644 | stat.S_IFREG,
                'st_size': 0,
                'st_uid': os.getuid(),
                'st_gid': os.getgid(),
                'st_ctime': now,
                'st_mtime': now,
                'st_atime': now,
                'st_nlink': 1,
            }
        self.st = st

    def getattr(self):
        return self.st


class UnionFSDir(UnionFSFile):

    def __init__(self, st=None):
        if st is None:
            now = time.time()
            st = {
                'st_mode': 0o755 | stat.S_IFDIR,
                'st_size': 0,
                'st_uid': os.getuid(),
                'st_gid': os.getgid(),
                'st_ctime': now,
                'st_mtime': now,
                'st_atime': now,
                'st_nlink': 2,
            }
        super(UnionFSDir, self).__init__(st)
        self.dir = {}

    def __getitem__(self, key):
        return self.dir[key]

    def __setitem__(self, key, value):
        self.dir[key] = value
        self.st['st_size'] = len(self.dir)

    def __delitem__(self, key):
        del self.dir[key]

    def __contains__(self, item):
        return item in self.dir

    def __iter__(self):
        for key in self.dir.keys():
            yield key

    def pop(self, key):
        return self.dir.pop(key)

    def findpath(self, dirname):
        d = self
        if not dirname:
            return d
        for p in dirname.split('/'):
            if not hasattr(d, '__iter__'):
                raise FuseOSError(errno.ENOTDIR)
            if p not in d:
                raise FuseOSError(errno.ENOENT)
            d = d[p]
        return d

    def createpath(self, dirname):
        d = self
        for p in dirname.split('/'):
            if p not in d:
                d[p] = UnionFSDir()
            d = d[p]
            if not hasattr(d, '__iter__'):
                raise FuseOSError(errno.ENOTDIR)
        return d


class UnionFSOperations(Operations):

    def __init__(self):
        self.root = UnionFSDir()

    def load_fs(self, top):
        attrs = ('st_mode', 'st_size', 'st_uid', 'st_gid', 'st_ctime', 'st_mtime', 'st_atime', 'st_nlink')
        for root, dirs, files in os.walk(top):
            relroot = path.relpath(root, top).lstrip('.')
            dir = self.root.findpath(relroot)
            for fn in dirs:
                st = os.lstat(path.join(root, fn))
                dir[fn] = UnionFSDir({key: getattr(st, key) for key in attrs})
            for fn in files:
                st = os.lstat(path.join(root, fn))
                dir[fn] = UnionFSFile({key: getattr(st, key) for key in attrs})

    def load_snapshot(self, snapshot):
        with gzip.open(snapshot) as fi:
            for line in fi:
                self.load_info(json.loads(line.strip()))

    def load_info(self, info):
        fp = info['path']
        if ':' in fp:
            fp = fp.split(':', 1)[-1]
        fp = fp.lstrip(os.sep)
        dirname, basename = path.split(fp)
        if info.get('isdir'):
            dir = self.root.createpath(fp)
            dir.info = info
            st = dir.getattr()
        else:
            dir = self.root.createpath(dirname)
            if basename in dir:
                raise FuseOSError(errno.EEXIST)
            dir[basename] = UnionFSFile()
            dir[basename].info = info
            st = dir[basename].getattr()
        st['st_size'] = info.get('size', 0)
        st['st_ctime'] = info['mtime']
        st['st_mtime'] = info['mtime']
        st['st_atime'] = info['mtime']

    def readdir(self, fp, fh):
        logger.info(f'readdir {fp}')
        dir = self.root.findpath(fp.lstrip(os.sep))
        return ['.', '..'] + sorted(dir)

    def getattr(self, fp, fh=None):
        logger.info(f'getattr {fp}')
        obj = self.root.findpath(fp.lstrip(os.sep))
        return obj.getattr()

    def rename(self, old, new):
        logger.info(f'rename {old} {new}')
        old_dirname, old_basename = path.split(old.lstrip(os.sep))
        old_dir = self.root.findpath(old_dirname)
        if old_basename not in old_dir:
            raise FuseOSError(errno.ENOENT)

        new_dirname, new_basename = path.split(new.lstrip(os.sep))
        new_dir = self.root.findpath(new_dirname)
        if new_basename in new_dir:
            new_obj = new_dir[new_basename]
            if not hasattr(new_obj, '__iter__'):
                raise FuseOSError(errno.EEXIST)
            new_dir = new_obj
            new_basename = old_basename

        new_dir[new_basename] = old_dir.pop(old_basename)

    def unlink(self, fp):
        logger.info(f'unlink {fp}')
        dirname, basename = path.split(fp.lstrip(os.sep))
        dir = self.root.findpath(dirname)
        if basename not in dir:
            raise FuseOSError(errno.ENOENT)
        del dir[basename]

    rmdir = unlink

    def mkdir(self, fp, mode):
        logger.info(f'mkdir {fp} {mode}')
        dirname, basename = path.split(fp.lstrip(os.sep))
        dir = self.root.findpath(dirname)
        if basename in dir:
            raise FuseOSError(errno.EEXIST)
        dir[basename] = UnionFSDir()


class Driver(object):

    def __init__(self, config):
        self.root = config['root']
        self.record = config['record']
        self.fd = open(self.record, 'a')

    def write(self, line):
        self.fd.write(line)
        self.fd.flush()


class DiskDrive(Driver):

    def rename(self, old, new):
        self.write(f'mv "{self.root+old}" "{self.root+new}"\n')

    def unlink(self, fp):
        self.write(f'rm "{self.root+fp}"\n')

    def rmdir(self, fp):
        self.write(f'rmdir "{self.root+fp}"\n')

    def mkdir(self, fp, mode):
        self.write(f'mkdir "{self.root+fp}"\n')


class RecordFSOperations(UnionFSOperations):
    driver_class = {
        'disk': DiskDrive,
    }

    def __init__(self, alloc_conf):
        super(RecordFSOperations, self).__init__()
        with open(alloc_conf) as fi:
            conf = json.load(fi)
        self.drivers = {}
        for name, config in conf['drivers'].items():
            self.drivers[name] = self.driver_class[config['type']](config)
        self.mountpoints = {}
        for name, drivers in conf['mountpoints'].items():
            self.mountpoints[name] = [self.drivers[d] for d in drivers]

    def single_op_exec_drivers(self, name, fp):
        fp = fp.lstrip(os.sep)
        for fn, mps in self.mountpoints.items():
            if fp.startswith(fn):
                for mp in mps:
                    getattr(mp, name)(fp)

    def rename(self, old, new):
        super(RecordFSOperations, self).rename(old, new)
        old, new = old.lstrip(os.sep), new.lstrip(os.sep)
        for fn, mps in self.mountpoints.items():
            if old.startswith(fn) and new.startswith(fn):
                for mp in mps:
                    mp.rename(old, new)

    def unlink(self, fp):
        super(RecordFSOperations, self).unlink(fp)
        self.single_op_exec_drivers('unlink', fp)

    def rmdir(self, fp):
        super(RecordFSOperations, self).rmdir(fp)
        self.single_op_exec_drivers('rmdir', fp)

    def mkdir(self, fp, mode):
        super(RecordFSOperations, self).mkdir(fp, mode)
        fp = fp.lstrip(os.sep)
        for fn, mps in self.mountpoints.items():
            if fp.startswith(fn):
                for mp in mps:
                    mp.mkdir(fp, mode)

@uft.register_command
class Mount(object):

    def register(self, parser):
        parser.add_argument('--record', '-r', help='record operations')
        parser.add_argument('--underlay', '-u', help='loglevel')
        parser.add_argument('snapshot', help='snapshot file.')
        parser.add_argument('mount', help='mount point.')

    def execute(self):
        global logger
        logger = self.logger
        if self.args.record:
            ufsop = RecordFSOperations(self.args.record)
        else:
            ufsop = UnionFSOperations()
        if self.args.underlay:
            ufsop.load_fs(self.args.underlay)
        ufsop.load_snapshot(self.args.snapshot)
        logger.warning('load done')
        fuse = FUSE(ufsop, self.args.mount, foreground=True)


def main():
    mnt = Mount()

    import logging
    import argparse
    parser = argparse.ArgumentParser()
    mnt.register(parser)
    parser.add_argument('--loglevel', '-l', default='warning', help='loglevel')
    mnt.args = parser.parse_args()

    mnt.logger = logging.getLogger()
    mnt.logger.setLevel(mnt.args.loglevel.upper())

    mnt.execute()


if __name__ == '__main__':
    main()
