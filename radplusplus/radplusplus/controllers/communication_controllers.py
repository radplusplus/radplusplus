#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe.utils.jinja import validate_template
from six import string_types
from frappe import _
from frappe.utils import cstr, flt

########################## Section Rad++ ##########################
print_debug = True

@frappe.whitelist()
def get_email_template(template_name, doc, lang=None):
	'''Returns the processed HTML of a standard reply with the given doc '''
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	email_template = frappe.get_doc("Email Template", template_name)
	
	if lang:
		response = '{% set print_language = "' + lang + '" %}' + email_template.response
	else:
		response = '{% set print_language = language %}' + email_template.response
	
	if print_debug: frappe.logger().debug("response : " + response )
	
	return {"subject" : frappe.render_template(_(email_template.subject,lang), doc),
			"message" : frappe.render_template(response, doc)}
	