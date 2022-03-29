$(window).on('load', function () {
    ///////////////////////////
    // These are tasks to do when the page loads
    $('.debug-info').detach();

    if (js_vars.show_notes){
        $('#notes-col').removeClass('hidden')
        $('#fulfilled-col').removeClass('hidden')
    }
    
    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});

    //Move the timer
    //var timer = $('.otree-timer').detach();
    //$('.message-box').prepend(timer);

    //Add placeholder on the order form
    $('#id_quantity').attr('placeholder', 'Quantity')
    $('#id_price').attr('placeholder', 'Price')
    $('#id_f0').attr('placeholder', js_vars.market_price)

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
    //make the close button TD
    const close_btn_elem = document.createElement("span");
    close_btn_elem.classList.add("close-button");
    close_btn_elem.id = "cb_" + oid;
    close_btn_elem.txt = "Cancel this order.";
    close_btn_elem.innerHTML = 'X';
    close_btn_elem.tabIndex = 0;

    const cancel_td = document.createElement("td");
    if (js_vars.show_cancel) {
        cancel_td.append(close_btn_elem);
    } else {
        cancel_td.innerHTML = "&nbsp;";
    }

    // Order Details TD
    const o_deats_td = document.createElement("td")

    // Type Span
    const type_span = document.createElement("span");
    type_span.classList.add('order-details', 'type-col')
    type_span.innerHTML = (o_info.type === "-1") ? 'Buy' : 'Sell';

    // Quant Span
    const quant_span = document.createElement("div");
    quant_span.classList.add('order-details', 'quant-col');
    quant_span.innerHTML="&nbsp;"
    const q_span = document.createElement("span");
    q_span.classList.add('r_just')
    q_span.innerHTML = o_info.requested_quant;
    quant_span.append(q_span)

    // Shares @ TD
    const shares_at_span = document.createElement("span");
    shares_at_span.classList.add('order-details', 'shares-at-col')
    shares_at_span.innerHTML = "shares @"

    // Price TD
    const price_span = document.createElement("span");
    price_span.classList.add('order-details', 'price-col')
    price_span.innerHTML="&nbsp;"
    const p_span = document.createElement("span");
    p_span.classList.add('r_just')
    p_span.innerHTML = o_info.price;
    price_span.append(p_span)

    o_deats_td.append(type_span, quant_span, shares_at_span, price_span)

    // Notes TD
    const notes_td = document.createElement("td");
    notes_td.classList.add("notes-col")
    if (! js_vars.show_notes){
        notes_td.classList.add("hidden")
        notes_td.innerHTML = "&nbsp;"
   } else {
        const notes_span = document.createElement("span")
        notes_span.innerHTML=o_info.note
        notes_td.append(notes_span)
    }

    // Fulfilled TD
    const fulfilled_td = document.createElement("td");
    fulfilled_td.classList.add("full-col")
    fulfilled_td.innerHTML = "&nbsp;"
    if (! js_vars.show_notes) {
        fulfilled_td.classList.add("hidden")
    } else {
        fulfilled_td.innerHTML = o_info.quantity_final + " @ " + js_vars.market_price_str;
    }

    //assemble order line and append to list
    let order_elem = document.createElement("tr");
    order_elem.id = "order_" + oid;
    order_elem.classList.add( "order-list-item");
    order_elem.append(cancel_td, o_deats_td, notes_td, fulfilled_td)
    $('#order-list').append(order_elem);

    // Disable the form is this is the sixth order
    num_orders += 1;
    if (num_orders >= 6){
        $("#submit-btn").addClass("disabled");
        $("input").prop( "disabled", true );
        $("select").prop("disabled", true);
        $(".order-form").parents('.boxed_area').addClass("disabled");
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

function process_warnings(data) {
    // Process Warnings
    $('.pop-up-warning').detach();
    let warnings = data.warnings;
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

function liveRecv(data) {
    const func = data.func;

    if (func === 'order_confirmed') {
        add_form_order_to_list(data);

    } else if (func === 'order_rejected') {
        process_order_rejection(data)

    } else if (func === 'order_list') {
        add_orders_to_list(data);
    }

    process_warnings(data)
}
