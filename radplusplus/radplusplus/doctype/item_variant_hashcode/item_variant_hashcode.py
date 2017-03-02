# -*- coding: utf-8 -*-
# Copyright (c) 2015, RAD plus plus inc. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr, flt
from frappe.model.document import Document
import hashlib

class ItemVariantHashCode(Document):
	pass

# 2017-02-21 - JDLP
@frappe.whitelist()
def create_from_item(item, method):
	create_from_variant(item)
	
def create_from_variant(item):	
	if item.variant_of:
		hash_code = get_hash_code([x.attribute_value for x in item.attributes])
				
		item_variant_hash_code = get_variant_hashcode_from_item_code(item.item_code)
		if item_variant_hash_code is None:
			item_variant_hash_code = frappe.new_doc("Item Variant HashCode")
			item_variant_hash_code.item = item.item_code
		item_variant_hash_code.hashcode = hash_code
		item_variant_hash_code.save(True)

def get_hash_code(attribute_value_list):
	att_str = ""
	for value in attribute_value_list:
		att_str += value
		
	bytes = att_str.encode("UTF-8")
	hash_object = hashlib.md5(bytes)
	return hash_object.hexdigest()

def get_variant_hashcode_from_item_code(item_code):
	filters = {"item": item_code}
	name = frappe.db.get_value("Item Variant HashCode",	filters,"name",None,False,False,False)
	if name:
		return frappe.get_doc("Item Variant HashCode", name)
		
def get_item_from_variant_hashcode(hashcode):
	frappe.errprint("get_item_from_variant_hashcode")
	frappe.errprint("hashcode: " + hashcode)
	item_variant_hashcode = frappe.get_doc("Item Variant HashCode", hashcode)
	
	filters = {"hashcode": hashcode}
	name = frappe.db.get_value("Item Variant HashCode",	filters,"name",None,False,False,False)
	frappe.errprint("name: " + name)
	if name:
		return frappe.get_doc("Item Variant HashCode", name).item

@frappe.whitelist()		
def get_item_from_attribute_value_list(attribute_value_list):
	return get_item_from_variant_hashcode(get_hash_code(attribute_value_list))
	
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

