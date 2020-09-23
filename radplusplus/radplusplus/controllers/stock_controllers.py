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
import json

########################## Section Rad++ ##########################
print_debug = False

@frappe.whitelist()
def reasign_batch(item_code, batch, stock_entry):
	doc_batch = frappe.get_doc("Batch",batch)
	
	if "Nouveau" in stock_entry: 
		frappe.throw("l'entrée de marchandise doit être enregistrée avant de pouvoir utiliser cette fonction.")
		return
	
	linked_doctypes = get_linked_doctypes("Batch")
	if print_debug: frappe.errprint("linked_doctypes : " + cstr(linked_doctypes))
	if print_debug: frappe.errprint("stock_entry : " + cstr(stock_entry))
	
	linked_doc = get_linked_docs("Batch",batch,	linked_doctypes)
	
	if linked_doc:
		if print_debug: frappe.errprint("linked_doc : " + cstr(linked_doc))
		for key, value in linked_doc.items():
			if print_debug: frappe.errprint("key : " + cstr(key))
			if print_debug: frappe.errprint("value : " + cstr(value))
			if key != "Stock Entry" and key != "Purchase Receipt":
				frappe.throw(_("Le lot {0} est lié au document {1}. Veuillez supprimer tous les liens avec le lot {0} avant de continuer").format(batch,cstr(value)))
			if key == "Stock Entry": 
				for link in value:
					stock_entry_split = stock_entry.split('-')
					if not stock_entry_split[1] in link.name:
						if print_debug: frappe.errprint("stock_entry : " + stock_entry)
						if print_debug: frappe.errprint("link.name : " + link.name)
						frappe.throw(_("Le lot {0} est lié au document {1}. Veuillez supprimer tous les liens avec le lot {0} avant de continuer").format(batch,link.name))
					for stock_entry_detail_name in frappe.get_all("Stock Entry Detail", {"batch_no":batch,"parent":link.name}, "name"):
						frappe.db.set_value("Stock Entry Detail", stock_entry_detail_name, "batch_no","")
			if key == "Purchase Receipt": 
				for link in value:
					stock_entry_split = stock_entry.split('-')
					if not stock_entry_split[1] in link.name:
						if print_debug: frappe.errprint("stock_entry : " + stock_entry)
						if print_debug: frappe.errprint("link.name : " + link.name)
						frappe.throw(_("Le lot {0} est lié au document {1}. Veuillez supprimer tous les liens avec le lot {0} avant de continuer").format(batch,link.name))
					for doc_detail_name in frappe.get_all("Purchase Receipt Item", {"batch_no":batch,"parent":link.name}, "name"):
						frappe.db.set_value("Purchase Receipt Item", doc_detail_name, "batch_no","")
	
	frappe.db.set_value("Batch", batch, "item",item_code)
	
@frappe.whitelist()
def get_item_details_translated(args):

	from erpnext.stock.get_item_details import get_item_details
	out = get_item_details(args)
	
	args = process_args(args)
	
	lang = "fr" 
	
	if args.get("customer"):
		if print_debug: frappe.logger().debug(" if args.customer : " + args.customer)
		if frappe.db.get_value("Customer", args.customer, "language"):
			if print_debug: frappe.logger().debug(" if Customer ")
			lang = frappe.db.get_value("Customer", args.customer, "language")
			
		if frappe.db.get_value("Lead", args.customer, "language"):
			if print_debug: frappe.logger().debug(" if Lead ")
			lang = frappe.db.get_value("Lead", args.customer, "language")
	
	if args.get("supplier"):
		lang = frappe.db.get_value("Supplier", args.supplier, "language")
	
	out.update({
			"description": frappe.db.get_value("Item Language", {"parent":args.item_code,"language":lang}, "description") or frappe.db.get_value("Item", args.item_code, "description")
		})

	if print_debug: frappe.logger().debug(out)
	
	return out
	
def process_args(args):
	if isinstance(args, basestring):
		args = json.loads(args)

	args = frappe._dict(args)

	return args
	
	


	
