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
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.party import set_taxes

########################## Section Rad++ #########################
print_debug = True
			
@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
					
	def set_missing_values(source, target):
					
		delete_list = []
		for d in target.get('items'):
			if d.qty <= 0 :
				delete_list.append(d)
				
		# delete from doclist
		if delete_list:
			delivery_details = target.get('items')
			target.set('items', [])
			for d in delivery_details:
				if d not in delete_list:
					target.append('items', d)
					
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
			
		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
		
		if print_debug: frappe.logger().debug("target.amount = " + cstr(target.amount))		
						
		if frappe.db.exists("Work Order", {"sales_order_item" : source.name}):
			work_order = frappe.get_doc("Work Order", {"sales_order_item" : source.name})
			
			if print_debug: frappe.logger().debug("work_order = " + cstr(work_order))		
			if work_order:
				target.batch_no = work_order.batch_no
				if print_debug: frappe.logger().debug("work_order = " + cstr(work_order))	
				target.nombre_de_boite = frappe.db.get_value("Batch", work_order.batch_no, "nombre_de_boite")
				target.nbr_palette = frappe.db.get_value("Batch", work_order.batch_no, "nbr_palette")
				
				from radplusplus.radplusplus.doctype.batch_stock_reconciliation.batch_stock_reconciliation import get_item_warehouse_batch_actual_qty
				
				target.qty = get_item_warehouse_batch_actual_qty(source.item_code, source.warehouse, target.batch_no, nowdate(), posting_time=frappe.utils.nowtime())
		else:
			target.qty = flt(source.qty) - flt(source.delivered_qty)
		
	
	if print_debug: frappe.logger().debug("*** make_delivery_note ***")
			
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
	
@frappe.whitelist()
def get_lead_details(lead, posting_date=None, company=None):
	if not lead: return {}
	
	# 2017-03-10 - renmai - copié la fonction get_lead_details au lieu de l'appel du module erpnext.
	# Partait en boucle.
	from erpnext.accounts.party import set_address_details
	out = frappe._dict()

	lead_doc = frappe.get_doc("Lead", lead)
	lead = lead_doc

	out.update({
		"territory": lead.territory,
		"customer_name": lead.company_name or lead.lead_name,
		"contact_display": lead.lead_name,
		"contact_email": lead.email_id,
		"contact_mobile": lead.mobile_no,
		"contact_phone": lead.phone,
	})

	set_address_details(out, lead, "Lead")

	taxes_and_charges = set_taxes(None, 'Lead', posting_date, company,
		billing_address=out.get('customer_address'), shipping_address=out.get('shipping_address_name'))
	if taxes_and_charges:
		out['taxes_and_charges'] = taxes_and_charges

	# 2017-01-18 - RM - Ajout de balise pour mettre le lead name en gras.
	out.update({"contact_display": "<b>" + lead.lead_name + "</b>"})

	# 2017-01-18 - RM - permet d afficher le telephone et le courriel dans contact_display. Pour les rapports Jasper.
	if lead.phone:
		out['contact_display'] = out['contact_display'] + "<br>" + lead.phone
	if lead.email_id:
		out['contact_display'] = out['contact_display'] + "<br>" + lead.email_id

	return out
		
	
	


	
