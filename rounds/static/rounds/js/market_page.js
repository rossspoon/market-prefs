$(window).on('load', function () {
    ///////////////////////////
    // These are tasks to do when the page loads
    
    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});

    //Move the timer
    //var timer = $('.otree-timer').detach();
    //$('.message-box').prepend(timer);

    //Add place holder on the order form
    $('#id_quantity').attr('placeholder', 'Quantity')
    $('#id_price').attr('placeholder', 'Price')

    ///////////////////////////
    // EVENT HANDLERS

    // Submit the order form
    $("#submit-btn").click(function(){
        data = get_order_details();
        remove_all_error_messages();
        liveSend({'func':'submit-order', 'data': data});
    });

    // Remove the error message for a form field as it is changed
    $(".form-control,.form-select").change(remove_error_message);
})

var num_orders = 0;
$(document).on('click', ".close-button", function(){
    var raw_id = $(this).attr('id');
    oid = raw_id.substr(raw_id.indexOf('_') +1);
    remove_all_error_messages();
    liveSend({'func': 'delete_order', 'oid': oid});

    $("#order_" + oid).detach();

    num_orders -= 1;
    if (num_orders < 6){
        $("#submit-btn").removeClass("disabled");
        $("input").prop( "disabled", false);
        $("select").prop("disabled", false);
        $(".order-form").removeClass("disabled");
    }
});

function remove_all_error_messages(){
        $(".form-control,.form-select").each(remove_error_message);
}

function remove_error_message(){
        $(this).removeClass("form-error");
        $(this).removeAttr("err-message")
                .parents('.controls')
                .removeClass('with-error')
    }

function get_order_details() {
    o_type = $("#id_type").find(":selected").val();
    o_price = $("#id_price").val();
    o_quant = $("#id_quantity").val();
    return {  'type': o_type
            , 'price': o_price
            , 'quantity': o_quant};
}

function clear_order_form() {
    $("#id_type option:selected").prop("selected", false);
    $("#id_price").val("");
    $("#id_quantity").val("");
}

//////////////////////////////
//   HANDLE LIVE MESSAGES
//////////////////////////////


function add_form_order_to_list(live_data){
    o_info = get_order_details();
    var oid = live_data.order_id;
    add_order_to_list(oid, o_info);
    
    //clear the form when done
    clear_order_form();
}

function add_orders_to_list(live_data) {
    var orders = live_data.orders;
    orders.forEach((o) => {
        var oid = o.oid
        add_order_to_list(oid, o);
    });
}

function add_order_to_list(oid, o_info){
    var order_details_elem = document.createElement("span");
    order_details_elem.classList.add( "order-details");
    var o_type = (o_info.type == "-1") ? 'Buy' : 'Sell';
    order_details_elem.innerHTML = o_type + "&nbsp;&nbsp;" + o_info.quantity + " shares @ " + o_info.price;

    //make the close button
    var close_btn_elem = document.createElement("div");
    close_btn_elem.classList.add( "close-button");
    close_btn_elem.id = "cb_" + oid;
    close_btn_elem.txt = "Cancel this order.";
    close_btn_elem.innerHTML = 'X';

    //assemble order line and append to list
    order_elem = document.createElement("div");
    order_elem.id = "order_" + oid;
    order_elem.classList.add( "order-list-item");
    order_elem.append(close_btn_elem, order_details_elem)
    $('#order-list').append(order_elem);

    num_orders += 1;
    if (num_orders >= 6){
        $("#submit-btn").addClass("disabled");
        $("input").prop( "disabled", true );
        $("select").prop("disabled", true);
        $(".order-form").addClass("disabled");
    }
}

let PRICE = 1;
let QUANTITY = 2;
let TYPE = 3;
let field_type_to_select = {1: '#id_price', 2: '#id_quantity', 3: '#id_type'}
function process_order_rejection(data) {
    code_from_server = data.error_code

    Object.keys(js_vars.error_codes).forEach( (code) => {
        code_data = js_vars.error_codes[code];
        is_on = code_data.value & code_from_server;
        if (is_on) {
            //change field to error type
            field_select = field_type_to_select[code_data.field];
            f = $(field_select).addClass("form-error")
            f = $(field_select)
                .parents('.controls')
                .addClass('with-error')
                .attr('err-message', code_data.desc)
        }
    });
}

function liveRecv(data) {
    var func = data.func;

    if (func == 'order_confirmed') {
        add_form_order_to_list(data);

    } else if (func == 'order_rejected') {
        process_order_rejection(data)

    } else if (func == 'order_list') {
        add_orders_to_list(data);
    }

    // Process Warnings
    $('.pop-up-warning').detach();
    let warnings = data.warnings;
    let warning_elem;
    if (warnings) {
        for (let idx in warnings) {
            let warning_elem = document.createElement("div");
            warning_elem.classList.add("alert", "alert-warning", "pop-up-warning");
            let p = document.createElement("p")
            p.classList.add("message")
            p.innerHTML = warnings[idx]
            warning_elem.append(p)

            $('.message-box').append(warning_elem)
        }
    }
}
