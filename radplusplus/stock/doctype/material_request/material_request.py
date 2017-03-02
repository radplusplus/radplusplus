# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# ERPNext - web based ERP (http://erpnext.com)
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import cstr, flt, getdate, new_line_sep
from frappe import msgprint, _
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.stock_balance import update_bin_qty, get_indented_qty
from erpnext.controllers.buying_controller import BuyingController
from erpnext.manufacturing.doctype.production_order.production_order import get_item_details


print_debug = True
	
@frappe.whitelist()
def update_default_values(material_request, method):
	if print_debug: frappe.errprint("update_default_values:")

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
	def postprocess(source, target_doc):
		set_missing_values(source, target_doc)

	doclist = get_mapped_doc("Material Request", source_name, 	{
		"Material Request": {
			"doctype": "Purchase Order",
			"validation": {
				"docstatus": ["=", 1],
				"material_request_type": ["=", "Purchase"]
			}
		},
		"Material Request Item": {
			"doctype": "Purchase Order Item",
			"field_map": [
				["name", "material_request_item"],
				["parent", "material_request"],
				["uom", "stock_uom"],
				["uom", "uom"],
				["batch_no", "batch_no"] # 2016-11-07 - JDLP
			],
			"postprocess": update_item,
			"condition": lambda doc: doc.ordered_qty < doc.qty
		}
	}, target_doc, postprocess)

	return doclist

@frappe.whitelist()
def make_request_for_quotation(source_name, target_doc=None):
	doclist = get_mapped_doc("Material Request", source_name, 	{
		"Material Request": {
			"doctype": "Request for Quotation",
			"validation": {
				"docstatus": ["=", 1],
				"material_request_type": ["=", "Purchase"]
			}
		},
		"Material Request Item": {
			"doctype": "Request for Quotation Item",
			"field_map": [
				["name", "material_request_item"],
				["parent", "material_request"],
				["uom", "uom"],
				["batch_no", "batch_no"] # 2016-11-07 - JDLP
			]
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_purchase_order_based_on_supplier(source_name, target_doc=None):
	if target_doc:
		if isinstance(target_doc, basestring):
			import json
			target_doc = frappe.get_doc(json.loads(target_doc))
		target_doc.set("items", [])

	material_requests, supplier_items = get_material_requests_based_on_supplier(source_name)

	def postprocess(source, target_doc):
		target_doc.supplier = source_name

		target_doc.set("items", [d for d in target_doc.get("items")
			if d.get("item_code") in supplier_items and d.get("qty") > 0])

		set_missing_values(source, target_doc)

	for mr in material_requests:
		target_doc = get_mapped_doc("Material Request", mr, 	{
			"Material Request": {
				"doctype": "Purchase Order",
			},
			"Material Request Item": {
				"doctype": "Purchase Order Item",
				"field_map": [
					["name", "material_request_item"],
					["parent", "material_request"],
					["uom", "stock_uom"],
					["uom", "uom"],
					["batch_no", "batch_no"] # 2016-11-07 - JDLP
				],
				"postprocess": update_item,
				"condition": lambda doc: doc.ordered_qty < doc.qty
			}
		}, target_doc, postprocess)

	return target_doc

@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		qty = flt(obj.qty) - flt(obj.ordered_qty) \
			if flt(obj.qty) > flt(obj.ordered_qty) else 0
		target.qty = qty
		target.transfer_qty = qty
		target.conversion_factor = 1

		if source_parent.material_request_type == "Material Transfer":
			target.t_warehouse = obj.warehouse
		else:
			target.s_warehouse = obj.warehouse

	def set_missing_values(source, target):
		target.purpose = source.material_request_type
		target.run_method("calculate_rate_and_amount")

	doclist = get_mapped_doc("Material Request", source_name, {
		"Material Request": {
			"doctype": "Stock Entry",
			"validation": {
				"docstatus": ["=", 1],
				"material_request_type": ["in", ["Material Transfer", "Material Issue"]]
			}
		},
		"Material Request Item": {
			"doctype": "Stock Entry Detail",
			"field_map": {
				"name": "material_request_item",
				"parent": "material_request",
				"uom": "stock_uom",
				"batch_no": "batch_no" # 2016-11-07 - JDLP
			},
			"postprocess": update_item,
			"condition": lambda doc: doc.ordered_qty < doc.qty
		}
	}, target_doc, set_missing_values)

	return doclist

@frappe.whitelist()
def raise_production_orders(material_request):
	mr= frappe.get_doc("Material Request", material_request)
	errors =[]
	production_orders = []
	from erpnext.manufacturing.doctype.production_order.production_order import OverProductionError, get_default_warehouse
	warehouse = get_default_warehouse() # 2016-11-07 - JDLP
	for d in mr.items:
		if (d.qty - d.ordered_qty) >0:
			if frappe.db.get_value("BOM", {"item": d.item_code, "is_default": 1}):
				prod_order = frappe.new_doc("Production Order")
				prod_order.production_item = d.item_code
				prod_order.qty = d.qty - d.ordered_qty
				prod_order.fg_warehouse = d.warehouse
				prod_order.description = d.description
				prod_order.stock_uom = d.uom
				prod_order.expected_delivery_date = d.schedule_date
				prod_order.sales_order = d.sales_order
				prod_order.bom_no = get_item_details(d.item_code).bom_no
				prod_order.material_request = mr.name
				prod_order.material_request_item = d.name
				prod_order.planned_start_date = mr.transaction_date
				prod_order.company = mr.company
				prod_order.batch_no = d.batch_no # 2016-11-07 - JDLP
				prod_order.wip_warehouse = warehouse.get('wip_warehouse') # 2016-11-07 - JDLP
				prod_order.save()
				production_orders.append(prod_order.name)
			else:
				errors.append(d.item_code + " in Row " + cstr(d.idx))
	if production_orders:
		message = ["""<a href="#Form/Production Order/%s" target="_blank">%s</a>""" % \
			(p, p) for p in production_orders]
		msgprint(_("The following Production Orders were created:" + '\n' + new_line_sep(message)))
	if errors:
		msgprint(_("Productions Orders cannot be raised for:" + '\n' + new_line_sep(errors)))
	return production_orders