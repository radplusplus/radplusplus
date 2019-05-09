# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import cstr, flt
from frappe.model.document import Document
import hashlib
from radplusplus.radplusplus.controllers.item_variant import get_item_variant_attributes_values

print_debug = True

class ItemVariantHashCode(Document):
	pass

# 2017-02-21 - JDLP
@frappe.whitelist()
def create_from_item(item, method):
	create_from_variant(item)
	
def create_from_variant(item):	
	if item.variant_of is not None:
		hash_code = get_hash_code(item.variant_of, [x.attribute_value for x in item.attributes])
				
		item_variant_hash_code = get_variant_hashcode_from_item_code(item.item_code)
		if item_variant_hash_code is None:
			item_variant_hash_code = frappe.new_doc("Item Variant HashCode")
			item_variant_hash_code.item = item.item_code
		item_variant_hash_code.hashcode = hash_code
		item_variant_hash_code.save(True)

def get_hash_code(template_name, attribute_value_list):
	
	if isinstance(template_name, basestring):
		att_str = template_name
	else:
		att_str = template_name.name
	#att_str = template_name
	attributes = get_item_variant_attributes_values(template_name)
	
	if print_debug: frappe.logger().debug("attributes: " + cstr(attributes))
	if print_debug: frappe.logger().debug("attribute_value_list: " + cstr(attribute_value_list))
	for value in attribute_value_list:
		att_str += value
		
	bytes = att_str.encode("UTF-8")
	hash_object = hashlib.md5(bytes)
	return hash_object.hexdigest()

def get_variant_hashcode_from_item_code(item_code):
	filters = {"item": item_code}
	name = frappe.db.get_value("Item Variant HashCode",	filters,"name",None,False,False,False)
	if name is not None:
		return frappe.get_doc("Item Variant HashCode", name)
		
def get_item_from_variant_hashcode(hashcode):
	if print_debug: frappe.logger().debug("get_item_from_variant_hashcode")
	if print_debug: frappe.logger().debug("hashcode: " + hashcode)
	
	if frappe.db.exists("Item Variant HashCode", hashcode):
		return frappe.get_doc("Item Variant HashCode", hashcode).item
	
def get_item_from_attribute_value_list(template_name, attribute_value_list):
	return get_item_from_variant_hashcode(get_hash_code(template_name, attribute_value_list))
	
@frappe.whitelist()
def delete_from_item(item, method):
	delete_from_variant(item)

def delete_from_variant(item):
	item_variant_hash_code = get_variant_hashcode_from_item_code(item.item_code)
	if item_variant_hash_code:
		frappe.delete_doc("Item Variant HashCode", item_variant_hash_code.name)
	
@frappe.whitelist()
def update_all_variants():
	variants = frappe.get_all('Item', fields=["name"])
	for variant in variants:
		create_from_variant(frappe.get_doc("Item", variant))


##### Hashcode #####
@frappe.whitelist()
def get_variant(template, args, variant=None):
	if print_debug: frappe.logger().debug("radpp get_variant ")
	"""Validates Attributes and their Values, then looks for an exactly matching Item Variant

		:param item: Template Item
		:param args: A dictionary with "Attribute" as key and "Attribute Value" as value
	"""
	if isinstance(args, basestring):
		args = json.loads(args)

	if not args:
		frappe.throw(_("Please specify at least one attribute in the Attributes table"))
	
	item = get_item_from_attribute_value_list(template, args.values())
	if item is not None:
		if print_debug: frappe.logger().debug(" item_code : " + item.item_code)
		return item.item_code
		
	#return find_variant(template, args, variant)
##### #####