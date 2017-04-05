// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Sales Order",{
	"onload": function(frm) {
		console.log(__("Custom Script Fixture"));
		
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
	},
	
	"refresh": function(frm) {
		console.log(__("Custom Script Fixture"));
	}
});

// 2016-09-17 - JDLP
// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
frappe.ui.form.on("Sales Order Item", "item_code", function(frm, cdt, cdn) {
    ShowHideAttributes(false, frm, cdt, cdn, false, false), AssignDefaultValues(false, frm, cdt, cdn)
});

// 2016-10-17 - JDLP
// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
frappe.ui.form.on("Sales Order Item", "create_variant", function(frm, cdt, cdn) {
    CreateItemVariant(false, frm, cdt, cdn, true, false)
});

// 2016-11-01 - JDLP
// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
frappe.ui.form.on("Sales Order Item", "reconfigure", function(doc, cdt, cdn) {
    ReconfigurerItemVariant(false, doc, cdt, cdn)
});
///////////////////////////// FIN Handles /////////////////////////////

////////////////////////////// Methodes ///////////////////////////////
// 2016-10-26 - JDLP
// Copier les valeurs de d'autres DocTypes
cur_frm.add_fetch("customer", "default_warehouse", "default_warehouse");


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

// 2017-02-28 - RM
// Script fonctionnel
// Permet d'assigner l'entete de lettre a la commande de vente selon le vendeur selectionne.
cur_frm.add_fetch('sales_person','letter_head','letter_head')

// 2017-03-06 - JDLP
// Assigne le "rate" lorsque la valeur du "template_service" change.
frappe.ui.form.on("Sales Order Item", "template_service", function(frm, cdt, cdn) {
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
});

//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////
