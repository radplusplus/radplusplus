///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

// 2017-02-28 - RENMAI
// Permet d'assigner l'entete de lettre à la commande de vente selon le vendeur selectionne.
cur_frm.add_fetch('sales_person','letter_head','letter_head')

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Quotation",{
	"onload": function(frm) {		
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
	},
	
	"refresh": function(frm) {
		// RENMAI - 2017-04-05 - Gestion de la langue d'impression.
		// Retrouver la valeur de language du client ou du prospect.
		if (frm.doc.quotation_to == "Customer" && frm.doc.customer){
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
		else if (frm.doc.quotation_to == "Lead"){
			// Retrouver la valeur de language
			console.log(__("frm.doc.lead : " + frm.doc.lead));
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					"doctype": "Lead",
					"filters": {
						"name": frm.doc.lead
					},
					"fieldname": ["language"]
				},
				callback: function(res) {
					cur_frm.set_value('language', res.message.language);
					refresh_field("language");
				}
			});
		} 
	},
	// 2016-12-02 - JDLP
	// Actualise la valeur du texte options.
	"qo_name": function(frm, cdt, cdn){
		var soi = locals[cdt][cdn];
		if (soi && soi.qo_name) {
			frappe.call({
			method: "frappe.client.get_value",
			args: {
				"doctype": "Quotation Options",
				"fieldname": ["options"],
				"filters": {
					"name": soi.qo_name
				}
			},
			callback: function(res) {
				soi.options = res.message.options;
				refresh_field("options");
			}});
		}
	}
});

frappe.ui.form.on("Quotation Item",{
	"item_code": function(frm, cdt, cdn) {	
		// 2016-09-17 - JDLP
		// Lancer la fonction "ShowHideAttributes" quand l'item_code change.
		ShowHideAttributes(false, frm, cdt, cdn, false, false), AssignDefaultValues(false, frm, cdt, cdn)
	},
	"create_variant": function(frm, cdt, cdn){
		// 2016-10-17 - JDLP
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(false, frm, cdt, cdn, false, false)
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
// Script fonctionnel
// Permet d'assigner les valeurs par defaut
function AssignDefaultValues(printDebug, frm, cdt, cdn) {
    if (printDebug) console.log(__("AssignDefaultValues"));

    var soi = locals[cdt][cdn];
    if (soi && soi.item_code) {
        	
    }

    if (printDebug) console.log(__("END AssignDefaultValues"));
}


//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////
