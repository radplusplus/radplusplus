# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.db_query import DatabaseQuery

class ItemLanguage(Document):
	pass

print_debug = True

# 2016-12-17 - RM
# Retourne la description de l'item selon la langue passé en paramètre.
@frappe.whitelist()
def item_description_query(doctype, docname, item_code):
	# args = {'doctype': doctype,
			# 'docname': docname
	# }
	frappe.errprint("doctype : " + doctype)
	frappe.errprint("docname : " + docname)
	
	child = frappe.get_doc(doctype, docname)
	
	frappe.errprint("child.parenttype : " + child.parenttype)
	frappe.errprint("child.parent : " + child.parent)
	
	parent = frappe.get_doc(child.parenttype, child.parent)
	
	frappe.errprint("child.item_code : " + child.item_code)
	frappe.errprint("item_code : " + item_code)
	frappe.errprint("parent.language : " + parent.language)
	
	description = frappe.db.get_value("Item Language", {"parent":item_code, "language":parent.language}, "description")
	
	frappe.errprint("description : " + description)
	
	if description:
		return description
	else:
		description = frappe.db.get_value("Item", {"item_code":child.item_code}, "description")
		return description

			

	