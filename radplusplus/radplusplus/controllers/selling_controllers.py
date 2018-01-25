#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt, nowdate
from frappe.desk.form.linked_with import get_linked_doctypes, get_linked_docs
import erpnext
import radplusplus
import myrador
from frappe.model.mapper import get_mapped_doc

########################## Section Rad++ ##########################
print_debug = True
			
@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
					
	def set_missing_values(source, target):
		if source.po_no:
			if target.po_no:
				target_po_no = target.po_no.split(", ")
				target_po_no.append(source.po_no)
				target.po_no = ", ".join(list(set(target_po_no))) if len(target_po_no) > 1 else target_po_no[0]
			else:
				target.po_no = source.po_no
				
		delete_list = []
		for d in target.get('items'):
			if d.qty <= 0 :
				delete_list.append(d)
				
		# delete from doclist
		if delete_list:
			delivery_details = self.get('items')
			self.set('items', [])
			for d in delivery_details:
				if d not in delete_list:
					self.append('items', d)
					
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
			
		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
		
		if print_debug: frappe.logger().debug("target.amount = " + cstr(target.amount))		
				
		if frappe.db.exists("Production Order", {"sales_order_item" : source.name}):
			production_order = frappe.get_doc("Production Order", {"sales_order_item" : source.name})
			
			if print_debug: frappe.logger().debug("production_order = " + cstr(production_order))		
			if production_order:
				target.batch_no = production_order.batch_no
				if print_debug: frappe.logger().debug("production_order = " + cstr(production_order))	
				target.nombre_de_boite = frappe.db.get_value("Batch", production_order.batch_no, "nombre_de_boite")
				target.nbr_palette = frappe.db.get_value("Batch", production_order.batch_no, "nbr_palette")
				
				from radplusplus.radplusplus.doctype.batch_stock_reconciliation.batch_stock_reconciliation import get_item_warehouse_batch_actual_qty
				
				target.qty = get_item_warehouse_batch_actual_qty(source.item_code, source.warehouse, target.batch_no, nowdate(), posting_time=frappe.utils.nowtime())
		else:
			target.qty = flt(source.qty) - flt(source.delivered_qty)
		
	
	if print_debug: frappe.logger().debug("target.amount = " + cstr(target.amount))
			
	target_doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Delivery Note",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Order Item": {
			"doctype": "Delivery Note Item",
			"field_map": {
				"rate": "rate",
				"name": "so_detail",
				"parent": "against_sales_order",
			},
			"postprocess": update_item,
			"condition": lambda doc: abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		},
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return target_doc
		
	
	


	
