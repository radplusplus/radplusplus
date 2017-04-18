#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt
import erpnext
import time
import radplusplus
import myrador
import json
from erpnext.stock.doctype.stock_entry.stock_entry import get_additional_costs
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
from erpnext.manufacturing.doctype.production_order.production_order import check_if_scrap_warehouse_mandatory
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate
from frappe.model.mapper import get_mapped_doc

########################## Section Rad++ ##########################
print_debug = True
		

		
def update_status(self, status=None):
	'''Update status of production order if unknown'''
	if not status:
		status = self.get_status(status)

	if status != self.status:
		self.db_set("status", status)

	update_required_items(self)

	return status

def update_required_items(self):
	'''
	update bin reserved_qty_for_production
	called from Stock Entry for production, after submit, cancel
	'''
	if self.docstatus==1 and self.source_warehouse:
		if self.material_transferred_for_manufacturing == self.produced_qty:
			# clear required items table and save document
			clear_required_items(self)
		else:
			# calculate transferred qty based on submitted
			# stock entries
			self.update_transaferred_qty_for_required_items()

			# update in bin
			self.update_reserved_qty_for_production()

def clear_required_items(self):
	'''Remove the required_items table and update the bins'''
	items = [d.item_code for d in self.required_items]
	self.required_items = []

	self.update_child_table('required_items')

	# completed, update reserved qty in bin
	self.update_reserved_qty_for_production(items)
	
def update_reserved_qty_for_production(self, items=None):
	'''update reserved_qty_for_production in bins'''
	if not self.source_warehouse:
		return

	if not items:
		items = [d.item_code for d in self.required_items]

	for item in items:
		# RENMAI - 2017-04-13 - a modifier lorsque les entrepots sources seront associé 
		# aux productions items.
		
		#doc_item = frappe.get_doc("Item",item)
		#if doc_item.variant_of && doc_item.variant_of == "PM":
		#	source_warehouse = self.source_warehouse
		source_warehouse = self.source_warehouse
		stock_bin = get_bin(item, source_warehouse)
		
		'''Update qty reserved for production from Production Item tables
			in open production orders'''
		stock_bin.reserved_qty_for_production = frappe.db.sql('''select sum(required_qty - transferred_qty)
			from `tabProduction Order` pro, `tabProduction Order Item` item
			where
				item.item_code = %s
				and item.parent = pro.name
				and pro.docstatus = 1
				and pro.source_warehouse = %s''', (stock_bin.item_code, stock_bin.warehouse))[0][0]

		stock_bin.set_projected_qty()

		stock_bin.db_set('reserved_qty_for_production', stock_bin.reserved_qty_for_production)
		stock_bin.db_set('projected_qty', stock_bin.projected_qty)

def set_required_items(self):
	'''set required_items for production to keep track of reserved qty'''
	frappe.msgprint(_("set_required_items"))
	if self.source_warehouse:
		item_dict = get_bom_items_as_dict(self.bom_no, self.company, qty=self.qty,
			fetch_exploded = self.use_multi_level_bom)

		for item in item_dict.values():
			self.append('required_items', {'item_code': item.item_code,
				'required_qty': item.qty})

		#print frappe.as_json(self.required_items)

def update_transaferred_qty_for_required_items(self):
	'''update transferred qty from submitted stock entries for that item against
		the production order'''

	for d in self.required_items:
		transferred_qty = frappe.db.sql('''select count(qty)
			from `tabStock Entry` entry, `tabStock Entry Detail` detail
			where
				entry.production_order = %s
				entry.purpose = "Material Transfer for Manufacture"
				and entry.docstatus = 1
				and detail.parent = entry.name
				and detail.item_code = %s''', (self.name, d.item_code))[0][0]

		d.db_set('transferred_qty', transferred_qty, update_modified = False)
		
def calculate_operation_time(self):
	
	for d in self.get("operations"):
		d.time_in_mins = flt(d.minutes_per) * flt(self.qty)

	self.calculate_operating_cost()
	
	return self
	
