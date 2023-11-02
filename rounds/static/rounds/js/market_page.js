$(window).on('load', function () {
    ///////////////////////////
    // These are tasks to do when the page loads
    $('.debug-info').detach();
    $('#_otree-title').detach();
    $('.input-group-text').detach();

    if (js_vars.show_notes){
        $('#notes-col').removeClass('hidden')
        $('#fulfilled-col').removeClass('hidden')
    }

    $("#pop-up-btn").click(function(){
        $("#round_num_alert").detach();
        $("#gray-out").detach();
    });
    
    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});

    //Add placeholder on the order form
    $('#id_quantity').attr('placeholder', 'Quantity')
    $('#id_price').attr('placeholder', 'Price')

    set_tool_tips();

    ///////////////////////////
    // EVENT HANDLERS

    // Submit the order form
    $("#submit-btn").click(function(){
        submit_order_form();
    });

    $("#submit-btn").keypress(function(event){
        if ( event.which == 13 ) {
            submit_order_form();
        }
    });

    // Remove the error message for a form field as it is changed
    $(".form-control,.form-select").change(remove_error_message);
})

function submit_order_form(){
        data = get_order_details();
        remove_all_error_messages();
        liveSend({'func':'submit-order', 'data': data});
}

var num_orders = 0;
$(document).on('click', ".close-button", function(){
    cancel_order($(this));
});

$(document).on('keydown', ".close-button", function(event){
    if (event.keyCode == 13) {
        cancel_order($(this));
    }
});

function cancel_order(elem){
    var raw_id = elem.attr('id');
    oid = raw_id.substr(raw_id.indexOf('_') +1);
    remove_all_error_messages();
    liveSend({'func': 'delete_order', 'oid': oid});

    $("#order_" + oid).detach();

    num_orders -= 1;
    if (num_orders < 6){
        $("#submit-btn").removeClass("disabled");
        $("input").prop( "disabled", false);
        $("select").prop("disabled", false);
        $(".order-form").parents('.boxed_area').removeClass("disabled");
    }
}

function remove_all_error_messages(){
        $(".form-control,.form-select").each(remove_error_message);
}

function remove_error_message(){
        $(this).removeClass("form-error");
        $(this).removeAttr("err-message")
                .parents('.controls')
                .removeClass('with-error')
                .removeClass('long-pseudo')
    }

function get_order_details() {
    let o_type = $("#id_type").find(":selected").val();
    let o_price = $("#id_price").val();
    if (!isNaN(o_price)){
        o_price = Number(o_price).toFixed(2)
    }
    let o_quant = $("#id_quantity").val();
    return {  'type': o_type
            , 'price': o_price
            , 'quantity': o_quant
            , 'requested_quant': o_quant};
}

// function process_warnings(data) {
//     // Process Warnings
//     $('.pop-up-warning').detach();
//     let warnings = data.warnings;
//     if (warnings) {
//         for (let idx in warnings) {
//             let warning_elem = document.createElement("div");
//             warning_elem.classList.add("alert", "alert-warning", "pop-up-warning");
//             let p = document.createElement("p")
//             p.classList.add("message")
//             p.innerHTML = warnings[idx]
//             warning_elem.append(p)
//
//             $('.message-box').append(warning_elem)
//         }
//     }
// }
//
// function liveRecv(data) {
//     process_warnings(data)
// }
