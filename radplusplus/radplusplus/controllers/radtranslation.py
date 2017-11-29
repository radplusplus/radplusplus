#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe, os, re, codecs, json
from frappe.model.utils import render_include, InvalidIncludePath
from frappe.utils import strip
from jinja2 import TemplateError
import itertools, operator

print_debug = False

@frappe.whitelist()
def get_user_translations(lang):
	raise ValueError("Hook get_user_translations")
	out = frappe.cache().hget('lang_user_translations', lang)
	if out is None:
		out = {}
		for fields in frappe.get_all('Translation',	fields= ["source_name", "target_name"],filters={'language_code': 'fr'}):
			if (lang == "en") 
				{out.update({fields.target_name: fields.source_name})}
			else
				{out.update({fields.source_name: fields.target_name})}
		frappe.cache().hset('lang_user_translations', lang, out)

	return out
	
@frappe.whitelist()
def update_translation_from_custom_doc(custom_doc, field_fr, field_en, data_fr, data_en):
	
	"""crée et met à jour les traductions en/fr.

	:param custom_doc: Document personnalisé d'où provient les traductions.
	:param data_fr: Terme en français.
	:param data_en: Terme en anglais.

	Pour que la tradcution fonctionne, vous devez ajouter l'appel de la fonction `update_translation_from_custom_doc` dans la méthode save du document personnalisé 
	
	"""
	
	# Dans le cas de l'enregistrement du document.
	if custom_doc.docstatus == 0 :
		translation_doc = frappe.db.get_value("Translation", {"source_name": data_en, "target_name" : data_fr }, "name")
		if !translation_doc:
			uo = frappe.new_doc("Translation")				
			uo.update({"source_name": data_en, "target_name" : data_fr })
			uo.save(ignore_permissions = True)
		
	# Dans le cas d'une mise à jour ou 
	
	if custom_doc.docstatus == 1 :
		server_fr = frappe.db.get_value(custom_doc.doc_type,  {"name": custom_doc.doc_name }, field_fr)
		server_en = frappe.db.get_value(custom_doc.doc_type,  {"name": custom_doc.doc_name }, field_en)
		if server_fr:
			if print_debug: frappe.errprint("server_fr : " + server_fr)
		if server_en:
			if print_debug: frappe.errprint("server_en : " + server_en)
		if server_fr != data_fr or server_en != data_en:
			translation_doc = frappe.db.get_value("Translation", {"source_name": data_en, "target_name" : data_fr }, "name")
			if translation_doc:
				frappe.delete_doc("Translation", translation_doc)
			translation_doc = frappe.new_doc("Translation")				
			translation_doc.update({"source_name": data_en, "target_name" : data_fr })
			translation_doc.save(ignore_permissions = True)
		else:
			translation_doc = frappe.db.get_value("Translation", {"source_name": data_en, "target_name" : data_fr }, "name")
			if !translation_doc:
				uo = frappe.new_doc("Translation")				
				uo.update({"source_name": data_en, "target_name" : data_fr })
				uo.save(ignore_permissions = True)