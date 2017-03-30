#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, flt
import json
import itertools
from frappe.utils.jinja import render_template
import erpnext
from erpnext.controllers.item_variant import validate_item_variant_attributes
import time
import radplusplus

########################## Section Rad++ ##########################
print_debug = False

@frappe.whitelist()
def item_after_insert(item, args):
	if print_debug: frappe.errprint("item_after_insert :" + cstr(item))
	from radplusplus.radplusplus.doctype.bom_maker.bom_maker import make_bom
	make_bom(item, args)
	make_variant_price_from_item_code(item, args)

@frappe.whitelist()
def item_before_save(item, args):
	if print_debug: frappe.errprint("item_before_save :" + cstr(item))
	make_variant_description(item)

@frappe.whitelist()
def create_variant(item, args):
	start_time = time.time()
	variant = erpnext.controllers.item_variant.create_variant(item, args)
	frappe.errprint("--- create_variant %s seconds ---" % (time.time() - start_time))
	
	start_time = time.time()
	make_variant_description(variant)
	frappe.errprint("--- make_variant_description %s seconds ---" % (time.time() - start_time))
	return variant


@frappe.whitelist()
def get_variant(template, args, variant=None):
	frappe.errprint("radpp get_variant ")
	"""Validates Attributes and their Values, then looks for an exactly matching Item Variant

		:param item: Template Item
		:param args: A dictionary with "Attribute" as key and "Attribute Value" as value
	"""
	if isinstance(args, basestring):
		args = json.loads(args)

	if not args:
		frappe.throw(_("Please specify at least one attribute in the Attributes table"))
	
	frappe.errprint(" before import " )
	from radplusplus.radplusplus.doctype.item_variant_hashcode.item_variant_hashcode import get_item_from_attribute_value_list
	
	frappe.errprint(" after import " )
	item_code = get_item_from_attribute_value_list(template, args.values())
	frappe.errprint(" item_code : " + cstr(item_code))
	if item_code:
		return item_code
		
	#return find_variant(template, args, variant)
	
#Obsolete
#def update_description(template_item_code, variant):			
#	template = frappe.get_doc("Item", template_item_code)
#	make_variant_description(template, variant)

# 2016-11-25 - JDLP
# Fonction pour gérer la description en utilisant les templates
# Permet de gère les description en plusieurs langues
@frappe.whitelist()
def make_variant_description(variant):
#Matière première en {{Wood Species}}, {{Wood Grad}},{{Wood Width}}
#Raw material, {{Wood Species}}, {{Wood Grad}},{{Wood Width}}
	# {u'Wood Width': u'2-5/8"'
	#, u'Wood Grade': u'Colonial - (GRADE-CN)'
	#, u'Wood Species': u'Pine'
	#, u'Thickness': u'4/4'}
	if variant.variant_of is not None:
		template = frappe.get_doc("Item", variant.variant_of)
		for template in template.description_template:
			jinjaTemplate = template.description
			values = {}
			for d in variant.attributes:
				attribute = frappe.get_doc("Item Attribute", d.attribute)
				jinjaTemplate = jinjaTemplate.replace("{{"+d.attribute, "{{"+attribute.field_name)
				
				if print_debug: frappe.errprint(template.language)
				target_field = "target_name"
				source_field = "source_name"
				template_language = template.language
				if template.language == "en":
					target_field = "source_name"
					source_field = "target_name"
					template_language = "fr"
					
				if print_debug: frappe.errprint(d.attribute)
				if print_debug: frappe.errprint(attribute.field_name)
				if print_debug: frappe.errprint(d.attribute_value)
				
				filters = {'language_code': template_language,source_field:d.attribute_value}
				target_name = frappe.db.get_value("Translation",filters,target_field,None,False,False,False)
				values[attribute.field_name] = target_name or d.attribute_value
				if print_debug: frappe.errprint(target_name)
				if print_debug: frappe.errprint(jinjaTemplate)
				
			if print_debug: frappe.errprint(jinjaTemplate)
			if print_debug: frappe.errprint(values)
			description = render_template(jinjaTemplate, values)
			
			filters = {"parent": variant.name,
							"parentfield": "language",
							"parenttype": "Item",
							"language": template.language}
			name = frappe.db.get_value("Item Language",	filters,"name",None,False,False,False)
			language_description = None
			if name:
				language_description = frappe.get_doc("Item Language", name)
			if not language_description:
				values = filters
				values["doctype"] = "Item Language"
				language_description = frappe.get_doc(values)
			language_description.description = description
			variant.append("language", language_description)

