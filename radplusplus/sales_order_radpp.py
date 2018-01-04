#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr
from frappe import _
from frappe.model.mapper import get_mapped_doc

from erpnext.controllers.selling_controller import SellingController

@frappe.whitelist()
def make_mapped_doc(method, source_name, selected_children=None):
	for hook in frappe.get_hooks("override_whitelisted_methods", {}).get(method, []):
		# override using the first hook
		method = hook

	return frappe.model.mapper.make_mapped_doc(method, source_name, selected_children)
	
@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.material_request_type = "Purchase" #2016-11-01 - JDLP

	def update_item(source, target, source_parent):
		target.project = source_parent.project
		target.schedule_date = source_parent.delivery_date #2016-11-01 - JDLP

	doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Material Request"
		},
		"Packed Item": {
			"doctype": "Material Request Item",
			"field_map": {
				"parent": "sales_order",
				"stock_uom": "uom"
			},
			"postprocess": update_item
		},
		"Sales Order Item": {
			"doctype": "Material Request Item",
			"field_map": {
				"parent": "sales_order",
				"stock_uom": "uom",
				"name": "sales_order_item" # 2017-06-26 - RENMAI
			},
			"condition": lambda doc: not frappe.db.exists('Product Bundle', doc.item_code),
			"postprocess": update_item
		}
	}, target_doc, postprocess)

	return doc