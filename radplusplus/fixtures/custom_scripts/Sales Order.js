// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

// 2016-10-26 - JDLP
// Copier les valeurs de d'autres DocTypes
cur_frm.add_fetch("customer", "default_warehouse", "default_warehouse");

// 2017-02-28 - RM
// Script fonctionnel
// Permet d'assigner l'entete de lettre a la commande de vente selon le vendeur selectionne.
cur_frm.add_fetch('sales_person','letter_head','letter_head')

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Sales Order",{
	"onload": function(frm) {
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
		cur_frm.add_fetch("customer", "language", "language");
	},
	
	"refresh": function(frm) {
		cur_frm.add_fetch("customer", "language", "language");
		
		// Retrouver la valeur de language
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                "doctype": "Customer",
                "filters": {
                    "name": frm.doc.customer
                },
                "fieldname": ["language"]
            },
            callback: function(res) {
				cur_frm.set_value('language', res.message.language);
				refresh_field("language");
            }
        });
	}
});

frappe.ui.form.on("Sales Order Item",{
	"item_code": function(frm, cdt, cdn) {
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(false, frm, cdt, cdn, false, false), AssignDefaultValues(false, frm, cdt, cdn)
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
	},
	"template_service": function(frm, cdt, cdn) {
		// 2017-03-06 - JDLP
		// Assigne le "rate" lorsque la valeur du "template_service" change.
		var printDebug = true;
		var soi = locals[cdt][cdn];
		if (printDebug) console.log(__("soi.template_service:" + soi.template_service));
		if (soi.template_service){
			frappe.call({
					method: "myrador.myrador.doctype.template_service.template_service.get_total_rate",
					args: {"customer": frm.doc.customer, "name": soi.template_service},
					callback: function(res) {
						if (res.message != null){
							console.log("res.message:" + res.message);
							frappe.model.set_value(soi.doctype, soi.name, "rate", res.message);
							refresh_field("rate");
						}
					}
			})
		}
	}
});	
	
///////////////////////////// FIN Handles /////////////////////////////

////////////////////////////// Methodes ///////////////////////////////

// 2016-10-24 - JDLP
// Script fonctionnel
// Permet d'assigner les valeurs par defaut
function AssignDefaultValues(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__("AssignDefaultValues"));

    var soi = locals[cdt][cdn];
    if (soi && soi.item_code) {
        // S'il n'y a aucune valeur, assigner la valeur du warehouse du client dans la ligne
		if (printDebug) console.log(__("warehouse:" + frm.cur_grid.doc.warehouse));
		if (!frm.cur_grid.doc.warehouse) {
			if (printDebug) console.log(__("warehouse:" + frm.doc.default_warehouse));
			frm.cur_grid.doc.warehouse = frm.doc.default_warehouse;
			if (printDebug) console.log(__("warehouse:" + frm.cur_grid.doc.warehouse));
			refresh_field("warehouse");
		}		
    }

    if (printDebug) console.log(__("END AssignDefaultValues"));
}

//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////
