#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.utils
import frappe.async
import frappe.sessions
import frappe.utils.file_manager
import frappe.desk.form.run_method


@frappe.whitelist()
def make_mapped_doc(method, source_name, selected_children=None):
	for hook in frappe.get_hooks("override_whitelisted_methods", {}).get(method, []):
		# override using the first hook
		method = hook

	return frappe.model.mapper.make_mapped_doc(method, source_name, selected_children)
