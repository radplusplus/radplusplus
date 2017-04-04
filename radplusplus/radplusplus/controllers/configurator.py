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
import operator
from frappe.utils.jinja import render_template

print_debug = False

@frappe.whitelist()
def get_configurator_attributes_values(user_name):
	frappe.errprint("get_configurator_attributes_values")
	if print_debug: frappe.errprint("get_configurator_attributes_values")
	if print_debug: frappe.errprint("user:" + user_name)
	lang = get_user_lang(user_name)
	update_user_translations(lang)
	attributes_values = get_configurator_attributes()
	result = groupe_attributes_and_translate(attributes_values)
		
	if print_debug: frappe.errprint("result:" + cstr(result))
	
	return result
	
@frappe.whitelist()
def get_required_attributes_fields(item_code):
	args = {'item_code': item_code}
	query = frappe.db.sql("""
			SELECT
				`tabItem Attribute`.`name`,
				`tabItem Attribute`.`field_name`
			FROM tabItem AS t1
				INNER JOIN tabItem AS t2 ON t1.configurator_of = t2.`name`
				INNER JOIN `tabItem Variant Attribute` ON t2.`name` = `tabItem Variant Attribute`.parent
				INNER JOIN `tabItem Attribute` ON `tabItem Variant Attribute`.attribute = `tabItem Attribute`.`name`
			WHERE
				t1.`name` = %(item_code)s AND
				t1.has_configuration = 1""", args, as_list = 1)
	
	return query
	
@frappe.whitelist()
def get_item_variant_attributes_values(user_name, item_code):
	args = {'item_code': item_code}
	query = frappe.db.sql("""
			SELECT
			`tabItem Attribute`.field_name,
			`tabItem Variant Attribute`.attribute_value
			FROM
			`tabItem Variant Attribute`
			INNER JOIN `tabItem Attribute` ON `tabItem Variant Attribute`.attribute = `tabItem Attribute`.`name`
			WHERE
			`tabItem Variant Attribute`.parent = %(item_code)s
			ORDER BY
			`tabItem Variant Attribute`.idx ASC""", args, as_list = 1)
	update_user_translations(get_user_lang(user_name))
	frappe.errprint("query:" + cstr(query))
	rows = []
	for q in query:
		rows.append((q[0],_(q[1])))
	
	frappe.errprint("rows:" + cstr(rows))
	return rows
	
@frappe.whitelist()
def get_attributes_values(attribute):
	args = {'attribute': attribute}
	query = frappe.db.sql("""
			SELECT
			`tabItem Attribute Value`.parent,
			`tabItem Attribute Value`.attribute_value
			FROM
			`tabItem Attribute Value`
			WHERE
			`tabItem Attribute Value`.parent = %(attribute)s""", args, as_list = 1)
	
	return query
	
def get_user_lang(user_name):
	lang = frappe.db.get_value("User", user_name, "language")
	if print_debug: frappe.errprint("lang:" + lang)
	return lang

def update_user_translations(lang):
	from frappe.translate import get_user_translations
	if print_debug: frappe.errprint(_("get_user_translations:"))
	
	#Clé pour ne pas refaire le traitement
	key = 'rad_translation_update'
	
	#Cet appel est necessaire pour loader le dictionnaire au moins une fois par frappe.
	load = _(key)
		
	#Obtenir les valeurs actuelles
	out = get_user_translations(lang)
	if not out.has_key(key) or out[key] != lang:
		# pour chaque enregistrement dans la table de translation (fr)
		for t in frappe.db.get_values("Translation",filters={'language_code' : 'fr'}, fieldname = "*"):
			if print_debug: frappe.errprint("source_name:" + t['source_name'] + ", target_name:" + t['target_name'])
			
			#renverser le dictionnnaire si l'utilateur est en "en"
			#source_name:Width in inches, target_name:Largeur en pouce
			if (lang == 'en'):
				out[t['target_name']] = t['source_name']
				if print_debug: frappe.errprint(t['target_name'] + ":" + t['source_name'])
			else:
				out[t['source_name']] = t['target_name']
				if print_debug: frappe.errprint(t['source_name'] + ":" + t['target_name'])
				
		frappe.local.lang_full_dict.update(out)
		out[key] = lang

@frappe.whitelist()
def get_configurator_attributes():
	query = frappe.db.sql("""
	SELECT
		`tabItem Attribute`.field_name,
		`tabItem Attribute Value`.attribute_value
		FROM
		`tabItem Attribute Value`
		INNER JOIN `tabItem Attribute` ON `tabItem Attribute`.`name` = `tabItem Attribute Value`.parent
		ORDER BY
		`tabItem Attribute`.field_name DESC,
		`tabItem Attribute Value`.ordering ASC,
		`tabItem Attribute Value`.attribute_value ASC""")
		
	#if print_debug: frappe.errprint("configurator_attributes:" + cstr(query))
	
	return query
	
def groupe_attributes_and_translate(attributes_values):

	it = itertools.groupby(attributes_values, operator.itemgetter(0))
	data = {}
	for key, subiter in it:
		list = []
		for item in subiter:
			#Tuple of value and translation
			t = (item[1], _(item[1]))
			frappe.errprint(t)
			list.append(t)
		data[key] = list
	return data
	
	
	
	
	
	