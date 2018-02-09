#!/usr/bin/env python
"""Print all of the clone-urls for a GitHub user or organization, excluding forks.

It requires the pygithub3 module, which you can install like this::

    $ sudo -H pip install pygithub3

Usage example::

    $ for url in $(python list-all-repos.py MarioVilas); do git clone $url; done

Original idea from https://gist.github.com/ralphbean/5733076
"""

import sys

try:
    import pygithub3
except ImportError:
    sys.stderr.write(__doc__.replace("::", ":"))
    exit(1)

users = sys.argv[1:]
if not users:
    sys.stderr.write(__doc__.replace("::", ":"))
    exit(1)

gh = pygithub3.Github()
for u in users:
    repos = gh.repos.list(user=u, type="all").all()
    repos = (r.clone_url for r in repos if not r.fork)
    print "\n".join(repos)

