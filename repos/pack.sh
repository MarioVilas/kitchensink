#!/bin/sh
# Compress all subdirectories into tar.bz2 files and delete them.
set -e
for target in */
do
	target=${target%/}
	tar -cvjf $target.tar.bz2 $target/
	rm -fr -- $target/
done

