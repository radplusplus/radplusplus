// Copyright (c) 2016, RAD plus plus inc. and contributors
// For license information, please see license.txt

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Opportunity",{
	refresh : function(frm) {	
		LoadAttributesValues(false, frm, "items")
	},
	setup : function(frm) {
		frm.fields_dict.items.grid.get_field('template').get_query = function() {
			return erpnext.queries.item({item_group : "Configurateur"});
		};
	}
});

frappe.ui.form.on("Opportunity Item",{
	template : function(frm, cdt, cdn){
		SetConfiguratorOf(false, frm, cdt, cdn)		
	},
	create_variant : function(frm, cdt, cdn) {
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
///////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

