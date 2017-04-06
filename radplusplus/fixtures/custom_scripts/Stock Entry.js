// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code spécifique ///////////////////////////
/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Stock Entry",{
	refresh: function(frm) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
	}
});

frappe.ui.form.on("Stock Entry Detail",{
	item_code: function(frm, cdt, cdn) {
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(false, frm, cdt, cdn, true, false)
	},
	
	create_variant: function(frm, cdt, cdn) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(false, frm, cdt, cdn, true, true)
	}

	reconfigure: function(doc, cdt, cdn) {
		// 2016-11-01 - JDLP
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	}
});

///////////////////////////// FIN Handles /////////////////////////////

////////////////////////////// Méthodes ///////////////////////////////
// 2016-10-24 - JDLP
// Script fonctionnel
// Permet d'assigner les valeurs par défaut
// Ce script doit etre present dans tous les doc utilisant le configurateur
function AssignDefaultValues(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__("AssignDefaultValues"));
    if (printDebug) console.log(__("Debug mode ON"));

    var soi = locals[cdt][cdn];
    if (soi && soi.item_code) {
		// 2016-11-02 - JDLP - 
        StockEntryDetailOnItemChange(printDebug, frm, cdt, cdn);
    }
    if (printDebug) console.log(__("END AssignDefaultValues"));
}

// 2016-11-22 - JDLP
// J'ai déplacé le code de "erpnext\stock\doctype\stock_entry\stock_entry.js" "cur_frm.cscript.item_code"
// Ceci rentrait en conflit avec le configurateur
function StockEntryDetailOnItemChange(printDebug, frm, cdt, cdn){
	if (printDebug) console.log(__("StockEntryDetailOnItemChange"));
	var d = locals[cdt][cdn];			
	if(d.item_code) {
		args = {
			'item_code'			: d.item_code,
			'warehouse'			: cstr(d.s_warehouse) || cstr(d.t_warehouse),
			'transfer_qty'		: d.transfer_qty,
			'serial_no	'		: d.serial_no,
			'bom_no'			: d.bom_no,
			'expense_account'	: d.expense_account,
			'cost_center'		: d.cost_center,
			'company'			: cur_frm.doc.company
		};
		return frappe.call({
			doc: cur_frm.doc,
			method: "get_item_details",
			args: args,
			callback: function(r) {
				if(r.message) {
					var d = locals[cdt][cdn];
					$.each(r.message, function(k, v) {
						d[k] = v;
					});
					refresh_field("items");
				}
			}
		});
	}	
}

//////////////////////////// Fin Méthodes /////////////////////////////
///////////////////////// FIN Code spécifique /////////////////////////
///////////////////////////////////////////////////////////////////////

	