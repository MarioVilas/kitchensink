#!/bin/bash

# This script is called from our systemd unit file to mount or unmount a USB drive.

usage()
{
    echo "Usage: $0 {add|remove} device_name (e.g. sdb1)"
    exit 1
}

if [[ $# -ne 2 ]]; then
    usage
fi

ACTION=$1
DEVBASE=$2
DEVICE="/dev/${DEVBASE}"

# See if this drive is already mounted, and if so where
MOUNT_POINT=$(/bin/mount | /bin/grep ${DEVICE} | /usr/bin/awk '{ print $3 }')

do_mount()
{
    if [[ -n ${MOUNT_POINT} ]]; then
        echo "Warning: ${DEVICE} is already mounted at ${MOUNT_POINT}"
        exit 1
    fi

    # Get info for this drive: $ID_FS_LABEL, $ID_FS_LABEL_ENC, $ID_FS_UUID, and $ID_FS_TYPE
    /sbin/blkid -o udev ${DEVICE}
    eval $(/sbin/blkid -o udev ${DEVICE} | grep -E ID_FS_LABEL\|ID_FS_UUID\|ID_FS_TYPE)

    # Figure out a mount point to use
    LABEL=${ID_FS_LABEL}
    if [[ "$LABEL" == "System_Reserved" ]]; then
        echo "Warning: $DEVICE appears to be a Windows System Reserved partition, ignored"
        exit 1
    fi
    if [[ -z "$LABEL" ]]; then
        # Label could not be determined
        LABEL+="-${DEVBASE}"
    elif /bin/grep -q " /media/${LABEL} " /etc/mtab; then
        # Already in use, make a unique one
        LABEL+="-${DEVBASE}"
    fi
    MOUNT_POINT="/media/${LABEL}"

    echo "Mount point: ${MOUNT_POINT}"

    /bin/mkdir ${MOUNT_POINT}

    # Global mount options
    OPTS="rw,nodiratime,noatime"

    # File system type specific mount options
    if [[ ${ID_FS_TYPE} == "vfat" ]]; then
        OPTS+=",users,uid=1000,gid=1000,umask=007,utf8=1,shortname=mixed,sync,flush"
    elif [[ ${ID_FS_TYPE} == "exfat" ]]; then
        OPTS+=",users,uid=1000,gid=1000,umask=007,utf8=1,shortname=mixed,async"
    elif [[ ${ID_FS_TYPE} == "ntfs" ]]; then
        OPTS+=",users,uid=1000,gid=1000,umask=007,utf8=1,shortname=mixed,async"
    elif [[ ${ID_FS_TYPE} == "ext4" ]]; then
        OPTS+=",nodelalloc,async"
    else
        OPTS+=",async"
    fi

    if ! /bin/mount -o ${OPTS} ${DEVICE} ${MOUNT_POINT}; then
        echo "Error mounting ${DEVICE} (status = $?)"
        /bin/rmdir -- ${MOUNT_POINT}
        exit 1
    fi

    echo "**** Mounted ${DEVICE} at ${MOUNT_POINT} ****"
}

do_unmount()
{
    echo "**** Unmounting ${DEVICE}"
    if [[ ! -z ${MOUNT_POINT} ]]; then
        /bin/umount ${DEVICE}
        /bin/rmdir -- ${MOUNT_POINT}
        echo "**** Unmounted ${DEVICE}"
    else
        echo "Warning: ${DEVICE} is not mounted"

        # Delete all empty dirs in /media that aren't being used as mount
        # points. This is kind of overkill, but if the drive was unmounted
        # prior to removal we no longer know its mount point, and we don't
        # want to leave it orphaned...
        for f in /media/* ; do
            if [[ -n $(/usr/bin/find "$f" -maxdepth 0 -type d -empty) ]]; then
                if ! /bin/grep -q " $f " /etc/mtab; then
                    echo "**** Removing mount point $f"
                    /bin/rmdir -- "$f"
                fi
            fi
        done
    fi
}

case "${ACTION}" in
    add)
        do_mount
        ;;
    remove)
        do_unmount
        ;;
    *)
        usage
        ;;
esac
