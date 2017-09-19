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
from erpnext.stock.utils import get_incoming_rate

########################## Section Rad++ ##########################
print_debug = False
		

		
def update_status(self, status=None):
	'''Update status of production order if unknown'''
	if not status:
		status = self.get_status(status)
		
	if status != self.status:	
		self.db_set("status", status)
		if print_debug: frappe.errprint("status : " + status)
		
	
	update_required_items(self)
	# update_production_order_item(self)

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
	""" Called to refresh transferred_qty based on stock_entry"""
	self = frappe.get_doc("Production Order", self)
	status = update_status(self,status)
	self.update_planned_qty()
	frappe.msgprint(_("Production Order status is {0}").format(status))
	self.notify_update()
	
@frappe.whitelist()
def stop_unstop(self, status):
	""" Called from client side on Stop/Unstop event"""
	self = frappe.get_doc("Production Order", self)
	status = update_status(self, status)
	self.update_planned_qty()
	frappe.msgprint(_("Production Order status is {0}").format(status))
	self.notify_update()

@frappe.whitelist()
def on_cancel(self,method):
	pass
	
@frappe.whitelist()
def set_production_order_materials_and_operations(source_name, target_doc=None):
	
	frappe.logger().debug("mapper :")	
	
	def postprocess(source, doc):
		frappe.logger().debug("postprocess :")	
		doc.calculate_time()
		doc = set_material_details(doc)

	def update_item(source, target, source_parent):
		target.quantity_per = source.qty / source_parent.quantity
		target.warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_raw_material_warehouse")
	
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
def update_transferred_qty_for_production_order_item(production_order):
	'''update transferred qty from submitted stock entries for that item against the production order'''

	if print_debug: frappe.msgprint("production_order.name : " + production_order.name)
	
	for poi in production_order.production_order_item:
		if print_debug: frappe.msgprint("poi.item_code : " + poi.item_code)
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
	wip_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_wip_warehouse")
	fg_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_fg_warehouse")
	source_warehouse = frappe.db.get_single_value("Manufacturing Settings",
		"default_raw_material_warehouse")
	return {"wip_warehouse": wip_warehouse, "fg_warehouse": fg_warehouse,"source_warehouse":source_warehouse}

def add_to_stock_entry_detail(self, item_dict, bom_no=None):
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
		
		# if print_debug: frappe.errprint("d : " + cstr(d))			
		# if print_debug: frappe.errprint("id.batch_no : " + cstr(item_dict[d].get("batch_no"))
		
		if print_debug: frappe.errprint("se_child.item_code : " + se_child.item_code)			
		if se_child.batch_no:
			if print_debug: frappe.errprint("se_child.batch_no : " + se_child.batch_no)
		if se_child.basic_rate:
			if print_debug: frappe.errprint("se_child.basic_rate : " + cstr(se_child.basic_rate))
			

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
	
			if print_debug: frappe.msgprint("item.item_code : " + cstr(item.item_code))			
			if print_debug: frappe.msgprint("item.batch_no : " + cstr(item.batch_no))
			
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
	if self.production_order:
		item_code = self.pro_doc.production_item
		to_warehouse = self.pro_doc.fg_warehouse
	else:
		item_code = frappe.db.get_value("BOM", self.bom_no, "item")
		to_warehouse = self.to_warehouse

	item = frappe.db.get_value("Item", item_code, ["item_name",
		"description", "stock_uom", "expense_account", "buying_cost_center", "name", "default_warehouse"], as_dict=1)
	
	valuation_rate = frappe.db.get_value("Sales Order Item", self.pro_doc.sales_order_item, ["rate"])
	
	if print_debug: frappe.errprint("valuation_rate : " + cstr(valuation_rate))

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
	if self.purpose in ["Manufacture", "Repack"]:
		for d in self.get("items"):
			if d.transfer_qty and (d.bom_no or d.t_warehouse) and (getattr(self, "pro_doc", frappe._dict()).scrap_warehouse != d.t_warehouse):
				if print_debug: frappe.errprint("set_basic_rate_for_finished_goods")
				if getattr(self, "pro_doc", frappe._dict()).sales_order:
					valuation_rate = frappe.db.get_value("Sales Order Item", self.pro_doc.sales_order_item, ["rate"])
					d.basic_rate = valuation_rate
				else:
					d.basic_rate = flt((raw_material_cost - scrap_material_cost) / flt(d.transfer_qty), d.precision("basic_rate"))
				d.basic_amount = flt((raw_material_cost - scrap_material_cost), d.precision("basic_amount"))

			
