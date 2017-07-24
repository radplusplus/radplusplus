#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt
from frappe.desk.form.linked_with import get_linked_doctypes, get_linked_docs
import erpnext
import radplusplus
import myrador

########################## Section Rad++ ##########################
print_debug = True
			
@frappe.whitelist()
def reasign_batch(item_code, batch, stock_entry):
	doc_batch = frappe.get_doc("Batch",batch)
	
	linked_doctypes = get_linked_doctypes("Batch")
	if print_debug: frappe.errprint("linked_doctypes : " + cstr(linked_doctypes))
	
	linked_doc = get_linked_docs("Batch",batch,	linked_doctypes)
	
	if linked_doc:
		if print_debug: frappe.errprint("linked_doc : " + cstr(linked_doc))
		for key, value in linked_doc.items():
			if print_debug: frappe.errprint("key : " + cstr(key))
			if print_debug: frappe.errprint("value : " + cstr(value))
			if key != "Stock Entry":
				frappe.throw(_("Le lot {0} est lié au document {1}. Veuillez supprimer tous les liens avec le lot {0} avant de continuer").format(batch,cstr(value)))
			for link in value:
				stock_entry_split = stock_entry.split('-')
				if not stock_entry_split[1] in link.name:
					if print_debug: frappe.errprint("stock_entry : " + stock_entry)
					if print_debug: frappe.errprint("link.name : " + link.name)
					frappe.throw(_("Le lot {0} est lié au document {1}. Veuillez supprimer tous les liens avec le lot {0} avant de continuer").format(batch,link.name))
				for stock_entry_detail_name in frappe.get_all("Stock Entry Detail", {"batch_no":batch,"parent":link.name}, "name"):
					frappe.db.set_value("Stock Entry Detail", stock_entry_detail_name, "batch_no","")
		frappe.db.set_value("Batch", batch, "item",item_code)
	
	


	
