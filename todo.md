
# Obolix todo list


_**Obol general enhancement:**_

  - [x] ~~Retrieve highest UID/GID before creating users~~ (not needed, because the code is currently retrieving free UID/GIDs greater than `1050`),
  - [x] Date function with "YYYY-MM-DD" format for `shadowLastChange` and `shadowExpire` (old style is still available; for the show option, use `--json` argument),
    - [x] add the abality to view the date from `shadowExpire` or `shadowLastChange` values,
    - [x] add the abality to enter directly a final date to `--expire` option and convert it to an `shadow` value,
    - [x] possibility to keep the old format (using `--json`, or with `--expire` days),
  - [x] integrating `/etc/skel` choice and copy it, instead of creating blank home directory,
    - [x] add the argument in the `main.py`,
    - [x] add the corresponding code in `src/obol.py` (when adding or modifying users),
  - [x] change home directory allowing creating a new homedir somewhere else when modifying an existing user,
  - [x] fix permissions issue while creating homedir,
    - [x] create a permission function,
  - [x] force delete group even if there are still users in it (?),
  - [x] accept to delete a user from a group even if the user does not exists anymore,
  - [x] better management of secondary group (if _memberOf_ is missing)
  - [x] adapt print size when last item is a very long list (need to be right stripped).

_**Optionnal advanced custom tasks:**_
  - [x] create a sandboxed environment to modify this code with podman,
  - [x] add a python `.gitignore` standard file,
  - [x] add a README for podman,
  - [x] add a README for the tool,

_**Additional custom ISDM tasks:**_

  - [ ] Create scratch directories,
    - [x] add parameters in the configuration file,
    - [x] ~~add arguments in `main.py`~~,
    - [ ] implementing the functions
      - [x] function itself
      - [x] when creating a user
      - [x] when modifying a user
      - [ ] when renaming a group
      - [x] when group is the user's primary group
  - [ ] Create symbolic links from homedir to scratchs,
    - [x] add parameters in the configuration file,
    - [x] ~~add arguments in `main.py`~~,
    - [ ] implementing the functions
      - [x] function itself
      - [x] when creating a user
      - [ ] when modifying a user
        - [x] when modifying groups
        - [ ] when renaming the user
  - [x] delete user scratch directory when deleting a user,
  - [x] delete user home directory when deleting a user,
  - [x] delete symbolic links from homedir to scratchs when modifying user's groups,
  - [ ] subscribe user to mailing list(s)
  - [ ] unsubscribe user to mailing list(s)
  