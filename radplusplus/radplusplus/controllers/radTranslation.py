# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe, os, re, codecs, json
from frappe.model.utils import render_include, InvalidIncludePath
from frappe.utils import strip
from jinja2 import TemplateError
import itertools, operator


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