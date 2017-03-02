# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from radplusplus.radplusplus.controllers.item_variant import (get_item_variant_attributes_values, create_variant_and_submit) #JDLP


class BomMaker(Document):
	pass

print_debug = False
	
@frappe.whitelist()
def make_bom(item, method):
	if print_debug: frappe.errprint("make_bom:")
	if print_debug: frappe.errprint("item_code:" + item.item_code)
	if print_debug: frappe.errprint("variant_of:" + str(item.variant_of))
	if print_debug: frappe.errprint("configurator_of:" + str(item.configurator_of))
			
	if item.variant_of in ["PV", "PH"] and not has_bom(item.item_code):
		make_variant_PV_PH(item)
	
def make_variant_PV_PH(item):
	if print_debug: frappe.errprint("make_variant_PV_PH:")
	if print_debug: frappe.errprint("item_code:" + item.item_code)
	
	bom = make_bom_base(item)
	
	pm = make_base_PM(item)
	bom_item_pm = make_bom_item(bom, pm)
	bom.append("items", bom_item_pm)
	
	operation = get_required_operation(item)
	bom_operation = make_bom_oper(bom, operation)
	bom.append("operations", bom_operation)
	
	#bom.save(True)
	#bom.docs = 1
	bom.insert(ignore_permissions=True)
	bom.submit()
	
def make_base_PM(item):
	pm = "PM"
	pm_attributes = get_item_variant_attributes_values(pm)
	item_attributes = get_item_variant_attributes_values(item.item_code)
	if print_debug: frappe.errprint("pm_attributes:" + str(pm_attributes))
	if print_debug: frappe.errprint("item_attributes:" + str(item_attributes))
	args = {}
	for pm_attribute in pm_attributes:
		for item_attribute in item_attributes:
			if pm_attribute[0] == item_attribute[0]:
				args[pm_attribute[0]] = item_attribute[1]
	if print_debug: frappe.errprint(args)
	return create_variant_and_submit(pm, args)

def make_bom_base(item):
	bom = frappe.new_doc("BOM")
	bom.item = item.item_code
	bom.item_name = item.item_code
	bom.quantity = 1
	bom.is_active = 1
	bom.is_default = 1
	bom.with_operations = 1
	bom.rm_cost_as_per = "Valuation Rate"
	bom.UOM = "pi²"
	
	return bom
	
def make_bom_item(bom, item):
	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_code
	bom_item.item_name = item.item_code
	bom_item.qty = 1
	bom_item.rate = 0
	
	return bom_item
	
def make_bom_oper(bom, operation):
	bom_operation = frappe.new_doc("BOM Item")
	bom_operation.operation = operation.name
	bom_operation.workstation = operation.workstation
	bom_operation.hour_rate = "CAD"
	bom_operation.time_in_mins = 0.063
	bom_operation.qty = 1
	
	return bom_operation
	
def get_required_operation(item):
	configurator_operations = frappe.get_value('Configurator Operation',
	filters={'configurator_template': item.variant_of},
	fieldname='operation', ignore=None, as_dict=False,
	debug=False, order_by=None, cache=False)
	
	if print_debug: frappe.errprint("configurator_operations:" + str(configurator_operations))
	operation = frappe.get_doc('Operation', configurator_operations)
	if print_debug: frappe.errprint("Operation:" + str(operation))
	if print_debug: frappe.errprint("Operation:" + str(operation.workstation))
	
	return operation
	
def has_bom(item_code):
	bom = frappe.get_value('BOM',
	filters={'item_name': item_code},
	fieldname='name', ignore=None, as_dict=False,
	debug=False, order_by=None, cache=False)
	
	if print_debug: frappe.errprint("bom:" + str(bom))
	exist = (bom != None)
	if print_debug: frappe.errprint("exist:" + str(exist))
	return exist
	#destination.__dict__.update(source.__dict__)
	# Template Bom Settings
	# Template
	# Operation
	# Workstation
	# time_in_mins
	# qty
	# rate
	
	

	
	