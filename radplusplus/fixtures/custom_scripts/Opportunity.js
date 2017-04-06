// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Opportunity",{
	"refresh": function(frm) {	
		// 2016-10-17 - JDLP
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items", false)
	}
});

frappe.ui.form.on("Opportunity Item",{
	"item_code": function(frm, cdt, cdn) {	
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(false, frm, cdt, cdn, false, true)
	},
	"create_variant": function(frm, cdt, cdn) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(false, frm, cdt, cdn, true, false)
	},
	"reconfigure": function(doc, cdt, cdn) {
		// 2016-11-01 - JDLP
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	}
});

	
///////////////////////////// FIN Handles /////////////////////////////
///////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

