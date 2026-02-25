#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######################################################################
# Obolix user management tool
#
# From original work from ClusterVision / Diego Sonaglia
# https://github.com/clustervision/obol
# forked from Hans
# https://github.com/hansthen/obol/, version 1.2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License (included with the sources) for more
# details.
######################################################################

__author__ = "Rémy Dernat"
__copyright__ = ""
__license__ = "GPL"
__version__ = "1.8"
__maintainer__ = "Rémy Dernat"
__email__ = "remy.dernat@umontpellier.fr"
__status__ = "Development"


import os
import sys
import time
import json
import hashlib
import base64
import configparser
import secrets
import inspect
from getpass import getpass
import ldap

from utils import misc as m, isdm_hooks as ih, printing as p




def show_output(func):
    """Function decorator to print the output of a function"""

    def inner(obol, *args, **kwargs):
        output = func(obol, *args, **kwargs)
        # get default output type for function
        default_output_type = inspect.signature(func).parameters.get("output_type", None)
        if default_output_type:
            default_output_type = default_output_type.default
        output_type = default_output_type or kwargs.pop("output_type", None)

        if output_type == "json":
            print(json.dumps(output, indent=2))
        elif output_type == "table":
            p.print_table(output)
        return output
    return inner


class Obol:
    """Obol class"""

    user_fields = [
        "cn",
        "uid",
        "uidNumber",
        "gidNumber",
        "homeDirectory",
        "loginShell",
        "shadowExpire",
        "shadowLastChange",
        "shadowMax",
        "shadowMin",
        "shadowWarning",
        "sn",
        "userPassword",
        "givenName",
        "mail",
        "telephoneNumber",
        "memberOf",
    ]
    group_fields = [
        "cn",
        "gid",
        "gidNumber",
        "member"
    ]

    def default_parser(self, values):
        """Default parser for LDAP fields"""
        return values[0].decode("utf-8")

    def member_parser(self, values):
        """Parser for LDAP member fields"""
        parsed_values = [v.decode("utf-8").split(",")[0].split("=")[1] for v in values]
        return parsed_values

    def member_of_parser(self, values):
        """Parser for LDAP memberOf fields"""
        parsed_values = [v.decode("utf-8").split(",")[0].split("=")[1] for v in values]
        return parsed_values

    def default_serializer(self, value):
        """Default serializer for LDAP fields"""
        return [value.encode("utf-8")]

    def member_serializer(self, values):
        """Serializer for LDAP member fields"""
        serialized_values = [f"uid={v},ou=People,{self.base_dn}".encode("utf-8") for v in values]
        return serialized_values

    def member_of_serializer(self, values):
        """Serializer for LDAP memberOf fields"""
        serialized_values = [f"cn={v},ou=Group,{self.base_dn}".encode("utf-8") for v in values]
        return serialized_values


    def __init__(self, config_path, overrides=None):
        self.config = configparser.ConfigParser()
        self.parsers = {
            "memberOf": self.member_of_parser,
            "member": self.member_parser	
        }


        # try to open and read configuration from config_path
        with open(config_path, "r", encoding="utf-8") as config_file:
            self.config.read_file(config_file)

        # override LDAP params from cli
        for key, value in (overrides or {}).items():
            if value and (key in self.config["ldap"]):
                self.config.set("ldap", key, value)

        # try binding to LDAP
        try:
            ldap_host = self.config.get("ldap", "host")
            ldap_bind_dn = self.config.get("ldap", "bind_dn")
            ldap_bind_pass = self.config.get("ldap", "bind_pass")

            self.conn = ldap.initialize(ldap_host)
            self.conn.simple_bind_s(ldap_bind_dn, ldap_bind_pass)
        except Exception as exc:
            raise ConnectionError("Failed binding to ldap") from exc

    @property
    def base_dn(self):
        """Returns the base DN"""
        return self.config.get("ldap", "base_dn")

    @property
    def users_dn(self):
        """Returns the users DN"""
        return f"ou=People,{self.base_dn}"

    @property
    def groups_dn(self):
        """Returns the groups DN"""
        return f"ou=Group,{self.base_dn}"

    @classmethod
    def _make_secret(cls, password):
        """Encodes the given password as a base64 SSHA hash+salt buffer"""
        if password.startswith("{SSHA}"):
            return password

        salt = os.urandom(4)
        # Hash the password and append the salt
        sha = hashlib.sha1(password.encode("utf-8"))
        sha.update(salt)
        # Create a base64 encoded string of the concatenated digest + salt
        digest_b64 = base64.b64encode(sha.digest() + salt).decode("utf-8")

        # Tag the digest above with the {SSHA} tag
        tagged_digest = f"{{SSHA}}{digest_b64}"

        return tagged_digest

    def _next_id(self, idlist, id_min=1050, id_max=15000):
        idlist = [int(i) for i in idlist]
        free_ids = [i for i in range(id_min, id_max) if i not in idlist]
        next_id = str(min(free_ids))
        return next_id

    def _next_uid(self, _users):
        idlist = [u["uidNumber"] for u in _users or []]
        return self._next_id(idlist, 1050, 15000)

    def _next_gid(self, _groups):
        idlist = [g["gidNumber"] for g in _groups or []]
        return self._next_id(idlist, 1050, 15000)

    def _user_show_by_uid(self, uid, _users=None):
        """Show system user details"""
        users = _users or self.user_list()
        for user in users:
            if user["uidNumber"] == str(uid):
                return user
        return None

    def _group_show_by_gid(self, gid, _groups=None):
        """Show system group details"""
        groups = _groups or self.group_list()
        for group in groups:
            if group["gidNumber"] == str(gid):
                return group
        return None

    def _username_exists(self, username, _users=None):
        """Check if a username exists"""
        users = _users or self.user_list()
        for user in users:
            if user["uid"] == username:
                return True
        return False

    def _groupname_exists(self, groupname, _groups=None):
        """Check if a groupname exists"""
        groups = _groups or self.group_list()
        for group in groups:
            if group["cn"] == groupname:
                return True
        return False

    def _usernames_exists(self, usernames, _users=None):
        """Check if all the usernames exists"""
        users = _users or self.user_list()
        for username in usernames:
            if not self._username_exists(username, _users=users):
                return False
        return True

    def _groupnames_exists(self, groupnames, _groups=None):
        """Check if all the groupnames exists"""
        groups = _groups or self.group_list()
        for groupname in groupnames:
            if not self._groupname_exists(groupname, _groups=groups):
                return False
        return True

    def _uid_exists(self, uid, _users=None):
        """Check if a uid exists"""
        users = _users or self.user_list()
        for user in users:
            if user["uidNumber"] == str(uid):
                return True
        return False

    def _gid_exists(self, gid, _groups=None):
        """Check if a gid exists"""
        groups = _groups or self.group_list()
        for group in groups:
            if group["gidNumber"] == str(gid):
                return True
        return False

    ###### List
    @show_output
    def user_list(self, **kwargs):
        """List users defined in the system"""

        # Retrieve users from LDAP
        users = []
        filter_dn = "(objectclass=posixAccount)"
        for _, attrs in self.conn.search_s(
            self.users_dn, ldap.SCOPE_SUBTREE, filter_dn, self.user_fields
        ):
            # Decode bytes to utf8 and parse data
            user = {
                k: self.parsers.get(k, self.default_parser)(v)
                for k, v in attrs.items()
            }
            users.append(user)

        return users

    @show_output
    def group_list(self, **kwargs):
        """List groups defined in the system"""

        # Retrieve groups from LDAP
        groups = []
        filter_dn = "(objectclass=posixGroup)"
        for _, attrs in self.conn.search_s(
            self.groups_dn, ldap.SCOPE_SUBTREE, filter_dn, self.group_fields
        ):
            # Decode bytes to utf8 and parse data
            group = {
                k: self.parsers.get(k, self.default_parser)(v)
                for k, v in attrs.items()
            }
            groups.append(group)
        return groups

    ###### Show
    @show_output
    def user_show(self, username, **kwargs):
        """Show system user details"""

        # Retrieve first user from LDAP query, raise error if not found
        filter_dn = f"(uid={username})"
        for _, attrs in self.conn.search_s(
            self.users_dn, ldap.SCOPE_SUBTREE, filter_dn, self.user_fields
        ):
            # Decode bytes to utf8 and parse data
            user = {
                k: self.parsers.get(k, self.default_parser)(v)
                for k, v in attrs.items()
            }
            break
        else:
            # Raise error if no user found
            raise LookupError(f"User '{username}' does not exist")

        return user

    @show_output
    def group_show(self, groupname, **kwargs):
        """
        Show system group details
        """

        # Retrieve first group from LDAP query, raise error if not found
        filter_dn = f"(cn={groupname})"
        for _, attrs in self.conn.search_s(
            self.groups_dn, ldap.SCOPE_SUBTREE, filter_dn, self.group_fields
        ):
            # Decode bytes to utf8 and parse data
            group = {
                k: self.parsers.get(k, self.default_parser)(v)
                for k, v in attrs.items()
            }
            break
        else:
            # Raise error if no group found
            raise LookupError(f"Group {groupname} does not exist")
        return group

    def _get_user_secondary_groups_from_groups(self, username):
        """
        Récupère les groupes secondaires d'un utilisateur en parcourant les entrées de groupe.
        @param username: Le username de l'utilisateur.
        @Return: Une liste des noms communs (cn) des groupes secondaires.
        """
        secondary_groups = []
        all_groups = self.group_list()
        for group_entry in all_groups:
            group_cn = group_entry.get("cn")
            members_raw = group_entry.get("member", [])
            members_dn = []
            if isinstance(members_raw, list):
                for m_val in members_raw:
                    members_dn.append(m_val.decode('utf-8') if isinstance(m_val, bytes) else m_val)
            elif isinstance(members_raw, (str, bytes)):
                members_dn.append(members_raw.decode('utf-8') if isinstance(members_raw, bytes) else members_raw)
            if username in members_dn:
                secondary_groups.append(group_cn)
        return secondary_groups

    ###### Add
    def user_add(
        self,
        username,
        cn=None,
        sn=None,
        given_name=None,
        password=None,
        autogen_password=False,
        prompt_password=False,
        uid=None,
        gid=None,
        mail=None,
        phone=None,
        shell=None,
        with_scratchs=None,
        with_symlinks=None,
        skel=None,
        groupname=None,
        groups=None,
        home=None,
        expire=None,
        **kwargs,
    ):
        """Add a user to the LDAP directory"""
        # Ensure username's uniqueness
        existing_users = self.user_list()
        if self._username_exists(username, _users=existing_users):
            raise ValueError(f"Username {username} already exists")

        # Ensure uid's correctness or generate one
        if uid:
            if self._uid_exists(uid, _users=existing_users):
                raise ValueError(f"UID {uid} already exists")
        else:
            uid = self._next_uid(existing_users)

        # Ensure groups correctness
        create_group = False
        existing_groups = self.group_list()
        if groupname or gid:
            if groupname:
                # if only groupname is specified: groupname should exist
                if not self._groupname_exists(groupname, _groups=existing_groups):
                    raise ValueError(f"Group {groupname} does not exist")
                gid = [g["gidNumber"] for g in existing_groups if g["cn"] == groupname][
                    0
                ]
            if gid:
                # if only gid is specified: gid should exist
                if not self._gid_exists(gid, _groups=existing_groups):
                    raise ValueError(f"GID {gid} does not exist")
                groupname = [g["cn"] for g in existing_groups if g["gidNumber"] == gid][
                    0
                ]
            if groupname and gid:
                # if both groupname and gid are specified: should refer to same group
                if (
                    groupname
                    != [g["cn"] for g in existing_groups if g["gidNumber"] == gid][0]
                ):
                    raise ValueError(f"Group {groupname} does not have gid {gid}")

        else:
            # neither groupname or gid is specified: groupname <- username
            groupname = username
            if self._groupname_exists(groupname, _groups=existing_groups):
                gid = [g["gidNumber"] for g in existing_groups if g["cn"] == groupname][
                    0
                ]
            else:
                gid = self._next_gid(existing_groups)
                create_group = True

        # Add the user
        dn = f"uid={username},ou=People,{self.base_dn}"
        cn = cn or username
        sn = sn or username
        # following is mandatory for old config files format
        try:
            skel = skel or f"{self.config.get('users', 'skel')}"
        except configparser.NoOptionError:
            skel = "/etc/skel"
        home = home or f"{self.config.get('users', 'home')}/{username}"
        shell = shell or self.config.get("users", "shell")

        with_scratchs = ih.check_if_custom('create_scratch_folders')
        with_symlinks = ih.check_if_custom('create_symlink_from_home')

        if (expire is not None) and (expire != "-1"):
            if "-" in expire:
                year_month_day = expire.split("-")
                expire = m.rev_calendar(year_month_day)
            else:
                expire = str(int(expire) + int(time.time() / 86400))
        else:
            expire = "-1"
        user_record = [
            (
                "objectclass",
                [
                    b"top",
                    b"person",
                    b"organizationalPerson",
                    b"inetOrgPerson",
                    b"posixAccount",
                    b"shadowAccount",
                ],
            ),
            ("uid", [username.encode("utf-8")]),
            ("cn", [cn.encode("utf-8")]),
            ("sn", [sn.encode("utf-8")]),
            ("loginShell", [shell.encode("utf-8")]),
            ("uidNumber", [str(uid).encode("utf-8")]),
            ("gidNumber", [str(gid).encode("utf-8")]),
            ("homeDirectory", [home.encode("utf-8")]),
            ("shadowMin", [b"0"]),
            ("shadowMax", [b"99999"]),
            ("shadowWarning", [b"7"]),
            ("shadowExpire", [str(expire).encode("utf-8")]),
            ("shadowLastChange", [str(int(time.time() / 86400)).encode("utf-8")]),
        ]

        if given_name:
            user_record.append(("givenName", [given_name.encode("utf-8")]))

        if mail:
            user_record.append(("mail", [mail.encode("utf-8")]))

        if phone:
            user_record.append(("telephoneNumber", [phone.encode("utf-8")]))

        if autogen_password:
            password = secrets.token_urlsafe(16)
            print(f"Generated password for user {username}: {password}")

        if prompt_password:
            password = getpass(f"Enter password for user {username}: ")

        if password:
            hashed_password = self._make_secret(password).encode("utf-8")
            user_record.append(("userPassword", [hashed_password]))

        # Add the user
        self.conn.add_s(dn, user_record)

        gids= {}
        # Add the default group if it does not exist
        if create_group:
            self.group_add(groupname, gid, [username])

        # Add the user to the specified groups
        for group in (groups or []) + [groupname]:
            self.group_addusers(group, [username])
            group_gid = self.group_show(group)['gidNumber']
            gids[group] = group_gid
        if home:
            m.create_homedir(uid, gid, home, skel)

        groups = (groups or []) + ([groupname] or [])
        if with_scratchs:
            if groupname != [username]:
                ih.create_scratch_folders(username, groups, uid, gids)
                if with_symlinks:
                    ih.create_symlinks(home, username, groups)

    def group_add(self, groupname=None, gid=None, users=None, **kwargs):
        """Add a group to the LDAP"""

        # Ensure groupname's uniqueness
        existing_groups = self.group_list()

        if self._groupname_exists(groupname, _groups=existing_groups):
            raise ValueError(f"Groupname {groupname} already exists")

        # Ensure gid's uniqueness
        if gid:
            if self._gid_exists(gid, _groups=existing_groups):
                raise ValueError(f"GID {gid} already exists")
        else:
            gid = self._next_gid(existing_groups)

        if users:
            # Ensure users exist
            existing_usernames = [u["uid"] for u in self.user_list()]
            incorrect_usernames = [u for u in users if u not in existing_usernames]
            if len(incorrect_usernames) > 0:
                raise ValueError(
                    f"Users '{', '.join(incorrect_usernames)}' do not exist"
                )

        # Add group
        group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
        group_record = [
            ("objectclass", [b"top", b"groupOfMembers", b"posixGroup"]),
            ("cn", [groupname.encode("utf-8")]),
            ("gidNumber", [str(gid).encode("utf-8")]),
        ]
        self.conn.add_s(group_dn, group_record)

        # Add users to group
        if users:
            self.group_addusers(groupname, users)

    ###### Delete
    def user_delete(self, username, **kwargs):
        """Delete a user from the system"""

        # Ensure user exists
        usernames = [u["uid"] for u in self.user_list()]
        if username not in usernames:
            raise LookupError(f"User '{username}' does not exist")

        # Delete the user
        user_dn = f"uid={username},ou=People,{self.base_dn}"
        existing_user = self.user_show(
            username,
        )

        # delete user from groups
        primary_group = self._group_show_by_gid(existing_user['gidNumber'])['cn']
        secondary_groups = self._get_user_secondary_groups_from_groups(username)
        for g in secondary_groups:
            self.group_delusers(g, [username], True, True)

        self.conn.delete_s(user_dn)
        # Delete the default group if it exists and has no other members
        try:
            group = self.group_show(username)
            if len(group.get("member", [])) == 0:
                group_dn = f"cn={group['cn']},ou=Group,{self.base_dn}"
                self.conn.delete_s(group_dn)
        except LookupError:
            self.group_delusers(primary_group, [username], True, True)

        user_scratch_force_removal = False
        homedir_force_removal = False
        # delete scratch directory if user_scratch_force_removal is True
        # delete home directory if homedir_force_removal is True
        user_scratch_force_removal = ih.check_if_custom('user_scratch_force_removal')
        homedir_force_removal = ih.check_if_custom('homedir_force_removal')

        ih.remove_user_folders(user_scratch_force_removal, homedir_force_removal, \
            username, existing_user["homeDirectory"])

    def group_delete(self, groupname, force=None, **kwargs):
        """Delete a group from the system"""

        # Ensure group exists
        groupnames = [g["cn"] for g in self.group_list()]
        if groupname not in groupnames:
            raise LookupError(f"Group '{groupname}' does not exist")

        # Ensure group has no members
        group = self.group_show(groupname)
        if len(group.get("member", [])) > 0:
            if force:
                group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
                self.conn.delete_s(group_dn)
            else:
                raise ValueError(f"Group '{groupname}' has members")
        # Delete the group
        group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
        self.conn.delete_s(group_dn)

    ###### Modify
    def user_modify(
        self,
        username,
        cn=None,
        sn=None,
        given_name=None,
        password=None,
        autogen_password=False,
        prompt_password=False,
        uid=None,
        gid=None,
        mail=None,
        phone=None,
        shell=None,
        with_scratchs=None,
        with_symlinks=None,
        skel=None,
        groupname=None,
        groups=None,
        home=None,
        expire=None,
        **kwargs,
    ):
        """Modify a user"""

        # Ensure user exists
        existing_user = self.user_show(
            username,
        )
        existing_groups = self.group_list()

        primary_group_changed = False
        mod_attrs = []

        groups_to_add = []
        groups_to_del = []

        if cn:
            mod_attrs.append((ldap.MOD_REPLACE, "cn", f"{cn}".encode("utf-8")))
        if sn:
            mod_attrs.append((ldap.MOD_REPLACE, "sn", f"{sn}".encode("utf-8")))
        if given_name:
            mod_attrs.append(
                (ldap.MOD_REPLACE, "givenName", f"{given_name}".encode("utf-8"))
            )
        if uid:
            raise NotImplementedError("changing UID of existing user is not supported")

        gids = {}
        if groupname:
            # if groupname is specified: groupname should exist
            if not self._groupname_exists(groupname, _groups=existing_groups):
                raise ValueError(f"Group '{groupname}' does not exist")

            _gid = [g["gidNumber"] for g in existing_groups if g["cn"] == groupname][0]
            # if also gid is specified: should refer to same group
            if gid and (gid != _gid):
                raise ValueError(f"Group '{groupname}' does not have gid {gid}")
            gid = _gid
        elif gid:
            # if only gid is specified: gid should exist
            if not self._gid_exists(gid, _groups=existing_groups):
                raise ValueError(f"GID {gid} does not exist")

        if gid:
            groupname = [g["cn"] for g in existing_groups if g["gidNumber"] == gid][0]

        if gid or groupname:
            gids[groupname] = gid
            old_groupname = [
                g["cn"]
                for g in existing_groups
                if g["gidNumber"] == existing_user["gidNumber"]
            ][0]
            mod_attrs.append((ldap.MOD_REPLACE, "gidNumber", f"{gid}".encode("utf-8")))
            primary_group_changed = True

        if mail:
            mod_attrs.append((ldap.MOD_REPLACE, "mail", f"{mail}".encode("utf-8")))

        if phone:
            mod_attrs.append(
                (ldap.MOD_REPLACE, "telephoneNumber", f"{phone}".encode("utf-8"))
            )
        if shell:
            mod_attrs.append(
                (ldap.MOD_REPLACE, "loginShell", f"{shell}".encode("utf-8"))
            )
        if home:
            mod_attrs.append(
                (ldap.MOD_REPLACE, "homeDirectory", f"{home}".encode("utf-8"))
            )
            try:
                skel = skel or f"{self.config.get('users', 'skel')}"
            except configparser.NoOptionError:
                skel = "/etc/skel"

        if expire:
            if (expire is not None) and (expire != "-1"):
                if "-" in expire:
                    year_month_day = expire.split("-")
                    expire = m.rev_calendar(year_month_day)
                else:
                    expire = str(int(expire) + int(time.time() / 86400))
            else:
                expire = "-1"
            mod_attrs.append(
                (ldap.MOD_REPLACE, "shadowExpire", f"{expire}".encode("utf-8"))
            )

        if autogen_password:
            password = secrets.token_urlsafe(16)
            print(f"Generated password for user {username}: {password}")
        if prompt_password:
            password = getpass(f"Enter password for user {username}: ")
        if password:
            hashed_password = self._make_secret(password).encode("utf-8")
            mod_attrs.append((ldap.MOD_REPLACE, "userPassword", hashed_password))
        if groups:
            # Ensure groups exist
            existing_groupnames = [g["cn"] for g in self.group_list()]
            incorrect_groupnames = [g for g in groups if g not in existing_groupnames]
            if len(incorrect_groupnames) > 0:
                incorrect_groupnames_str = ", ".join(incorrect_groupnames)
                raise ValueError(f"Groups '{incorrect_groupnames_str}' do not exist")

            primary_group = [
                g["cn"]
                for g in existing_groups
                if g["gidNumber"] == existing_user["gidNumber"]
            ][0]

            groups_to_add = [g for g in groups if g not in existing_user.get("memberOf", [])]
            groups_to_del = [
                g
                for g in existing_user.get("memberOf", [])
                if (g not in groups) and (g != primary_group)
            ]
            if not groups_to_del:
                p.print_info("Did not found any group to delete; \
'memberOf' attribute looks empty. Checking 'member' attr from every posixGroups...")
                existing_groups = self._get_user_secondary_groups_from_groups(username)
                groups_to_del = [
                    g
                    for g in existing_groups
                    if (g not in groups) and (g != primary_group)
                ]

        # Modify the user in LDAP
        dn = f"uid={username},ou=People,{self.base_dn}"
        self.conn.modify_s(dn, mod_attrs)

        if primary_group_changed:
            # Modify the user's primary group
            groups_to_del.append(old_groupname)
            groups_to_add.append(groupname)

        with_scratchs = ih.check_if_custom('create_scratch_folders')
        with_symlinks = ih.check_if_custom('create_symlink_from_home')

        # refreshing after modifications
        existing_user = self.user_show(
            username,
        )
        if home:
            m.create_homedir(existing_user["uidNumber"], \
                existing_user["gidNumber"], home, skel)
        else:
            home = existing_user['homeDirectory']

        for group in groups_to_add:
            self.group_addusers(group, [username])
            group_gid = self.group_show(group)['gidNumber']
            gids[group] = group_gid

        if groups_to_add:
            if with_scratchs:
                if groups_to_add != [username]:
                    ih.create_scratch_folders(username, groups_to_add, \
                        existing_user["uidNumber"], gids)
                    if with_symlinks:
                        ih.create_symlinks(home, username, groups_to_add)
        for group in groups_to_del:
            self.group_delusers(group, [username], True, True)
        if groups_to_del:
            if with_symlinks:
                ih.remove_symlinks(home, None, groups_to_del)




    def group_modify(self, groupname, gid=None, users=None, **kwargs):
        """Modify a group"""

        # Ensure group exists
        existing_group = self.group_show(groupname)

        group_mod_attrs = []
        users_mod_attrs = {}
        users_to_add = []
        users_to_del = []

        if gid:
            # Not implemented yet
            raise NotImplementedError("changing GID of existing group is not supported")

        if users is not None:
            # Ensure users exist
            existing_users = self.user_list()
            existing_usernames = [u["uid"] for u in existing_users]
            incorrect_usernames = [u for u in users if u not in existing_usernames]
            if len(incorrect_usernames) > 0:
                raise ValueError(
                    f"Users '{', '.join(incorrect_usernames)}' do not exist"
                )

            existing_group_usernames = existing_group.get("member", [])
            existing_primary_group_usernames = [
                u["uid"]
                for u in existing_users
                if u["gidNumber"] == existing_group["gidNumber"]
            ]
            users_to_add = [u for u in users if u not in existing_group_usernames]
            users_to_del = [
                u
                for u in existing_group.get("member", [])
                if (u not in existing_primary_group_usernames)
            ]

        # Modify the group
        group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
        self.conn.modify_s(group_dn, group_mod_attrs)
        self.group_addusers(groupname, users_to_add)
        self.group_delusers(groupname, users_to_del, True, True)
        # Modify the users that use this group as primaryGroup
        for user_dn, user_mod_attrs in users_mod_attrs.items():
            self.conn.modify_s(user_dn, user_mod_attrs)

    ###### Other
    def group_rename(self, groupname, new_groupname, **kwargs):
        """Rename a group"""

        existing_groups = self.group_list()
        # Ensure group exists
        if not self._groupname_exists(groupname, _groups=existing_groups):
            raise LookupError(f"Group '{groupname}' does not exist")

        # Ensure new groupname does not exist
        if self._groupname_exists(new_groupname, _groups=existing_groups):
            raise ValueError(f"Group '{new_groupname}' already exists")

        # Rename the group
        group_dn = f"cn={groupname},{self.groups_dn}"
        new_group_rdn = f"cn={new_groupname}"

        #with_scratchs = ih.check_if_custom('create_scratch_folders')
        #if with_scratchs:
        #    create_scratch_folders(...)
        #    os.symlink(groupname, new_groupname)
        self.conn.rename_s(group_dn, new_group_rdn, self.groups_dn)

    def group_addusers(self, groupname, usernames, **kwargs):
        """Add users to a group"""

        # Ensure group exists
        existing_group = self.group_show(groupname)
        if all(u in existing_group.get("member", []) for u in usernames):
            return

        # Ensure users exist
        existing_usernames = [u["uid"] for u in self.user_list()]
        incorrect_usernames = [u for u in usernames if u not in existing_usernames]
        if len(incorrect_usernames) > 0:
            raise ValueError(f"Users '{', '.join(incorrect_usernames)}' do not exist")

        mod_attrs = []
        for name in usernames:
            mod_attrs.append(
                (
                    ldap.MOD_ADD,
                    "member",
                    f"uid={name},ou=People,{self.base_dn}".encode("utf-8"),
                )
            )

        group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
        self.conn.modify_s(group_dn, mod_attrs)

    def group_delusers(self, groupname, usernames, warn=False, force=False, **kwargs):
        """Remove users from a group"""

        # Ensure group exists
        existing_group = self.group_show(groupname)

        # Ensure users exist
        existing_users = self.user_list()
        existing_usernames = [u["uid"] for u in existing_users]
        incorrect_usernames = [u for u in usernames if u not in existing_usernames]
        if len(incorrect_usernames) > 0 and not force:
            raise LookupError(f"Users '{', '.join(incorrect_usernames)}' do not exist")

        mod_attrs = []
        for user in existing_users:
            if user["uid"] in usernames:
                if user["gidNumber"] == existing_group["gidNumber"]:
                    if warn:
                        p.print_warning(
                            f"You removed user {user['uid']} from its primary group"
                        )
                mod_attrs.append(
                    (
                        ldap.MOD_DELETE,
                        "member",
                        f"uid={user['uid']},ou=People,{self.base_dn}".encode("utf-8"),
                    )
                )

        group_dn = f"cn={groupname},ou=Group,{self.base_dn}"
        self.conn.modify_s(group_dn, mod_attrs)

    @show_output
    def export_(self, output_type='json', **kwargs):
        "Export json function (user and groups)"
        users = self.user_list()
        groups = self.group_list()
        data = {
            "users": users,
            "groups": groups
        }
        return data

    def import_(self, data=None, **kwargs):
        "import json data function (user and groups)"
        if not data:
            p.print_info("Enter the data to import: ")
            raw_data = sys.stdin.read()
            data = json.loads(raw_data)
        users = data.get("users", [])
        groups = data.get("groups", [])

        for group in groups:
            try: 
                self.group_add(groupname=group["cn"], gid=group["gidNumber"])
                p.print_info(f"Group {group['cn']} added")
            except ValueError as e:
                p.print_warning(f"Group '{group['cn']}' already exists: {e}")
            except Exception as e:
                p.print_error(f"Failed adding group {group['cn']}: {e}")

        for user in users:
            try:
                self.user_add(
                    username=user["uid"],
                    cn=user.get("cn"),
                    sn=user.get("sn"),
                    given_name=user.get("givenName"),
                    password=user.get("userPassword"),
                    uid=user.get("uidNumber"),
                    gid=user.get("gidNumber"),
                    mail=user.get("mail"),
                    phone=user.get("telephoneNumber"),
                    shell=user.get("loginShell"),
                    groups=user.get("memberOf"),
                    home=user.get("homeDirectory"),
                    expire=user.get("shadowExpire"),
                )
                p.print_info(f"User {user['uid']} added")
            except ValueError as e:
                p.print_warning(f"User '{user['uid']}' already exists: {e}")

    def erase_(self, **kwargs):
        """Erase all users and groups"""
        users = self.user_list()
        for user in users:
            self.user_delete(user["uid"])
        groups = self.group_list()
        for group in groups:
            self.group_delete(group["cn"])
