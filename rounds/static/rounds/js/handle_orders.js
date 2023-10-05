$(window).on('load', function () {
    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});
});

function add_form_order_to_list(live_data){
    var oid = live_data.order_id;
    add_order_to_list(oid, submitted_odata);
}

function add_orders_to_list(live_data) {
    var orders = live_data.orders;
    orders.forEach((o) => {
        var oid = o.oid
        add_order_to_list(oid, o);
    });
}

let num_orders = 0;
function add_order_to_list(oid, o_info){
    //make the close button TD
    const close_btn_elem = document.createElement("span");
    close_btn_elem.classList.add("close-button-grid");
    close_btn_elem.id = "cb_" + oid;
    close_btn_elem.txt = "Cancel this order.";
    close_btn_elem.innerHTML = 'X';
    close_btn_elem.tabIndex = 0;

    const cancel_span = document.createElement("span");
    if (js_vars.show_cancel) {
        cancel_span.append(close_btn_elem);
    } else {
        cancel_span.innerHTML = "&nbsp;";
    }

    // Order Details TD
    const o_deats_td = document.createElement("span")

    // Type Span
    const type_span = document.createElement("span");
    type_span.classList.add('order-details-grid', 'type-col-grid')
    if (isNaN(o_info.type)) {
        type_span.innerHTML = o_info.type;
    } else {
        type_span.innerHTML = (parseInt(o_info.type) === -1) ? 'Buy' : 'Sell';
    }

    // Quant Span
    const quant_span = document.createElement("div");
    quant_span.classList.add('order-details-grid', 'quant-col-grid');
    quant_span.innerHTML="&nbsp;"
    const q_span = document.createElement("span");
    q_span.classList.add('r_just')
    q_span.innerHTML = o_info.quantity;
    quant_span.append(q_span)

    // Shares @ TD
    const shares_at_span = document.createElement("span");
    shares_at_span.classList.add('order-details-grid', 'shares-at-col-grid')
    shares_at_span.innerHTML = "shares @"

    // Price TD
    const price_span = document.createElement("div");
    price_span.classList.add('order-details-grid', 'price-col-grid')
    price_span.innerHTML="&nbsp;"
    const p_span = document.createElement("span");
    p_span.classList.add('r_just')
    p_span.innerHTML = parseFloat(o_info.price).toFixed(2);
    price_span.append(p_span)

    o_deats_td.append(type_span, quant_span, shares_at_span, price_span)

    //assemble order line and append to list
    let order_elem = document.createElement("div");
    order_elem.id = "order_" + oid;
    order_elem.classList.add( 'submitted-order-grid');
    order_elem.append(cancel_span, o_deats_td)//, notes_td, fulfilled_td)
    $('#order_list_grid').append(order_elem);

    // Disable the form is this is the sixth order
    num_orders += 1;
    if (num_orders >= 6){  //show_cancel is true only on the market page.
        disable_grid();
    }
}


function disable_grid() {
    grid_enabled = false;
}

function enable_grid() {
    grid_enabled = true;
}

$(document).on('click', ".close-button-grid", function(){
    cancel_order($(this));
});

$(document).on('keydown', ".close-button-grid", function(event){
    if (event.keyCode == 13) {
        cancel_order($(this));
    }
});

function cancel_order(elem){
    var raw_id = elem.attr('id');
    oid = raw_id.substr(raw_id.indexOf('_') +1);
    //remove_all_error_messages();
    liveSend({'func': 'delete_order', 'oid': oid});

    $("#order_" + oid).detach();

    num_orders -= 1;
    if (num_orders < 6){
        enable_grid();
    }
}

function process_order_rejection(data) {
    code_from_server = data.error_code

    Object.keys(js_vars.error_codes).forEach( (code) => {
        code_data = js_vars.error_codes[code];
        is_on = code_data.value & code_from_server;
        if (is_on) {
            $('#curr_ord_msg').text(code_data.desc);
        }
    });
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

    // process_warnings(data)
}
