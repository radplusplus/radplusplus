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
import json
from erpnext.stock.doctype.stock_entry.stock_entry import get_additional_costs
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
from erpnext.manufacturing.doctype.production_order.production_order import check_if_scrap_warehouse_mandatory
from frappe.utils import flt, get_datetime, getdate, date_diff, cint, nowdate
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.utils import get_incoming_rate

########################## Section Rad++ ##########################
print_debug = False
		
def update_status(self, status=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_status---")
	'''Update status of production order if unknown'''
	if not status:
		status = self.get_status(status)
		
	if status != self.status:	
		self.db_set("status", status)
	
	update_required_items(self)
	
	if status == "Completed":
		self.set_actual_dates()
		self.save()

	return status

def update_required_items(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_required_items---")
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
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.clear_required_items---")
	'''Remove the required_items table and update the bins'''
	items = [d.item_code for d in self.required_items]
	self.required_items = []

	self.update_child_table('required_items')

	# completed, update reserved qty in bin
	self.update_reserved_qty_for_production(items)
	
def update_reserved_qty_for_production(self, items=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_reserved_qty_for_production---")
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

# def set_required_items(self):
	# '''set required_items for production to keep track of reserved qty'''
	# frappe.msgprint(_("set_required_items"))
	# if self.source_warehouse:
		# item_dict = get_bom_items_as_dict(self.bom_no, self.company, qty=self.qty,
			# fetch_exploded = self.use_multi_level_bom)

		# for item in item_dict.values():
			# self.append('required_items', {'item_code': item.item_code,
				# 'required_qty': item.qty})

		#print frappe.as_json(self.required_items)

def update_transaferred_qty_for_required_items(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_transaferred_qty_for_required_items---")
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
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.calculate_operation_time---")
	for d in self.get("operations"):
		d.time_in_mins = flt(d.minutes_per) * flt(self.qty)

	self.calculate_operating_cost()
	
	return self
	
def set_material_details(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.set_material_details---")
	
	for d in self.get("required_items"):
		if self.qty:
			d.required_qty = flt(d.quantity_per) * flt(self.qty)
		item = frappe.get_doc("Item",d.item_code)
		if self.sales_order_item and item.variant_of == "PM":
			if frappe.db.get_value("Sales Order Item", self.sales_order_item, "description_sous_traitance"):
				d.warehouse = frappe.db.get_value("Customer", self.customer, "default_warehouse")
			d.warehouse = item.default_warehouse
		elif item.default_warehouse:
			d.warehouse = item.default_warehouse
		else:
			d.warehouse = self.source_warehouse
	
	return self

@frappe.whitelist()
def update_transferred_qty(self, status):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_transferred_qty---")
	""" Called to refresh transferred_qty based on stock_entry"""
	self = frappe.get_doc("Production Order", self)
	status = update_status(self,status)
	self.update_planned_qty()
	frappe.msgprint(_("Production Order status is {0}").format(status))
	self.notify_update()
	
@frappe.whitelist()
def update_reserved_qty(production_order):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_reserved_qty---")
	if print_debug: frappe.logger().debug("production_order : " + production_order)
	transferred_qty = frappe.db.sql('''select sum(qty)
		from `tabStock Entry` entry, `tabStock Entry Detail` detail
		where
			entry.production_order = %s
			and entry.purpose = "Material Transfer for Manufacture"
			and entry.docstatus = 1
			and detail.parent = entry.name''', (production_order))[0][0]
			
	if transferred_qty:		
		if print_debug: frappe.logger().debug("return : " + cstr(transferred_qty))
		return transferred_qty
	else:
		if print_debug: frappe.logger().debug("return : 0")
		return 0

# @frappe.whitelist()
# def on_cancel(self,method):
	# pass
	
@frappe.whitelist()
def set_production_order_materials_and_operations(source_name, target_doc=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.set_production_order_materials_and_operations---")
	
	frappe.logger().debug("mapper :")	
	
	def postprocess(source, doc):
		if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.postprocess---")
		frappe.logger().debug("postprocess :")	
		doc.calculate_time()
		doc = set_material_details(doc)

	def update_item(source, target, source_parent):
		if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_item---")
		target.quantity_per = source.qty / source_parent.quantity
		target.warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_raw_material_warehouse")
	
	def update_operation(source, target, source_parent):
		if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_operation---")
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
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_details---")
	
	doc = json.loads(self)
	doc = frappe.get_doc(doc)
	if doc.operations:
		doc = calculate_operation_time(doc)
	if doc.required_items:
		doc = set_material_details(doc)
	
	return doc

@frappe.whitelist()
def update_transferred_qty_for_production_order_item(production_order):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.update_transferred_qty_for_production_order_item---")
	'''update transferred qty from submitted stock entries for that item against the production order'''
	
	for poi in production_order.required_items:
		transferred_qty = frappe.db.sql('''select sum(qty)
		from `tabStock Entry` entry, `tabStock Entry Detail` detail
			where
			entry.production_order = %s
				and entry.purpose = "Material Transfer for Manufacture"
				and entry.docstatus = 1
				and detail.parent = entry.name
				and detail.item_code = %s''', (production_order.name, poi.item_code))[0][0]

		poi.db_set('transferred_qty', transferred_qty, update_modified = False)
		
@frappe.whitelist()
def get_default_warehouse():
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.get_default_warehouse---")
	wip_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_wip_warehouse")
	fg_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_fg_warehouse")
	source_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_raw_material_warehouse")
	return {"wip_warehouse": wip_warehouse, "fg_warehouse": fg_warehouse,"source_warehouse":source_warehouse}

def add_to_stock_entry_detail(self, item_dict, bom_no=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.add_to_stock_entry_detail---")
	expense_account, cost_center = frappe.db.get_values("Company", self.company, \
		["default_expense_account", "cost_center"])[0]

	for d in item_dict:
		se_child = self.append('items')
		se_child.s_warehouse = item_dict[d].get("from_warehouse")
		se_child.t_warehouse = item_dict[d].get("to_warehouse")
		se_child.item_code = cstr(d)
		se_child.item_name = item_dict[d]["item_name"]
		se_child.description = item_dict[d]["description"]
		se_child.uom = item_dict[d]["stock_uom"]
		se_child.stock_uom = item_dict[d]["stock_uom"]
		se_child.qty = flt(item_dict[d]["qty"])
		se_child.expense_account = item_dict[d]["expense_account"] or expense_account
		se_child.cost_center = item_dict[d]["cost_center"] or cost_center
		se_child.batch_no = item_dict[d].get("batch_no")
		se_child.basic_rate = item_dict[d].get("valuation_rate")			

		if se_child.s_warehouse==None:
			se_child.s_warehouse = self.from_warehouse
		if se_child.t_warehouse==None:
			se_child.t_warehouse = self.to_warehouse

		# in stock uom
		se_child.transfer_qty = flt(item_dict[d]["qty"])
		se_child.conversion_factor = 1.00

		# to be assigned for finished item
		se_child.bom_no = bom_no
			
def get_transfered_raw_materials(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.get_transfered_raw_materials---")
	
	transferred_materials = frappe.db.sql("""
		select
			item_name, item_code, sum(qty) as qty, sed.t_warehouse as warehouse,
			description, stock_uom, expense_account, cost_center, sed.batch_no
		from `tabStock Entry` se,`tabStock Entry Detail` sed
		where
			se.name = sed.parent and se.docstatus=1 and se.purpose='Material Transfer for Manufacture'
			and se.production_order= %s and ifnull(sed.t_warehouse, '') != ''
		group by sed.item_code, sed.t_warehouse, sed.batch_no
	""", self.production_order, as_dict=1)

	materials_already_backflushed = frappe.db.sql("""
		select
			item_code, sed.s_warehouse as warehouse, sum(qty) as qty, sed.batch_no
		from
			`tabStock Entry` se, `tabStock Entry Detail` sed
		where
			se.name = sed.parent and se.docstatus=1 and se.purpose='Manufacture'
			and se.production_order= %s and ifnull(sed.s_warehouse, '') != ''
		group by sed.item_code, sed.s_warehouse, sed.batch_no
	""", self.production_order, as_dict=1)

	backflushed_materials= {}
	for d in materials_already_backflushed:
		#backflushed_materials.setdefault(d.item_code,[]).append({d.warehouse: d.qty, "batch_no":d.batch_no})
		if d.batch_no:				
			backflushed_materials.setdefault(d.item_code,{})
			backflushed_materials[d.item_code].setdefault(d.batch_no,[]).append({d.warehouse: d.qty})
		else:
			backflushed_materials.setdefault(d.item_code,[]).append({d.warehouse: d.qty})

	po_qty = frappe.db.sql("""select qty, produced_qty, material_transferred_for_manufacturing from
		`tabProduction Order` where name=%s""", self.production_order, as_dict=1)[0]
	manufacturing_qty = flt(po_qty.qty)
	produced_qty = flt(po_qty.produced_qty)
	trans_qty = flt(po_qty.material_transferred_for_manufacturing)

	for item in transferred_materials:
		qty= item.qty

		# if trans_qty and manufacturing_qty > (produced_qty + flt(self.fg_completed_qty)):
			# qty = (qty/trans_qty) * flt(self.fg_completed_qty)

		# elif backflushed_materials.get(item.item_code):
		
		
		if item.batch_no:
			if backflushed_materials.get(item.item_code):
				if backflushed_materials[item.item_code].get(item.batch_no):
					for d in backflushed_materials[item.item_code].get(item.batch_no):
						if d.get(item.warehouse):
							qty-= d.get(item.warehouse)
		else:
			if backflushed_materials.get(item.item_code):
				for d in backflushed_materials.get(item.item_code):
					if d.get(item.warehouse):
						qty-= d.get(item.warehouse)

		if qty > 0:
			add_to_stock_entry_detail(self,{
				item.item_code: {
					"from_warehouse": item.warehouse,
					"to_warehouse": "",
					"qty": qty,
					"item_name": item.item_name,
					"description": item.description,
					"stock_uom": item.stock_uom,
					"expense_account": item.expense_account,
					"cost_center": item.buying_cost_center,
					"batch_no": item.batch_no,
					"valuation_rate": 0
				}
			})
				
def load_items_from_bom(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.load_items_from_bom---")
	if self.production_order:
		item_code = self.pro_doc.production_item
		to_warehouse = self.pro_doc.fg_warehouse
	else:
		item_code = frappe.db.get_value("BOM", self.bom_no, "item")
		to_warehouse = self.to_warehouse

	item = frappe.db.get_value("Item", item_code, ["item_name",
		"description", "stock_uom", "expense_account", "buying_cost_center", "name", "default_warehouse"], as_dict=1)
	
	valuation_rate = frappe.db.get_value("Sales Order Item", self.pro_doc.sales_order_item, ["rate"])

	if not self.production_order and not to_warehouse:
		# in case of BOM
		to_warehouse = item.default_warehouse
			
	add_to_stock_entry_detail(self,{
		item.name: {
			"to_warehouse": to_warehouse,
			"from_warehouse": "",
			"qty": self.fg_completed_qty,
			"item_name": item.item_name,
			"description": item.description,
			"stock_uom": item.stock_uom,
			"expense_account": item.expense_account,
			"cost_center": item.buying_cost_center,
			"batch_no": self.pro_doc.batch_no,
			"valuation_rate": valuation_rate
		}
	}, bom_no = self.bom_no)
		
def get_items(self):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.get_items---")
	self.set('items', [])
	self.validate_production_order()

	if not self.posting_date or not self.posting_time:
		frappe.throw(_("Posting date and posting time is mandatory"))

	self.set_production_order_details()

	if self.bom_no:
		if self.purpose in ["Material Issue", "Material Transfer", "Manufacture", "Repack",
				"Subcontract", "Material Transfer for Manufacture"]:
			if self.production_order and self.purpose == "Material Transfer for Manufacture":
				item_dict = self.get_pending_raw_materials()
				if self.to_warehouse and self.pro_doc:
					for item in item_dict.values():
						item["to_warehouse"] = self.pro_doc.wip_warehouse
				self.add_to_stock_entry_detail(item_dict)

			elif self.production_order and self.purpose == "Manufacture" and \
				frappe.db.get_single_value("Manufacturing Settings", "backflush_raw_materials_based_on")== "Material Transferred for Manufacture":
				get_transfered_raw_materials(self)

			else:
				if not self.fg_completed_qty:
					frappe.throw(_("Manufacturing Quantity is mandatory"))

				item_dict = self.get_bom_raw_materials(self.fg_completed_qty)
				for item in item_dict.values():
					if self.pro_doc:
						item["from_warehouse"] = self.pro_doc.wip_warehouse

					item["to_warehouse"] = self.to_warehouse if self.purpose=="Subcontract" else ""
				
				self.add_to_stock_entry_detail(item_dict)

				scrap_item_dict = self.get_bom_scrap_material(self.fg_completed_qty)
				for item in scrap_item_dict.values():
					if self.pro_doc and self.pro_doc.scrap_warehouse:
						item["to_warehouse"] = self.pro_doc.scrap_warehouse
				self.add_to_stock_entry_detail(scrap_item_dict, bom_no=self.bom_no)
				
		# fetch the serial_no of the first stock entry for the second stock entry
		if self.production_order and self.purpose == "Manufacture":
			self.set_serial_nos(self.production_order)

		# add finished goods item
		if self.purpose in ("Manufacture", "Repack"):
			load_items_from_bom(self)

	self.set_actual_qty()
	calculate_rate_and_amount(self)

def set_basic_rate(self, force=False, update_finished_item_rate=True):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.set_basic_rate---")
	"""get stock and incoming rate on posting date"""
	raw_material_cost = 0.0
	scrap_material_cost = 0.0
	fg_basic_rate = 0.0

	for d in self.get('items'):
		if d.t_warehouse: fg_basic_rate = flt(d.basic_rate)
		args = frappe._dict({
			"item_code": d.item_code,
			"warehouse": d.s_warehouse or d.t_warehouse,
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			"qty": d.s_warehouse and -1*flt(d.transfer_qty) or flt(d.transfer_qty),
			"serial_no": d.serial_no,
		})

		# get basic rate
		if not d.bom_no:
			if not flt(d.basic_rate) or d.s_warehouse or force:
				basic_rate = flt(get_incoming_rate(args), self.precision("basic_rate", d))
				if basic_rate > 0:
					d.basic_rate = basic_rate

			d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))
			if not d.t_warehouse:
				raw_material_cost += flt(d.basic_amount)

		# get scrap items basic rate
		if d.bom_no:
			if not flt(d.basic_rate) and getattr(self, "pro_doc", frappe._dict()).scrap_warehouse == d.t_warehouse:
				basic_rate = flt(get_incoming_rate(args), self.precision("basic_rate", d))
				if basic_rate > 0:
					d.basic_rate = basic_rate
				d.basic_amount = flt(flt(d.transfer_qty) * flt(d.basic_rate), d.precision("basic_amount"))

			if getattr(self, "pro_doc", frappe._dict()).scrap_warehouse == d.t_warehouse:

				scrap_material_cost += flt(d.basic_amount)

	number_of_fg_items = len([t.t_warehouse for t in self.get("items") if t.t_warehouse])
	if (fg_basic_rate == 0.0 and number_of_fg_items == 1) or update_finished_item_rate:
		set_basic_rate_for_finished_goods(self, raw_material_cost, scrap_material_cost)

def set_basic_rate_for_finished_goods(self, raw_material_cost, scrap_material_cost):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.set_basic_rate_for_finished_goods---")
	if self.purpose in ["Manufacture", "Repack"]:
		for d in self.get("items"):
			if d.transfer_qty and (d.bom_no or d.t_warehouse) and (getattr(self, "pro_doc", frappe._dict()).scrap_warehouse != d.t_warehouse):
				if getattr(self, "pro_doc", frappe._dict()).sales_order:
					valuation_rate = frappe.db.get_value("Sales Order Item", self.pro_doc.sales_order_item, ["rate"])
					d.basic_rate = valuation_rate
				else:
					d.basic_rate = flt((raw_material_cost - scrap_material_cost) / flt(d.transfer_qty), d.precision("basic_rate"))
				d.basic_amount = flt((raw_material_cost - scrap_material_cost), d.precision("basic_amount"))

			
def calculate_rate_and_amount(self, force=False, update_finished_item_rate=True):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.calculate_rate_and_amount---")
	set_basic_rate(self, force, update_finished_item_rate)
	self.distribute_additional_costs()
	self.update_valuation_rate()
	self.set_total_incoming_outgoing_value()
	self.set_total_amount()

		
@frappe.whitelist()
def make_stock_entry(production_order_id, purpose, qty=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.make_stock_entry---")
	
	production_order = frappe.get_doc("Production Order", production_order_id)
	
	if production_order.skip_transfer and purpose == "Material Transfer for Manufacture":
		return
	
	if not frappe.db.get_value("Warehouse", production_order.wip_warehouse, "is_group") \
			and not production_order.skip_transfer:
		wip_warehouse = production_order.wip_warehouse
	else:
		wip_warehouse = None
		
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.production_order = production_order_id
	stock_entry.company = production_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = production_order.bom_no
	stock_entry.use_multi_level_bom = production_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(production_order.qty) - flt(production_order.produced_qty))
	

	if purpose=="Material Transfer for Manufacture":
		defaut_raw_warehouse = frappe.db.get_single_value('Manufacturing Settings', 'default_raw_material_warehouse')
		if defaut_raw_warehouse:
			stock_entry.from_warehouse = defaut_raw_warehouse
		stock_entry.to_warehouse = production_order.wip_warehouse
		stock_entry.project = production_order.project	
		if production_order.sales_order:
			doc_sales_order = frappe.get_doc("Sales Order", production_order.sales_order)
			if doc_sales_order.po_no:
				stock_entry.po_no = doc_sales_order.po_no
	else:
		stock_entry.from_warehouse = production_order.wip_warehouse
		stock_entry.to_warehouse = production_order.fg_warehouse
		additional_costs = get_additional_costs(production_order, fg_qty=stock_entry.fg_completed_qty)		
		# stock_entry.project = frappe.db.get_value("Stock Entry",{"production_order": production_order_id,"purpose": "Material Transfer for Manufacture"}, "project") - renmai - 2018-02-20 - V10
		stock_entry.project = production_order.project
		stock_entry.set("additional_costs", additional_costs)

	get_items(stock_entry)
	
	if purpose=="Material Transfer for Manufacture":
		for d in stock_entry.items:
			item = frappe.get_doc("Item",d.item_code)
			if production_order.sales_order_item and item.variant_of == "PM":
				if frappe.db.get_value("Sales Order Item", production_order.sales_order_item, "description_sous_traitance"):
					# d.s_warehouse = frappe.db.get_value("Customer", production_order.customer, "default_warehouse") - renmai - 2018-02-20 - V10
					d.allow_zero_valuation_rate = 1
				# else:
					# d.s_warehouse = item.default_warehouse
			# elif item.default_warehouse:
				# d.s_warehouse = item.default_warehouse
			# else:
				# d.s_warehouse = production_order.source_warehouse
				
	if purpose=="Manufacture" and not production_order.skip_transfer:
		stock_entry_for_reserved_material = frappe.get_value("Stock Entry", filters={"production_order": production_order_id, "purpose":"Material Transfer for Manufacture", "docstatus":1})
		reserved_material = frappe.get_doc("Stock Entry",stock_entry_for_reserved_material)
		for d in stock_entry.items:
			item = frappe.get_doc("Item",d.item_code)
			stock_entry_for_reserved_material_item = frappe.get_value("Stock Entry Detail", filters={"parent": stock_entry_for_reserved_material, "item_code":item.name})
			if stock_entry_for_reserved_material_item:
				reserved_material_detail = frappe.get_doc("Stock Entry Detail",stock_entry_for_reserved_material_item)
				if production_order.customer and item.variant_of == "PM":
					d.allow_zero_valuation_rate = 1
					if reserved_material_detail.qty_per_box:
						d.qty_per_box = reserved_material_detail.qty_per_box
	
	return stock_entry.as_dict()
	
# @frappe.whitelist()
# def copy_sales_order_information_to_production_order(production_order, method):

	# if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.copy_sales_order_information_to_production_order---")
	
	# if production_order.sales_order:
		# production_order.db_set('reference_client', frappe.db.get_value("Sales Order", production_order.sales_order, "po_no"))			
		# production_order.db_set('customer', frappe.db.get_value("Sales Order", production_order.sales_order, "customer"))
		
@frappe.whitelist()		
def set_required_item_wharehouse(production_order, method=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.set_required_item_wharehouse:")
	for d in production_order.required_items:
		item = frappe.get_doc("Item",d.item_code)
		if production_order.sales_order_item and item.variant_of in ["PM","PV","PH","PS"] and frappe.db.get_value("Sales Order Item", production_order.sales_order_item, "description_sous_traitance"):
			d.source_warehouse = frappe.db.get_value("Customer", frappe.db.get_value("Sales Order", production_order.sales_order, "customer"), "default_warehouse")
		elif item.default_warehouse:
			d.source_warehouse = item.default_warehouse
		else:
			d.source_warehouse = production_order.source_warehouse
		
		
@frappe.whitelist()
def make_production_orders(items, sales_order, company, project=None):
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.make_production_orders---")
	''' renmai - Override of ERPNext sales_order.py function.'''
	'''Make Production Orders against the given Sales Order for the given `items`'''
	items = json.loads(items).get('items')
	out = []

	for i in items:
		if not i.get("bom"):
			frappe.throw(_("Please select BOM against item {0}").format(i.get("item_code")))
		if not i.get("pending_qty"):
			frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))
		
		customer=frappe.db.get_value("Sales Order", sales_order, "customer") # renmai - 2018-02-14
		language = "fr"
		if customer: 
			language = frappe.db.get_value("Customer", customer, "language") # renmai - 2019-01-07

		production_order = frappe.get_doc(dict(
			doctype='Production Order',
			production_item=i['item_code'],
			bom_no=i.get('bom'),
			qty=i['pending_qty'],
			company=company,
			sales_order=sales_order,
			sales_order_item=i['sales_order_item'],
			customer=customer, # renmai - 2018-02-14
			language=language, # renmai - 2019-01-07
			reference_client=frappe.db.get_value("Sales Order", sales_order, "po_no"), # renmai - 2018-02-14 - 
			project=project,
			fg_warehouse=i['warehouse'],
			source_warehouse=frappe.db.get_single_value("Manufacturing Settings", "default_raw_material_warehouse")
		)).insert()
		production_order.set_production_order_operations()
		set_required_item_wharehouse(production_order)
		production_order.save()
		out.append(production_order)

	return [p.name for p in out]
		
@frappe.whitelist()	
def get_purchase_order_items(self):
	'''Returns items that already do not have a linked purchase order'''
	
	if print_debug: frappe.logger().debug("---radplusplus.manufacturing_controllers.get_purchase_order_items:")
	
	if print_debug: frappe.logger().debug("self : " + self)
	
	required_items = json.loads(self).get('required_items')
	self = json.loads(self)
	items = []

	for i in required_items:
		if print_debug: frappe.logger().debug("i : ")
		if print_debug: frappe.logger().debug(i)
		if print_debug: frappe.logger().debug("i['required_qty'] : " + cstr(i['required_qty']))
		
		pending_qty= i['required_qty'] - flt(frappe.db.sql('''select sum(qty) from `tabPurchase Order Item`
				where item_code=%s and production_order=%s and production_order_item = %s and docstatus<2''', (i['item_code'], i['parent'], i['name']))[0][0])
		if pending_qty:
			items.append(dict(
				item_code= i['item_code'],
				warehouse = i['source_warehouse'],
				pending_qty = pending_qty,
				production_order_item = i['name']
			))
				
	return items
	
@frappe.whitelist()
def make_purchase_orders(items, production_order, company, project=None):
	'''Make Purchase Orders against the given production Order for the given `items`'''
	items = json.loads(items).get('items')
	out = []
	supplier = ""
	purchase_order = []

	for i in sorted(items, key=lambda item:item['supplier']): 
		if not i.get("supplier"):
			frappe.throw(_("Please select supplier against item {0}").format(i.get("item_code")))
		if not i.get("pending_qty"):
			frappe.throw(_("Please select Qty against item {0}").format(i.get("item_code")))
		
		if supplier != i['supplier']:
			if purchase_order != []:
				purchase_order.save()
				out.append(purchase_order)
				
			purchase_order = frappe.new_doc("Purchase Order")
			purchase_order.schedule_date = i['required_date']
			purchase_order.supplier = i['supplier']
			purchase_order.company = company
			supplier = i['supplier']
			
		purchase_order.append('items', {
			'item_code': i['item_code'],
			'qty': i['pending_qty'],
			'warehouse': i['warehouse'],
			'production_order':production_order,
			'production_order_item':i['production_order_item'],
			'schedule_date':i['required_date'],
			'project':project
		})	
		
	if purchase_order != []:
		purchase_order.save()
		out.append(purchase_order)

	return [p.name for p in out]
	
	
@frappe.whitelist()
def get_sales_order_item_description(sales_order,production_item):
	''' Return Sales Order Items Details for link OF to Sales Order Item'''
	
	if print_debug: frappe.logger().debug("sales_order : " + sales_order)
	
	sales_order = frappe.get_doc("Sales Order", sales_order)
	
	sales_order_item_list = []
	
	for item in sales_order.get('items'):
		if item.item_code == production_item:
			sales_order_item_list.append({"key":item.name,"value":"{0} - {1} : {2}".format(item.idx,item.item_code,item.qty)})
	
	return sales_order_item_list
	