# 2016-08-23 Ajoute par Antonio pour creer et faire le submit 
@frappe.whitelist()
def create_variant_and_submit(template_item_code, args):
	print_debug = True
	if print_debug: frappe.errprint("--- create_variant_and_submit ---")
	
	start_time = time.time()
	
	if isinstance(args, basestring):
		args = json.loads(args)
	
	if print_debug: frappe.errprint(template_item_code)
	if print_debug: frappe.errprint(args)
	
	template = frappe.get_doc("Item", template_item_code)
	
	start_time1 = time.time()
	create_missing_attributes_values(template, args)
	frappe.errprint("--- create_missing_attributes_values %s seconds ---" % (time.time() - start_time1))
	
	start_time2 = time.time()
	validate_item_variant_attributes(template, args)
	frappe.errprint("--- validate_item_variant_attributes %s seconds ---" % (time.time() - start_time2))
	
	start_time3 = time.time()
	variant = erpnext.controllers.item_variant.get_variant(template, args)
	frappe.errprint("--- get_variant %s seconds ---" % (time.time() - start_time3))
	if variant is None:
		start_time4 = time.time()
		variant = create_variant(template_item_code, args)
		frappe.errprint("--- create_variant %s seconds ---" % (time.time() - start_time4))
		
		#Tenter de trouver un item avec le meme code
		#duplicate_item_code = frappe.db.sql_list("""select item_name from `tabItem` item where item_name=%s)""",variant.item_code)
		
		start_time5 = time.time()
		if not frappe.db.exists("Item", variant.item_code):
			variant.docs = 1
			variant.save(True)
		frappe.errprint("--- save %s seconds ---" % (time.time() - start_time5))
		
		start_time6 = time.time()
		variant = frappe.get_doc("Item", variant.item_code)
		frappe.errprint("--- get_doc %s seconds ---" % (time.time() - start_time6))
		
		frappe.errprint("--- create_variant_and_submit %s seconds ---" % (time.time() - start_time))
		return variant
		
	frappe.errprint("--- create_variant_and_submit %s seconds ---" % (time.time() - start_time))
	return variant

# 2016-10-30 - JDLP
# Fonction du configurateur:
# Permet de transferer la valeur d'un champ de type Doc_Type en Item Atribute Value
# Fonctionnement:
# Si un valeur n'existe pas dans Attribute Value
# Recuperer le name 
def create_missing_attributes_values(template, args):
	#if print_debug: frappe.errprint("create_missing_attributes_values")
	# Pour chacun des pairs [parent:attribute_value]
	for parent, attribute_value in args.items():
		#if print_debug: frappe.errprint("[parent=" + parent + ":attribute_value=" + attribute_value + "]")
		# Si l'item_attribute_value n'existe pas
		
		#if print_debug: frappe.errprint("Need to create=" + cstr(get_item_attribute_value(parent, attribute_value) is None))
		if get_item_attribute_value(parent, attribute_value) is None:
			# Name = abreviation!
			# Si le parent correspond a une table
			doc_name = cstr(parent)
			table_exist = frappe.db.table_exists(doc_name)
			#if print_debug: frappe.errprint("doc_name=" + doc_name + " Exist=" + cstr(table_exist))
			
			# Retrouver le record
			if table_exist:
				doc = frappe.get_doc(doc_name, attribute_value)
				abbr = attribute_value
				if doc.abbr:
					abbr = doc.abbr
				#if print_debug: frappe.errprint("doc=" + doc.name)
				if doc and doc.name:
					item_attribute_value = frappe.get_doc({
						"doctype": "Item Attribute Value",
						"parent": parent,
						"parentfield": "item_attribute_values",
						"parenttype": "Item Attribute",
						"attribute_value": attribute_value,
						"abbr": abbr,
						"document_type": doc_name
					})
					item_attribute_value.insert()


def get_item_attribute_value(parent, attribute_value):
	#if print_debug: frappe.errprint("get_item_attribute_value")
	item_attribute_value = None

	filters = {"parent":parent,"attribute_value":attribute_value}
	item_attribute_value = frappe.db.get_value("Item Attribute Value",
	filters,"name",None,False,False,False)
	return item_attribute_value

# 2016-11-01 
@frappe.whitelist()
def get_item_variant_attributes_values(item_code):
	args = {'item_code': item_code}
	query = frappe.db.sql("""
			SELECT
			`tabItem Attribute`.attribute_name,
			`tabItem Variant Attribute`.attribute_value,
			`tabItem Attribute`.field_name
			FROM
			`tabItem Variant Attribute`
			INNER JOIN `tabItem Attribute` ON `tabItem Variant Attribute`.attribute = `tabItem Attribute`.`name`
			WHERE
			`tabItem Variant Attribute`.parent = %(item_code)s
			ORDER BY
			`tabItem Variant Attribute`.idx ASC""", args, as_list = 1)
	
	return query
	
