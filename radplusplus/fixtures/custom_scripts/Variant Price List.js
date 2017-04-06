// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on('Variant Price List', {
	onload: function(frm) {

	},
	refresh: function(frm) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.	
		LoadAttributesValues(false, frm, "variants")
	}
});