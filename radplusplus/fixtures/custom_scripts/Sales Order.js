// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////



/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Sales Order",{
	onload : function(frm) {
		cur_frm.add_fetch("customer", "language", "language");
		cur_frm.add_fetch("customer", "default_warehouse", "default_warehouse");
		// Permet d'assigner l'entete de lettre a la commande de vente selon le vendeur selectionne.
		cur_frm.add_fetch('sales_person','letter_head','letter_head')
	},
	
	refresh : function(frm) {
		// Lancer la fonction "LoadAttributesValues" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
		
		// Retrouver la valeur de language
		if (frm.doc.customer){
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
	},
	setup : function(frm) {
		frm.fields_dict.items.grid.get_field('template').get_query = function() {
			return erpnext.queries.item({item_group : "Configurateur"});
		};
	}
});

frappe.ui.form.on("Sales Order Item",{
	template : function(frm, cdt, cdn){
		SetConfiguratorOf(false, frm, cdt, cdn)		
	},
	create_variant : function(frm, cdt, cdn) {
		// Lancer la fonction "CreateItemVariant"lorque le bouton "create_variant" est active.
		CreateItemVariant(false, frm, cdt, cdn, true, false)
	},
	reconfigure : function(doc, cdt, cdn) {
		// Lancer la fonction "ReconfigurerItemVariant" lorque le bouton "reconfigure" est active.
		ReconfigurerItemVariant(false, doc, cdt, cdn)
	},
	template_service : function(frm, cdt, cdn) {
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