def set_material_details(self):
	
	for d in self.get("production_order_item"):
		if self.qty:
			d.required_qty = d.quantity_per * self.qty
			
		item = frappe.get_doc("Item",d.item_code)
		if self.customer and item.variant_of == "PM":
			d.warehouse = frappe.db.get_value("Customer", self.customer, "default_warehouse")
		elif item.default_warehouse:
			d.warehouse = item.default_warehouse
		else:
			d.warehouse = self.source_warehouse
	
	return self

@frappe.whitelist()
def stop_unstop(self, status):
	""" Called from client side on Stop/Unstop event"""
	self = frappe.get_doc("Production Order", self)
	status = update_status(status)
	self.update_planned_qty()
	frappe.msgprint(_("Production Order status is {0}").format(status))
	self.notify_update()

@frappe.whitelist()
def on_cancel(self,method):
	frappe.msgprint(_("on_cancel HOOK*"))

@frappe.whitelist()
def set_production_order_materials_and_operations(source_name, target_doc=None):
	
	frappe.logger().debug("mapper :")	
	
	def postprocess(source, doc):
		frappe.logger().debug("postprocess :")	
		doc.calculate_time()
		doc = set_material_details(doc)

	def update_item(source, target, source_parent):
		target.quantity_per = source.qty / source_parent.quantity
	
	def update_operation(source, target, source_parent):
		target.minutes_per = source.time_in_mins / source_parent.quantity

	doc = get_mapped_doc("BOM", source_name, {
		"BOM": {
			"doctype": "Production Order",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"BOM Item": {
			"doctype": "Production Order Item",
			"field_map": {
				"qty": "quantity_per"
			},
			"postprocess": update_item
		},
		"BOM Operation": {
			"doctype": "Production Order Operation",
			"field_map": {
				"time_in_mins": "minutes_per"
			},
			"postprocess": update_operation
		}
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def update_details(self):
	
	doc = json.loads(self)
	doc = frappe.get_doc(doc)
	if doc.operations:
		doc = calculate_operation_time(doc)
	if doc.production_order_item:
		doc = set_material_details(doc)
	
	return doc
	
@frappe.whitelist()
def get_default_warehouse():
	wip_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_wip_warehouse")
	fg_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_fg_warehouse")
	source_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_raw_material_warehouse")
	return {"wip_warehouse": wip_warehouse, "fg_warehouse": fg_warehouse,"source_warehouse":source_warehouse}
	
@frappe.whitelist()
def make_stock_entry(production_order_id, purpose, qty=None):
	
	production_order = frappe.get_doc("Production Order", production_order_id)
	
	if print_debug: frappe.errprint(production_order)
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.production_order = production_order_id
	stock_entry.company = production_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = production_order.bom_no
	stock_entry.use_multi_level_bom = production_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(production_order.qty) - flt(production_order.produced_qty))

	if purpose=="Material Transfer for Manufacture":
		if production_order.source_warehouse:
			stock_entry.from_warehouse = production_order.source_warehouse
		stock_entry.to_warehouse = production_order.wip_warehouse
		stock_entry.project = production_order.project
	else:
		stock_entry.from_warehouse = production_order.wip_warehouse
		stock_entry.to_warehouse = production_order.fg_warehouse
		additional_costs = get_additional_costs(production_order, fg_qty=stock_entry.fg_completed_qty)
		stock_entry.project = frappe.db.get_value("Stock Entry",{"production_order": production_order_id,"purpose": "Material Transfer for Manufacture"}, "project")
		stock_entry.set("additional_costs", additional_costs)

	stock_entry.get_items()
	
	for d in stock_entry.items:
	
		item = frappe.get_doc("Item",d.item_code)
		if production_order.customer and item.variant_of == "PM":
			d.s_warehouse = frappe.db.get_value("Customer", production_order.customer, "default_warehouse")
		elif item.default_warehouse:
			d.s_warehouse = item.default_warehouse
		else:
			d.s_warehouse = production_order.source_warehouse
	
	return stock_entry.as_dict()



	
