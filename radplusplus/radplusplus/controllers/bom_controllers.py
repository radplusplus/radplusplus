#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt
from frappe.model.document import Document
from radplusplus.radplusplus.controllers.item_variant import (get_item_variant_attributes_values, create_variant_and_submit) #JDLP
import operator

########################## Section Rad++ ##########################
print_debug = False

@frappe.whitelist()
def make_bom_from_list_of_items(items_list, create_new_if_exist):		 
	if len(items_list) > 0 :
		for item in items_list:
			doc_item = frappe.get_doc("Item",item.name)
			if doc_item.item_code:				
				make_dynamic_bom(doc_item, create_new_if_exist)
		frappe.msgprint("BOM créés.")
	else:
		frappe.msgprint("Aucun variant de trouvé.")
		

@frappe.whitelist()
def make_bom_from_template(template, create_new_if_exist):
	
	items_list = frappe.get_list(
		"Item",
		filters={'variant_of': template},
		fields=['name','variant_of']
	)
	
	if print_debug: frappe.logger().debug("len(items_list):" + str(len(items_list)))
	
	if len(items_list) > 25 :
		#make_bom_from_list_of_items(items_list, create_new_if_exist)
		from frappe.utils.background_jobs import enqueue
		enqueue("radplusplus.radplusplus.controllers.bom_controllers.make_bom_from_list_of_items",  items_list=items_list, create_new_if_exist=create_new_if_exist) 
		frappe.msgprint("BOM en cours de création.")
	else:
		make_bom_from_list_of_items(items_list, create_new_if_exist)
		
@frappe.whitelist()
def make_bom(item, method):
	if print_debug: frappe.logger().debug("***make_bom***")
	if print_debug: frappe.logger().debug("item_code:" + item.item_code)
	if print_debug: frappe.logger().debug("variant_of:" + str(item.variant_of))
	if print_debug: frappe.logger().debug("configurator_of:" + str(item.configurator_of))
	
	make_dynamic_bom(item)
	
def make_child_variant(parent, template_name):
	if print_debug: frappe.logger().debug("***make_child_variant***")
	
	#mapper selon le noms des attributes
	attribute_map={}
	child_attributes = get_item_variant_attributes_values(template_name)
	parent_attributes = get_item_variant_attributes_values(parent.item_code)
	for child_attribute in child_attributes:
		for item_attribute in parent_attributes:
			if print_debug: frappe.logger().debug("attribute: " + item_attribute[0])	
			if print_debug: frappe.logger().debug("Uninheritable: " + cstr(item_attribute[3]))					
			#if child_attribute[0] == item_attribute[0] and item_attribute[3] == 0:
			if child_attribute[0] == item_attribute[0]:
				attribute_map[child_attribute[0]] = child_attribute[0]
	
	#mapper selon la configuration dans la bd
	attribute_map_bd = get_attribute_mapping(parent.variant_of, template_name)
	if attribute_map_bd:
		attribute_map.update(attribute_map_bd)
	parent_attributes_dict = {i[0]: i[1] for i in parent_attributes}
	args = {}
	for key, value in attribute_map.iteritems():
		att_value = get_attribute_value_mapping(parent.variant_of, template_name, key, value, parent_attributes_dict[key])
		args[value] = att_value
		
	# for child_attribute in child_attributes:
		# for item_attribute in parent_attributes:
			# if child_attribute[0] == item_attribute[0]:
				# args[child_attribute[0]] = item_attribute[1]
	if print_debug: frappe.logger().debug(args)
	return create_variant_and_submit(template_name, args)

def make_bom_base(item, configurator_bom):
	bom = frappe.new_doc("BOM")
	bom.item = item.item_code
	bom.item_name = item.item_code
	bom.quantity = configurator_bom.quantity
	bom.uom = configurator_bom.uom
	bom.is_active = 1
	bom.is_default = 1
	bom.with_operations = 1
	bom.rm_cost_as_per = "Valuation Rate"
	
	return bom
	
