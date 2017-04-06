///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Purchase Order",{
	"onload":  function(frm) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		cur_frm.set_value("letter_head", "Myrador - ERPNext");
		cur_frm.set_value("tc_name", "Bon d'achat"); 
		cur_frm.set_value("ship_to_address", "FOB Myrador");
	},
	
	"refresh":  function(frm) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "refresh" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
	},
	
	"ship_to_address": function(frm, cdt, cdn) {
		// 2017-01-25 - RENMAI
		// Permet d'assigner la description complete de l'adresse de livraison
		return frm.call({
			method: "frappe.geo.doctype.address.address.get_address_display",
			args: {
				"address_dict": frm.doc.ship_to_address
			},
			callback: function(r) {
				console.log(__(r.message));
				if(r.message)
					frappe.model.set_value(cdt,cdn,"ship_to_address_display", r.message);
			}
		});
	}
});

frappe.ui.form.on("Purchase Order Item",{
	"item_code": function(frm, cdt, cdn){
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(false, frm, cdt, cdn, false, false), AssignDefaultValues(false, frm, cdt, cdn)
	},
	
	"create_variant": function(frm, cdt, cdn){
		// 2016-10-17 - JDLP
		// Lancer la fonction "CreateItemVariant" lorque le bouton "create_variant" est active.
		CreateItemVariant(true, frm, cdt, cdn, true, false)
	},

	"reconfigure": function(doc, cdt, cdn) {
		// 2016-11-01 - JDLP
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	}
});
///////////////////////////// FIN Handles /////////////////////////////

////////////////////////////// Methodes ///////////////////////////////
// 2016-10-24 - JDLP
// Permet d'assigner les valeurs par defaut
function AssignDefaultValues(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__("AssignDefaultValues"));
    if (printDebug) console.log(__("Debug mode ON"));

    var soi = locals[cdt][cdn];
    if (soi && soi.item_code) {
        	
    }

    if (printDebug) console.log(__("END AssignDefaultValues"));
}

//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////