def calculate_rate_and_amount(self, force=False, update_finished_item_rate=True):
	set_basic_rate(self, force, update_finished_item_rate)
	self.distribute_additional_costs()
	self.update_valuation_rate()
	self.set_total_incoming_outgoing_value()
	self.set_total_amount()

		
@frappe.whitelist()
def make_stock_entry(production_order_id, purpose, qty=None):
	
	if print_debug: frappe.errprint("make_stock_entry")
	
	production_order = frappe.get_doc("Production Order", production_order_id)
	
	if print_debug: frappe.msgprint(cstr(production_order.name))
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.production_order = production_order_id
	stock_entry.company = production_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = production_order.bom_no
	stock_entry.use_multi_level_bom = production_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(production_order.qty) - flt(production_order.produced_qty))

	if purpose=="Material Transfer for Manufacture":
		if print_debug: frappe.errprint("if purpose")
		if production_order.source_warehouse:
			stock_entry.from_warehouse = production_order.source_warehouse
		stock_entry.to_warehouse = production_order.wip_warehouse
		stock_entry.project = production_order.project	
		if production_order.sales_order:
			if print_debug: frappe.errprint("if production_order.sales_order : " + production_order.sales_order)
			doc_sales_order = frappe.get_doc("Sales Order", production_order.sales_order)
			if doc_sales_order.po_no:
				stock_entry.po_no = doc_sales_order.po_no
	else:
		stock_entry.from_warehouse = production_order.wip_warehouse
		stock_entry.to_warehouse = production_order.fg_warehouse
		additional_costs = get_additional_costs(production_order, fg_qty=stock_entry.fg_completed_qty)
		stock_entry.project = frappe.db.get_value("Stock Entry",{"production_order": production_order_id,"purpose": "Material Transfer for Manufacture"}, "project")
		stock_entry.set("additional_costs", additional_costs)

	get_items(stock_entry)
	
	if purpose=="Material Transfer for Manufacture":
		for d in stock_entry.items:
			item = frappe.get_doc("Item",d.item_code)
			if production_order.sales_order_item and item.variant_of == "PM":
				if frappe.db.get_value("Sales Order Item", production_order.sales_order_item, "description_sous_traitance"):
					d.s_warehouse = frappe.db.get_value("Customer", production_order.customer, "default_warehouse")
					d.is_sample_item = 1
				else:
					d.s_warehouse = item.default_warehouse
			elif item.default_warehouse:
				d.s_warehouse = item.default_warehouse
			else:
				d.s_warehouse = production_order.source_warehouse
				
	if purpose=="Manufacture":
		if print_debug: frappe.msgprint("production_order.name : " + production_order.name)
		stock_entry_for_reserved_material = frappe.get_value("Stock Entry", filters={"production_order": production_order_id, "purpose":"Material Transfer for Manufacture", "docstatus":1})
		if print_debug: frappe.msgprint("stock_entry_for_reserved_material : " + stock_entry_for_reserved_material)
		reserved_material = frappe.get_doc("Stock Entry",stock_entry_for_reserved_material)
		for d in stock_entry.items:
			item = frappe.get_doc("Item",d.item_code)
			if print_debug: frappe.msgprint("item.name : " + item.name)
			stock_entry_for_reserved_material_item = frappe.get_value("Stock Entry Detail", filters={"parent": stock_entry_for_reserved_material, "item_code":item.name})
			if stock_entry_for_reserved_material_item:
				reserved_material_detail = frappe.get_doc("Stock Entry Detail",stock_entry_for_reserved_material_item)
				if print_debug: frappe.msgprint("stock_entry_for_reserved_material_item : " )
				if print_debug: frappe.msgprint(stock_entry_for_reserved_material_item)
				if production_order.customer and item.variant_of == "PM":
					d.is_sample_item = 1
					#d.batch_no = reserved_material_detail.batch_no
					if reserved_material_detail.qty_per_box:
						d.qty_per_box = reserved_material_detail.qty_per_box
	
	return stock_entry.as_dict()



	
