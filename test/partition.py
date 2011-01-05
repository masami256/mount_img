#!/usr/bin/env python

import os
import guestfs

if __name__ == "__main__":
    g = guestfs.GuestFS ()
    f = open("/home/masami/tmp/test.img", "w")
    f.truncate (1024 * 1024 * 1024 * 5)
    f.close()
   
    g.add_drive("/home/masami/tmp/test.img")
    g.launch()
    g.sfdiskM("/dev/sda",[",4000,83", ",1000,c"])
    print "sfdiskM was finished."
    print g.list_partitions()

    print "setup /dev/sda1"
    g.mkfs("ext3", "/dev/sda1")
    g.mount("/dev/sda1", "/")
    g.mkdir("/test1")
    g.mkdir("/test2")
    g.sync
    g.umount_all()

    print "setup /dev/sda2"
    g.mkfs("vfat", "/dev/sda2")
    g.mount("/dev/sda2", "/")
    g.mkdir("/test3")
    g.mkdir("/test4")
    g.sync()
    g.umount_all()

    print "file systems were created\n"

