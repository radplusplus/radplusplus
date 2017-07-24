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
import myrador

########################## Section Rad++ ##########################
print_debug = True

		
@frappe.whitelist()
def make_description_from_template(template):
	
	items_list = frappe.get_list(
		"Item",
		filters={'variant_of': template},
		fields=['name','variant_of']
	)
	
	if print_debug: frappe.msgprint("len(items_list):" + str(len(items_list)))
	
	from frappe.utils.background_jobs import enqueue
	enqueue(regenerate_description_from_item_list, items_list=items_list) 
		
@frappe.whitelist()
def regenerate_description_from_item_list(items_list):	
	if len(items_list) > 0 :
		for item in items_list:
			doc_item = frappe.get_doc("Item",item.name)
			if doc_item:
				make_variant_description(doc_item) 
				doc_item.save(True)
		frappe.msgprint("Description créés.")
	else:
		frappe.msgprint("Aucun variant de trouvé.")	

@frappe.whitelist()
def regenerate_description_from_item_code(item_code):	
	
	doc_item = frappe.get_doc("Item",item_code)
	if doc_item:
		make_variant_description(doc_item) 
		doc_item.save(True)			

@frappe.whitelist()
def item_before_insert(item, args):
	if print_debug: frappe.errprint("item_before_insert :" + cstr(item))
	make_variant_description(item)

@frappe.whitelist()
def create_variant(item, args):
	if isinstance(item, basestring):
		item = frappe.get_doc('Item', item)
		
	start_time = time.time()
	variant = erpnext.controllers.item_variant.create_variant(item.item_code, args)
	if print_debug: frappe.errprint("--- create_variant %s seconds ---" % (time.time() - start_time))

	# RENMAI - 2017-07-07 - Permet de copier la propriété uninheritable lors de la création d'un variant.
	for d in variant.attributes:
		if print_debug: frappe.errprint("d.attribute : " + d.attribute)
		uninheritable = frappe.get_value("Item Variant Attribute", {"parent":item.item_code,"attribute":d.attribute},"uninheritable")
		if uninheritable:			
			if print_debug: frappe.errprint("uninheritable : " + cstr(uninheritable))
			d.uninheritable = uninheritable
	
	from radplusplus.radplusplus.doctype.item_variant_hashcode.item_variant_hashcode import create_from_item
	create_from_item(item, args)
	
	return variant


