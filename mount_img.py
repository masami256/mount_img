#!/usr/bin/env python

from optparse import OptionParser
import os
import commands

def get_options():
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="disk image file", metavar="DISK IMAGE FILE")
    parser.add_option("-m", "--mountdir", dest="mountdir",
                      help="mount point for a disk image", metavar="MOUNT POINT")
    parser.add_option("-c", "--creatdir", dest="createdir",
                      action="store_true", help="create a directory if given mount point is not exists", default=False)
    parser.add_option("-p", "--partition", dest="partition",
                      help="partition number", default=1)
    
    (options, args) = parser.parse_args()
    
    if options.filename == None or options.mountdir == None:
        parser.error("disk image file and mount point are required")

    options.partition = int(options.partition)
    return options

def check_file(path):
    if os.path.isfile(path) != True:
        print "%s is not found" % path
        return False

    if os.access(path, os.R_OK | os.W_OK) != True:
        print "You do not have right permission to %s" % path
        return False

    return True

def check_dir(path, createdir):
    if os.path.isdir(path) != True:
        if createdir == True:
            try:
                os.mkdir(path)
                print "%s was created" % path
            except OSError:
                print "You are not allowed to create dierctory in %s" % os.path.dirname(path)
                return False
        else:
            print "%s is not found" % path
            return False
    else:
        if os.access(os.path.dirname(path), os.R_OK | os.W_OK | os.X_OK) != True:
            print "You do not have right permission to %s" % path
            return False

    return True

def get_fdisk_path():
    paths = [ "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/local/bin", "/usr/local/sbin" ]
    for path in paths:
        path = path + "/fdisk"
        if os.path.exists(path) == True:
            return path

    return None

def get_sector_size(strings):
    for s in strings:
        if s.startswith("Sector size ") == True:
            return long(s.split(':')[1].split('/')[1].split(' ')[1])

    print "could not get sector size"
    return -1

def get_start_address(strings, image, partition):
    part_num = "%(image)s%(partition)d" % { 'image':image, 'partition':partition }

    for s in strings:
        if s.startswith(part_num) == True:
            tmp = s[len(part_num):]
            return long(tmp.strip().split(' ')[0])
    return -1

def get_mount_offset(fdisk, image, partition):
    """
    fdisk (util-linux-ng 2.18)'s result is like this.
    
    Disk tmp/test.img: 5368 MB, 5368709120 bytes
    16 heads, 63 sectors/track, 10402 cylinders, total 10485760 sectors
    Units = sectors of 1 * 512 = 512 bytes
    Sector size (logical/physical): 512 bytes / 512 bytes
    I/O size (minimum/optimal): 512 bytes / 512 bytes
    Disk identifier: 0x00000000
    
    Device Boot      Start         End      Blocks   Id  System
    tmp/test.img1               1     8192015     4096007+  83  Linux
    tmp/test.img2         8192016    10240271     1024128   83  Linux
    """
    cmd = "%(command)s -l %(file)s" % { 'command':fdisk, 'file':image }
    (status, results) = commands.getstatusoutput(cmd)
    if status != 0: 
        print "executing fdisk failed"
        return -1

    strings = results.split('\n')
    size = get_sector_size(strings)
    address = get_start_address(strings, image, partition)
    if address < 0:
        print "partition %d is not found in the image." % partition
        return -1
    return long(size * address)

def mount_image(image, mountdir, offset):
    cmd = "mount -o loop,offset=%(offset)s %(image)s %(mountdir)s" % \
        { 'offset':offset, 'image':image, 'mountdir':mountdir }
    (status, results) = commands.getstatusoutput(cmd)
    if status != 0: 
        print results
        return False
    
    return True

if __name__ == "__main__":
    opts = get_options()
    
    if check_file(opts.filename) != True:
        exit(-1)

    if check_dir(opts.mountdir, opts.createdir) != True:
        exit(-1)

    fdisk_path = get_fdisk_path()
    if fdisk_path == None:
        exit(-1)

    offset = get_mount_offset(fdisk_path, opts.filename, opts.partition)
    if offset < 0:
        exit(-1)

    if mount_image(opts.filename, opts.mountdir, offset) != True:
        exit(-1)

    print "mounted %(imagefile)s on %(mountdir)s success." % { 'imagefile':opts.filename, 'mountdir':opts.mountdir }
