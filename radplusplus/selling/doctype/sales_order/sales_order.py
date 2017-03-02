#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
import json
import frappe.utils
from frappe.utils import cstr, flt, getdate, comma_and, cint
from frappe import _
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.stock_balance import update_bin_qty, get_reserved_qty
from frappe.desk.notifications import clear_doctype_notifications
from erpnext.controllers.recurring_document import month_map, get_next_date
from frappe.desk.reportview import get_match_cond
from frappe.model.db_query import DatabaseQuery

from erpnext.controllers.selling_controller import SellingController

@frappe.whitelist()
def make_material_request(source_name, target_doc=None):
	def postprocess(source, doc):
		doc.material_request_type = "Manufacture" #2016-11-01 - JDLP

	def update_item(source, target, source_parent):
		target.project = source_parent.project
		target.schedule_date = source_parent.delivery_date #2016-11-01 - JDLP
		target.sales_order = None

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
				"batch_no": "batch_no" # 2016-11-07 - JDLP
			},
			"condition": lambda doc: not frappe.db.exists('Product Bundle', doc.item_code),
			"postprocess": update_item
		}
	}, target_doc, postprocess)

	return doc