def make_bom_item(parent, bom, config_bom_item):
	item = frappe.get_doc("Item", config_bom_item.item)
	if item.has_variants:
		item = make_child_variant(parent, config_bom_item.item)
		
	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = item.item_code
	bom_item.item_name = item.item_code
	bom_item.related_operation = config_bom_item.related_operation
	bom_item.qty = config_bom_item.quantity
	bom_item.rate = config_bom_item.rate
	bom.append("items", bom_item)
	return bom_item
	
def make_bom_oper(parent, bom, config_bom_oper):
	operation = frappe.get_doc("Operation", config_bom_oper.operation)
	bom_operation = frappe.new_doc("BOM Operation")
	bom_operation.operation = operation.name
	bom_operation.workstation = operation.workstation
	bom_operation.no_oper = config_bom_oper.operation_sequence
	bom_operation.hour_rate = config_bom_oper.hour_rate
	bom_operation.time_in_mins = config_bom_oper.time_in_mins
	bom_operation.qty = config_bom_oper.quantity
	bom.append("operations", bom_operation)
	return bom_operation
	
def make_packaging(parent, bom):
	if print_debug: frappe.logger().debug("***make_packaging***")
	
	if parent.variant_of not in ["PV","PH"]:
		return
	
	packaging = get_packaging(parent)
	
	if not packaging:
		return
	
	bom_item = frappe.new_doc("BOM Item")
	bom_item.item_code = packaging.item_code
	bom_item.item_name = packaging.item_name
	bom_item.related_operation = 0
	bom_item.qty = .05
	bom_item.rate = packaging.valuation_rate
	bom.append("items", bom_item)
	return bom_item
	
def get_packaging(parent):
		
	# RENMAI - 2017-05-25
	# Faire une requête SQL au lieu de multiple get_value.
	filters = {"parent":parent.name,"attribute":"Packaging"}
	attribute_packaging = frappe.db.get_value("Item Variant Attribute",
	filters,"attribute_value")
	
	filters = {"parent":parent.name,"attribute":"Flooring Width"}
	attribute_flooring_width = frappe.db.get_value("Item Variant Attribute",
	filters,"attribute_value")
	
	if not attribute_flooring_width :
		return
	
	filters = {"flooring_width":attribute_flooring_width}
	box_size = frappe.db.get_value("Flooring Width",
	filters,"box_size")

	if not attribute_flooring_width :
		return
	
	filters = {"packaging":attribute_packaging, "box_size":box_size}
	box = frappe.db.get_value("Plancher Par Boite",
	filters,"box")
	
	if not box :
		return
		
	box = frappe.get_doc("Item", box)
	
	return box
	
def has_bom(item_code):
	if print_debug: frappe.logger().debug("***has_bom***")
	bom = get_bom(item_code)
	
	if print_debug: frappe.logger().debug("bom:" + str(bom))
	exist = (bom != None)
	if print_debug: frappe.logger().debug("has_bom:" + str(exist))
	return exist

def get_boms(item_code):
	return frappe.get_value('BOM',
	filters={'item_name': item_code},
	fieldname='name', ignore=None, as_dict=False,
	debug=False, order_by=None, cache=False)
	
def get_bom(item_code):
	boms =  get_boms(item_code)
	if boms is not None:
		frappe.errprint("boms:" + cstr(boms))
		return frappe.get_doc('BOM', boms)
	return None
	