# 2016-10-26 
@frappe.whitelist()
def get_show_attributes(item_code):
	args = {'item_code': item_code}
	query = frappe.db.sql("""
			SELECT
				`tabItem Attribute`.attribute_name,
				`tabItem Attribute`.`name`
			FROM tabItem AS t1
				INNER JOIN tabItem AS t2 ON t1.configurator_of = t2.`name`
				INNER JOIN `tabItem Variant Attribute` ON t2.`name` = `tabItem Variant Attribute`.parent
				INNER JOIN `tabItem Attribute` ON `tabItem Variant Attribute`.attribute = `tabItem Attribute`.`name`
			WHERE
				t1.`name` = %(item_code)s AND
				t1.has_configuration = 1""", args, as_list = 1)
	
	return query

# 2016-11-04 
@frappe.whitelist()
def get_item_attributes_values(item_code):
	template_item_code = frappe.db.get_value("Item", {"item_code":item_code}, "configurator_of")
	args = {'item_code': template_item_code}
	query = frappe.db.sql("""
			SELECT
				`tabItem Variant Attribute`.attribute,
				`tabItem Attribute Value`.attribute_value
			FROM
				`tabItem Variant Attribute`
			INNER JOIN `tabItem Attribute Value` ON `tabItem Variant Attribute`.attribute = `tabItem Attribute Value`.parent
			WHERE
				`tabItem Variant Attribute`.parent = %(item_code)s AND
				`tabItem Attribute Value`.abbr <> "_"
			ORDER BY
				`tabItem Variant Attribute`.idx ASC,
				`tabItem Attribute Value`.idx ASC""", args, as_list = 1)
	
	return query
	
# 2016-11-04 
@frappe.whitelist()
def create_batch_variants(configurator_of, batch_name):
	args = {'batch_name': batch_name}
	query = frappe.db.sql("""
			SELECT
				`tabConfigurator Batch Attribute`.attribute_name,
				`tabConfigurator Batch Attribute`.item_attribute_value
			FROM
				`tabConfigurator Batch`
			INNER JOIN `tabConfigurator Batch Attribute` ON `tabConfigurator Batch`.`name` = `tabConfigurator Batch Attribute`.parent
			WHERE
				`tabConfigurator Batch`.`name` = %(batch_name)s AND
				`tabConfigurator Batch Attribute`.selected = true
			ORDER BY
				`tabConfigurator Batch Attribute`.idx ASC""", args, as_list = 1)
	
	list_result={}
	template_item_code = frappe.db.get_value("Item", {"item_code":configurator_of}, "configurator_of")
	#if print_debug: frappe.errprint(configurator_of)
	#if print_debug: frappe.errprint(template_item_code)
	
	for attribute in query:
		list_result[attribute[0]]=[]
	
	for attribute in query:
		list_result[attribute[0]].append(attribute[1])

	sets_of_values = list(itertools.product(*list_result.values()))
	#if print_debug: frappe.errprint(sets_of_values)
	created_items = ""
	keys = list_result.keys()
	for set in sets_of_values:
		attribute_values = {}
		for i in range(len(keys)):
			attribute_values[keys[i]] = set[i]
		variant = create_variant_and_submit(template_item_code, attribute_values)
		created_items += variant.item_code + "\n\n"
		
	return created_items


# 2016-11-09 - JDLP
def make_variant_prices(item_code):
	if print_debug: frappe.errprint("make_variant_prices")
	if print_debug: frappe.errprint("item_code:" + item_code)
	
	item = frappe.get_doc('Item', item_code)
	template_item_code = frappe.db.get_value("Item", {"configurator_of":item.variant_of}, "item_code")
	if print_debug: frappe.errprint("variant_of:" + item.variant_of)
	if print_debug: frappe.errprint("variant_of:" + template_item_code)
	if item.variant_of:
		variant_price_lists = frappe.get_all('Variant Price List', fields=["price_list"], filters={'configurator': template_item_code})
			
		if print_debug: frappe.errprint(variant_price_lists)
		for variant_price_list in variant_price_lists:
			if print_debug: frappe.errprint(variant_price_list["price_list"])
			make_variant_price(variant_price_list["price_list"], item_code)
	
@frappe.whitelist()
def make_variant_price_from_item_code(item, method):
	make_variant_prices(item.item_code)		
	
# 2016-11-09 - JDLP
def make_variant_price(variant_price_list, item_code):
	if print_debug: frappe.errprint("make_variant_price")
	attribute_values = get_item_variant_attributes_values(item_code)
	if print_debug: frappe.errprint(attribute_values)
	args = {'parent': variant_price_list,
			'construction': 0,
			'species': 0,
			'flooring_grade': 0,
			'flooring_width': 0,
			'thickness' : 0,
	}
	for pair in attribute_values:
		if pair[2] in args.keys():
			args[pair[2]] = pair[1]
	if print_debug: frappe.errprint(args)
	query = frappe.db.get_value('Variant Price', args, 'rate')
	if print_debug: frappe.errprint(query)
	if (query):
		make_price_item(variant_price_list, item_code, query)
	
