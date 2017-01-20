# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import get_match_cond
from frappe.model.db_query import DatabaseQuery


# 2016-12-17 - RM
# Retourne la description de l'item selon la langue passé en paramètre.
@frappe.whitelist()
def item_description_query(doctype, docname):
	# args = {'doctype': doctype,
			# 'docname': docname
	# }
	frappe.errprint("doctype : " + doctype)
	frappe.errprint("docname : " + docname)
	
	#child = frappe.get_doc(doctype, docname)
	#parent = frappe.get_doc(child.parenttype, child.parent)
	
	#description = frappe.db.get_value("Item Language", {"item_code":child.item_code, "language":parent.language}, "description")
	
	if description:
		return description
	else:
		description = frappe.db.get_value("Item", {"item_code":child.item_code}, "description")
		return description
		
	