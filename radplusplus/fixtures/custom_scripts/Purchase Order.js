///////////////////////////////////////////////////////////////////////
/////////////////////////// Code specifique ///////////////////////////

/////////////////////////////// Handles ///////////////////////////////

frappe.ui.form.on("Purchase Order",{
	"refresh":  function(frm) {
		// 2016-10-17 - JDLP
		// Lancer la fonction "refresh" au "onLoad" du formulaire parent.
		LoadAttributesValues(false, frm, "items")
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
