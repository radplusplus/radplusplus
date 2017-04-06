// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////
frappe.ui.form.on("Production Order",{
	"onload": function(frm) {		
		// 2017-03-28 - RENMAI
		//Permet d'assigner le client l'ordre de fabrication selon la commande de vente sélectionnée.
		frappe.db.get_value("Sales Order", { name: cur_frm.doc.sales_order },
			"customer", function(data){
		cur_frm.set_value("customer", data.customer); });
	}
});