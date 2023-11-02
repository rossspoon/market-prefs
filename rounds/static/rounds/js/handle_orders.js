let ALL_ORDERS = new Map();

$(window).on('load', function () {
    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});
});

function clear_orders_grid(){
    //Remove all orders so we can re-add them
    $('.orders-box-grid li').detach();
    num_sells = 0;
    num_buys = 0;
}


function add_form_order_to_list(live_data){
    var oid = live_data.order_id;
    submitted_odata.oid = oid;
    ALL_ORDERS.set(""+oid, submitted_odata)
    fill_order_section();
}

function add_orders_to_list(live_data) {
    var orders = live_data.orders;
    ALL_ORDERS.clear();

    orders.forEach((o) => {
        oid = o.oid;
        ALL_ORDERS.set(""+oid, o);
    });

    fill_order_section();
}

function fill_order_section(){
    clear_orders_grid();

    let o_list = Array.from(ALL_ORDERS.values());
    let o_sort = o_list.sort((a,b) => b.price - a.price)

    o_sort.forEach((o) => {
        let oid = o.oid
        add_order_to_list(oid, o);
    });
}

let num_buys = 0;
let num_sells = 0;
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

    // Type
    const type_span = document.createElement("span");
    if (isNaN(o_info.type)) {
        o_type = o_info.type;
    } else {
        o_type = (parseInt(o_info.type) === -1) ? 'Buy' : 'Sell';
    }

    // Quant Span
    const quant_span = document.createElement("span");
    quant_span.classList.add('order-details-grid', 'quant-col-grid');
    quant_span.innerHTML = "&nbsp;" + o_info.quantity + " @ ";

    // Price TD
    const price_span = document.createElement("span");
    price_span.classList.add('order-details-grid', 'price-col-grid')
    price_span.innerHTML="&nbsp;"
    const p_span = document.createElement("span");
    p_span.classList.add('r_just')
    p_span.innerHTML = parseFloat(o_info.price).toFixed(2);
    price_span.append(p_span)

    o_deats_td.append(quant_span, price_span)

    // Fulfilled TD
    if (js_vars.show_notes && o_info.quantity_final>0) {
        const filled_span = document.createElement("span");
        filled_span.classList.add("filled-grid")
        filled_span.innerHTML = "&nbsp; Filled " + o_info.quantity_final;
        o_deats_td.append(filled_span)
    }

    //assemble order line and append to list
    let order_elem = document.createElement("li");
    order_elem.id = "order_" + oid;
    order_elem.classList.add( 'submitted-order-grid');
    order_elem.append(cancel_span, o_deats_td)

    if (o_type.toUpperCase() == 'BUY'){
        num_buys += 1;
        $('#buy_orders').append(order_elem);
    } else {
        num_sells += 1;
        $('#sell_orders').append(order_elem);
    }

    let dark_right = num_buys >= 3;
    let dark_left = num_sells >= 3;
    if (dark_left || dark_right) {
        draw_grid(dark_left=dark_left, dark_right=dark_right);
    }
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
    const raw_id = elem.attr('id');
    let oid = raw_id.substr(raw_id.indexOf('_') + 1);

    //determine if this is a buy or sell
    let parent_id = $('#order_' + oid).parents('.order_col')[0].id

    //remove_all_error_messages();
    liveSend({'func': 'delete_order', 'oid': oid});

    $("#order_" + oid).detach();
    //Remove the order from the ALL_ORDERS collection
    ALL_ORDERS.delete(oid);


    //determine which side of the ordergrid to enable
    if (parent_id == 'buy_box'){
        num_buys -= 1;
    } else {
        num_sells -= 1;
    }
    let dark_right = num_buys >=3;
    let dark_left = num_sells >= 3;
    draw_grid(dark_left=dark_left, dark_right=dark_right);
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