# 2016-11-09 - JDLP	
def make_price_item(price_list, item_code, rate):
	price_items = frappe.get_all('Item Price', filters={'price_list': price_list,
		'item_code': item_code}, fields=['name'])
	
	price_item = None
	if price_items:
		price_item = frappe.get_doc('Item Price', price_items[0]['name'])
		if print_debug: frappe.errprint("price_item=" + _(price_items))
		if print_debug: frappe.errprint("price_item=" + price_items[0]['name'])
		if print_debug: frappe.errprint("price_item=" + _(price_item))
	
	if price_item:
		if price_item.price_list_rate != rate:
			price_item.price_list_rate = rate
			price_item.save(True)
	else:
		price_item = frappe.new_doc("Item Price")
		price_item.item_code = item_code
		price_item.price_list = price_list
		price_item.price_list_rate = rate
		price_item.save(True)
		
# 2016-11-09 - JDLP
def make_variant_prices_v2(item_code):
	if print_debug: frappe.errprint("make_variant_prices")
	if print_debug: frappe.errprint("item_code:" + item_code)
	
	item = frappe.get_doc('Item', item_code)
	template_item_code = frappe.db.get_value("Item", {"configurator_of":item.variant_of}, "item_code")
	if print_debug: frappe.errprint("variant_of:" + item.variant_of)
	if print_debug: frappe.errprint("variant_of:" + template_item_code)
	if item.variant_of:
		variant_price_lists = frappe.get_all('Variant Price List', fields=["price_list"], filters={'configurator': template_item_code})
			
		if print_debug: frappe.errprint(variant_price_lists)
		for variant_price_list in variant_price_lists:
			if print_debug: frappe.errprint(variant_price_list["price_list"])
			make_variant_price_v2(variant_price_list["price_list"], item_code)

# 2016-11-09 - JDLP
def make_variant_price_v2(variant_price_list, item_code):
	print_debug=False
	attribute_values = get_item_variant_attributes_values(item_code)
	fields = frappe.db.get_table_columns('Variant Price')
	variant_price_list_doc = frappe.get_doc('Variant Price List', variant_price_list)
	
	if print_debug: frappe.errprint(attribute_values)
	if print_debug: frappe.errprint(fields)
	if print_debug: frappe.errprint(variant_price_list_doc)
	
	query = u" SELECT `tabVariant Price`.rate"
	query += "\n FROM `tabVariant Price List`"
	query += "\n INNER JOIN `tabVariant Price` ON `tabVariant Price List`.`name` = `tabVariant Price`.parent"
	query += "\n WHERE"
	query += "\n `tabVariant Price List`.price_list = '" + variant_price_list_doc.price_list + "' AND"
	query += "\n `tabVariant Price List`.configurator = '" + variant_price_list_doc.configurator + "' "
	
	for pair in attribute_values:
		if pair[2] in fields:
			query += "\n AND (`tabVariant Price`." + pair[2] + " = '" + pair[1].replace("'","''") + "'"
			query += " OR `tabVariant Price`." + pair[2] + " IS NULL " 
			query += " OR `tabVariant Price`." + pair[2] + u" = 'ANY' "
			query += " OR `tabVariant Price`." + pair[2] + u" = 'TOUS' )"
			
	query += " ORDER BY `tabVariant Price List`.priority DESC"
	
	if print_debug: frappe.errprint(query)
	
	rate = frappe.db.sql(query)
	if print_debug: frappe.errprint(rate)
	if (rate):
		make_price_item_v2(variant_price_list_doc, item_code, rate[0][0])
	

# 2016-11-09 - JDLP	
def make_price_item_v2(variant_price_list, item_code, rate):
	if print_debug: frappe.errprint("make_price_item(" + _(variant_price_list) + ','  + _(item_code) + ','  + _(rate) + ')')
	if print_debug: frappe.errprint("price_list:" + _(variant_price_list.price_list))
	
	price_items = frappe.get_all('Item Price', filters={'price_list': variant_price_list.price_list,
		'item_code': item_code}, fields=['name'])
	
	price_item = None
	if price_items:
		price_item = frappe.get_doc('Item Price', price_items[0]['name'])
	
	if price_item:
		if price_item.price_list_rate != rate:
			price_item.price_list_rate = rate
			price_item.variant_price_list = variant_price_list.name
			price_item.save(True)
			
	else:
		price_item = frappe.new_doc("Item Price")
		price_item.item_code = item_code
		price_item.price_list = variant_price_list.price_list
		price_item.price_list_rate = rate
		price_item.variant_price_list = variant_price_list.name
		price_item.save(True)
		
	if print_debug: frappe.errprint("price_item=" + _(price_items))
