// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Quotation",{	
	onload : function(frm) {
		// Permet d'assigner l'entete de lettre a la commande de vente selon le vendeur selectionne.
		cur_frm.add_fetch('sales_person','letter_head','letter_head')
	},
	refresh : function(frm) {		
		LoadAttributesValues(false, frm, "items")
		
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
	qo_name : function(frm, cdt, cdn){
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
	},
	setup : function(frm) {
		frm.fields_dict.items.grid.get_field('template').get_query = function() {
			return erpnext.queries.item({item_group : "Configurateur"});
		};
	}
});

frappe.ui.form.on("Quotation Item",{
	template : function(frm, cdt, cdn){
		SetConfiguratorOf(false, frm, cdt, cdn)		
	},
	create_variant : function(frm, cdt, cdn){
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(false, frm, cdt, cdn, true, true)
	},
	reconfigure : function(doc, cdt, cdn) {
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	},
	configurator_of : function(frm, cdt, cdn) {	
		if (frm.doc.shipper){
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					'doctype': 'Customer',
					'filters': {'name': frm.doc.shipper},
					'fieldname': [
						'milling'
					]
				},
				callback: function(r) {
					if (!r.exc) {	
						if (r.message.milling) {
							ShowHideAttributes(false, frm, cdt, cdn, false, true, r.message.milling)
						}
						else {
							ShowHideAttributes(false, frm, cdt, cdn, false, true)
						}
					}
				}
			});			
		}
		else {
			ShowHideAttributes(false, frm, cdt, cdn, false, true)
		}
	}, 
	construction : function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];		
		if (row.construction == "Massif"){
			row.thickness = '3/4"';
			row.length = "1' à 7'";
			console.log("1' à 7'")
			refresh_field("items");
		}
		if (row.construction == "Hardwood"){
			row.thickness = '3/4"';
			row.length = '1\' to 7\'';
			console.log('1\' to 7\'')
			refresh_field("items");
		}
		if (row.construction.toString().substring(0,10) == "Ingénierie" ){
			row.thickness = __('5/8"');
			row.length = "1' à 8'";
			console.log("1' à 8'")
			refresh_field("items");
		}
		if (row.construction.toString().substring(0,10) == "Engineered"){
			row.thickness = '5/8"';
			row.length = '1\' to 8\'';
			console.log('1\' to 8\'')
			refresh_field("items");
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
        	
    }

    if (printDebug) console.log(__("END AssignDefaultValues"));
}


//////////////////////////// Fin Methodes /////////////////////////////
///////////////////////// FIN Code specifique /////////////////////////
///////////////////////////////////////////////////////////////////////
