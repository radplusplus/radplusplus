#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, RAD plus plus inc. and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint

print_debug = False

def boot_session(bootinfo):
	"""boot session - add custom translate"""
	
	lang = frappe.db.get_value("User", frappe.session.user, "language") 
	
	if print_debug: frappe.logger().debug("lang : " + lang)
	
	from radplusplus.radplusplus.controllers.configurator import update_user_translations
	update_user_translations(lang)