@frappe.whitelist()
def get_variant(template, args, variant=None):
	if print_debug: frappe.errprint("radpp get_variant ")
	"""Validates Attributes and their Values, then looks for an exactly matching Item Variant

		:param item: Template Item
		:param args: A dictionary with "Attribute" as key and "Attribute Value" as value
	"""
	if isinstance(args, basestring):
		args = json.loads(args)

	if not args:
		frappe.throw(_("Please specify at least one attribute in the Attributes table"))
	
	if print_debug: frappe.errprint(" before import " )
	from radplusplus.radplusplus.doctype.item_variant_hashcode.item_variant_hashcode import get_item_from_attribute_value_list
	
	if print_debug: frappe.errprint(" after import " )
	item_code = get_item_from_attribute_value_list(template, args.values())
	if print_debug: frappe.errprint(" item_code : " + cstr(item_code))
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
	
	if print_debug: frappe.errprint("variant : " + cstr(variant.name))
	if variant.variant_of is not None:
		template = frappe.get_doc("Item", variant.variant_of)
		variant.set('language',[])
		for template in template.description_template:
			jinjaTemplate = template.description
			values = {}
				
			if print_debug: frappe.errprint("template.language : " + template.language)
			
			for d in variant.attributes:
				attribute = frappe.get_doc("Item Attribute", d.attribute)
				jinjaTemplate = jinjaTemplate.replace("{{"+d.attribute, "{{"+attribute.field_name)
				target_field = "target_name"
				source_field = "source_name"
				template_language = template.language
				if template.language == "en":
					target_field = "source_name"
					source_field = "target_name"
					template_language = "fr"
					
				# if print_debug: frappe.errprint("d.attribute : " + d.attribute)
				# if print_debug: frappe.errprint("attribute.field_name : " + attribute.field_name)
				# if print_debug: frappe.errprint("d.attribute_value : " + d.attribute_value)
				
				filters = {'language_code': template_language,source_field:d.attribute_value}
				target_name = frappe.db.get_value("Translation",filters,target_field,None,False,False,False)
				values[attribute.field_name] = target_name or d.attribute_value
				# if print_debug: frappe.errprint("target_name : " + cstr(target_name))
				# if print_debug: frappe.errprint("jinjaTemplate : " + jinjaTemplate)
				
			if print_debug: frappe.errprint("jinjaTemplate : " + jinjaTemplate)
			if print_debug: frappe.errprint("values : " + cstr(values))
			description = render_template(jinjaTemplate, values)
			
			if print_debug: frappe.errprint("description : " + description)
			
			filters = {"parent": variant.name,
							"parentfield": "language",
							"parenttype": "Item",
							"language": template.language}
			name = frappe.db.get_value("Item Language",	filters,"name",None,False,False,False)
			language_description = None
			# for d in self.language:
				# if d.language = template.language
					# d.db_set('description', description, update_modified = False)
			# if name:
				# if print_debug: frappe.errprint("if name")
				# language_description = frappe.get_doc("Item Language", name)
				# frappe.db.set_value("Item Language", name, "description", description)
				
			# if not language_description:
				# if print_debug: frappe.errprint("if not language_description")
				# values = filters
				# values["doctype"] = "Item Language"
				# language_description = frappe.get_doc(values)
				# language_description.description = description
				# variant.append("language", language_description)
				
			values = filters
			values["doctype"] = "Item Language"
			language_description = frappe.get_doc(values)
			language_description.description = description
			variant.append("language", language_description)

# 2016-08-23 Ajoute par Antonio pour creer et faire le submit 
@frappe.whitelist()
def create_variant_and_submit(template_item_code, args):
	print_debug = False
	if print_debug: frappe.errprint("--- create_variant_and_submit ---")
	
	start_time = time.time()
	
	if isinstance(args, basestring):
		args = json.loads(args)
	
	if print_debug: frappe.errprint(template_item_code)
	#if print_debug: frappe.errprint(args)
	
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
		variant = create_variant(template, args)
		frappe.errprint("--- create_variant %s seconds ---" % (time.time() - start_time4))
		
		#Tenter de trouver un item avec le meme code
		#duplicate_item_code = frappe.db.sql_list("""select item_name from `tabItem` item where item_name=%s)""",variant.item_code)
		
		start_time5 = time.time()
		if not frappe.db.exists("Item", variant.item_code):
			variant.docs = 1
			variant.save(True)
			frappe.errprint("--- variant.save(True) ---")
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
# Permet de transferer la valeur d'un champ de type Doc_Type en Item Atribute Value qui n'existe pas dans la liste des attributs sélectionnés.
# Fonctionnement:
# Si un valeur n'existe pas dans Attribute Value
# Recuperer le name 
def create_missing_attributes_values(template, args):
	# Pour chacun des pairs [parent:attribute_value]
	for parent, attribute_value in args.items():
		# Si l'item_attribute_value n'existe pas
		
		create_attribute_value_from_doctype(parent, attribute_value)
					
# 2017-06-20 - JDLP
# Permet de transferer la valeur d'un champ de type Doc_Type en Item Atribute Value
# Fonctionnement:
# Si un valeur n'existe pas dans Attribute Value
# Recuperer le name 
@frappe.whitelist()
def create_attribute_value_from_doctype(parent, attribute_value):
		
	if get_item_attribute_value(parent, attribute_value) is None:
		# Name = abreviation!
		# Si le parent correspond a une table
		doc_name = cstr(parent)
		table_exist = frappe.db.table_exists(doc_name)
		
		# Retrouver le record
		if table_exist:
			doc = frappe.get_doc(doc_name, attribute_value)
			abbr = attribute_value
			if doc.abbr:
				abbr = doc.abbr
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
			`tabItem Attribute`.field_name,
			`tabItem Variant Attribute`.uninheritable
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

