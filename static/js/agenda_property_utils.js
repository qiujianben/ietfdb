/*
*   agenda_property_utils.js
*
*   Orlando Project: Credil 2013 ( http://credil.org/ )
*   Author: Justin Hornosty    <justin@credil.org>
*   Author: Michael Richardson <mcr@sandelman.ca>
*
*
*   Some functions for toggling, saving and deleting agenda properties.
*
*/




//////////////-GLOBALS----////////////////////////////////////////


/////////////-END-GLOBALS-///////////////////////////////////////


function delete_agenda(event) {
    var agenda_url    = $(event.target).closest('tr').attr('href');
    event.preventDefault();

    $("#agenda_delete_dialog").dialog({
      buttons : {
        "Confirm" : function() {
	    $.ajax({
		url: agenda_url,
	       type: 'DELETE',
	    success: function(result) {
			window.location.reload(true);
                 }
            });
            $(this).dialog("close");
        },
        "Cancel" : function() {
            $(this).dialog("close");
        }
      }
    });

    $("#room_delete_dialog").dialog("open");
}

function toggle_public(event) {
    var span_to_replace = event.target;
    var current_value   = $(event.target).html();
    var agenda_url      = $(event.target).closest('tr').attr('href');

    var new_value = 1;
    log("value "+current_value)
    if(current_value == "public") {
        new_value = 0
    }
    event.preventDefault();

    $.ajax({ "url": agenda_url,
             "type": "PUT",
             "data": { "public" : new_value },
             "dataType": "json",
             "success": function(result) {
                 /* result is a json object */
                 value = result["public"]
                 log("new value "+value)
                 $(span_to_replace).html(value)
             }});
}

function toggle_visible(event) {
    var span_to_replace = event.target;
    var current_value   = $(event.target).html();
    var agenda_url      = $(event.target).closest('tr').attr('href');

    var new_value = 1;
    log("value "+current_value)
    if(current_value == "visible") {
        new_value = 0
    }
    event.preventDefault();

    $.ajax({ "url": agenda_url,
             "type": "PUT",
             "data": { "visible" : new_value },
             "dataType": "json",
             "success": function(result) {
                 /* result is a json object */
                 value = result["visible"]
                 log("new value "+value)
                 $(span_to_replace).html(value)
             }});
}

/*
 * Local Variables:
 * c-basic-offset:4
 * End:
 */