def make_dynamic_bom(item, create_new_if_exist = False):
	if print_debug: frappe.logger().debug("***make_dynamic_bom***")
	#Si c'est un variant et que son modèle possède un constructeur de BOM
	if item.variant_of is not None and frappe.db.exists("Configurator Bom", item.variant_of):
		#RENMIA - 2017-09-11 - ajout pour ne pas créer de BOM pour une pièce qui n'a pas les mêmes attributs que le modèle.
		# frappe.errprint(item.name)
		# frappe.errprint(item.variant_of)
		# item_attributes = frappe.get_list(
			# "Item Variant Attribute",
			# filters={'parent': item.name},
			# fields=['name']
		# )
		# template_attributes = frappe.get_list(
			# "Item Variant Attribute",
			# filters={'parent': item.variant_of},
			# fields=['name']
		# )
		
		# if item_attributes != template_attributes:
			# return
			
		cb = frappe.get_doc("Configurator Bom", item.variant_of)
		
		#Obtenir le bom actuel
		bom = get_bom(item.item_code)
		if bom is None or create_new_if_exist:
			bom = make_bom_base(item, cb)
		else:
			return
		
		for bom_oper in cb.operations:
			make_dynamic_bom_oper(item, bom, bom_oper)
			
		for bom_item in cb.items:
			make_bom_item(item, bom, bom_item)
			
		#make_packaging(item, bom)
			
		bom.insert(ignore_permissions=True)
		bom.submit()
		if print_debug: frappe.logger().debug("bom created: " + cstr(bom.name))

def make_dynamic_bom_oper(parent, bom, bom_oper):
	if print_debug: frappe.logger().debug("***make_dynamic_bom_oper***")
	
	if bom_oper.condition == "Always":
		make_bom_oper(parent, bom, bom_oper)
	elif bom_oper.condition == "Attribute Condition":
		if evaluate_attribute_condition(parent, bom_oper):
			make_bom_oper(parent, bom, bom_oper)
	elif bom_oper.condition == "Query":
		not_implementer = True

def make_dynamic_bom_item(parent, bom, bom_item):
	if print_debug: frappe.logger().debug("***make_dynamic_bom_item***")
	
	if bom_item.condition == "Always":
		make_bom_oper(parent, bom, bom_item)
	elif bom_item.condition == "Attribute Condition":
		if evaluate_attribute_condition(parent, bom_item):
			make_bom_oper(parent, bom, bom_item)
	elif bom_item.condition == "Query":
		not_implementer = True
		
def evaluate_attribute_condition(parent, bom_condition):
	if print_debug: frappe.logger().debug("evaluate_attribute_condition: ")
	attributes = {d.attribute:_(d.attribute_value) for d in parent.attributes}
	
	truth = get_truth(attributes[bom_condition.attribute],bom_condition.operator, bom_condition.attribute_value)
	
	return truth

def get_truth(inp, relate, cut):
    ops = {'>': operator.gt,
		   '&gt;': operator.gt,
           '<': operator.lt,
           '&lt;': operator.lt,
           '>=': operator.ge,
           '&gt;=': operator.ge,
           '<=': operator.le,
           '&lt;=': operator.le,
           '=': operator.eq,
           '!=': operator.ne,
           '<>': operator.ne,
           '&lt;&gt;': operator.ne}
    return ops[relate](inp, cut)

	
######### Section a transferer dans une bd ########
def get_attribute_mapping(parent_template_name, child_template_name):
	if parent_template_name == "PM" and child_attribute == "PB":
		return {"Flooring Grade" : "Wood Grade",
				"Flooring Width" : "Wood Width"}
		
def get_attribute_value_mapping(parent_template_name, child_template_name, attribute_source, attribute_destination, value):
	dict = {}
	if parent_template_name == "PM" and child_template_name == "PB" and attribute_source == "Flooring Width" and attribute_destination == "Wood Width":
		dict = {'3"' : '3-5/8"',
				'4"' : '4-5/8"',
				'5"' : '5-5/8"'}
	
	if child_template_name == "PM" and attribute_source == "Wirebrushed" and attribute_destination == "Wirebrushed":
		dict = {value : 'Non'}
	
	if child_template_name == "PM" and attribute_source == "Hand Scraped" and attribute_destination == "Hand Scraped":
		dict = {value : 'Non'}
		
	if value in dict:
		return dict[value]
	return value
	
