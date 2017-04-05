// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

/////////////////////////////// Handles ///////////////////////////////
// 2017-04-05 - RENMAI
// définir les valeurs par défaut.
frappe.ui.form.on("Sales Order",{
	"onload": function(frm) {
		console.log(__("Custom Script Fixture"));
	},
	
	"refresh": function(frm) {
		console.log(__("Custom Script Fixture"));
	}
	//cur_frm.add_fetch("lead","language","language")
});