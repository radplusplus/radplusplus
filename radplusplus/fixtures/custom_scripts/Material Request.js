// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Material Request",{
	"refresh": function(frm) {	
		// 2016-10-17 - JDLP
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(true, frm, "items", false)
	}
});

frappe.ui.form.on("Material Request Item",{
	"item_code": function(frm, cdt, cdn) {	
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(true, frm, cdt, cdn, false, true)
	},
	"create_variant": function(frm, cdt, cdn) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(true, frm, cdt, cdn, true, false)
	},
	"reconfigure": function(doc, cdt, cdn) {
		// 2016-11-01 - JDLP
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(true, doc, cdt, cdn)
	}
});

	
///////////////////////////// FIN Handles /////////////////////////////
///////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////
