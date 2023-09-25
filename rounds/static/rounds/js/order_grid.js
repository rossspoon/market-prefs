
let rad = 5;

let NUM_GRID_LINES = 4;
let PRICE_EXTREME = 100;
let MINOR_TICK = 4
let PRICE_PER_LINE = PRICE_EXTREME / ((NUM_GRID_LINES + 1) * MINOR_TICK);
let START_MSG = "Submit an order by clicking on the grid."
let o_data = null;
let submitted_odata = null;
let num_orders = 0;
let grid_enabled = true;
let edgepad = 5;
let textpad = 50;

$(window).on('load', function () {
    $('#curr_ord_msg').text( START_MSG );
    reset_grid();

    // This requests all the orders
    // If the page is reloaded then we need to see any existing orders
    liveSend({'func': 'get_orders_for_player'});

    $("#price-grid").on("mousemove", function(e){
        $('#curr_ord_msg').text( "" );

        let mp = js_vars.market_price;
        let c = draw_grid(mp);
        let ctx = c.ctx;
        let hspace = c.hspace;
        let vspace = c.vspace / MINOR_TICK;
        let box = c.box;

        let x = e.pageX - this.offsetLeft;
        let y = e.pageY - this.offsetTop;

        // early out if mouse pointer is outside the grid box
        if (x > edgepad+box || y > edgepad+box){
            $('#curr_ord_type_cell').text("");
            $('#curr_ord_quant_cell').text("");
            $('#curr_ord_price_cell').text("");
            o_data = null;
            return;
        }

        // Snap
        let h_num_space = Math.round(x / hspace);
        let loc_x = edgepad + (h_num_space * hspace);
        let v_num_space = Math.round(y / vspace);
        let loc_y = edgepad + (v_num_space * vspace);

        // Draw Circle
        ctx.beginPath();
        ctx.arc(loc_x, loc_y, rad, 0, 2*Math.PI, false);
        ctx.fillStyle = 'red';
        ctx.fill();
        ctx.lineWidth = 3;
        ctx.strokeStyle=`rgb(200, 50, 50)`;
        ctx.stroke();

        // Current Order
        let quantity = -5 + h_num_space;
        let price = (mp + PRICE_EXTREME) - (v_num_space * PRICE_PER_LINE);

        o_data = update_current_order(price, quantity);
    });

    //Clear Grid
    $("#price-grid").on("mouseleave", function(e){
        reset_grid();
    });

    // Submit Order on Click
    $("#price-grid").on("click", function(e){
        if (o_data && grid_enabled) {
            submitted_odata = o_data;
            liveSend({'func': 'submit-order', 'data': submitted_odata});
            reset_grid();
        }
    });

    // Handle resize
    $( window ).on( "resize", function() {
        GRID_BOX_SIZE = -1;
        reset_grid();
    });
});

function update_current_order(price, quantity){
    $('#curr_ord_quant_cell').removeClass('curr_ord_alert');
    $('#curr_ord_price_cell').removeClass('curr_ord_alert');

    let type =  quantity == 0 ? "": quantity < 0 ? "SELL": "BUY";
    let q = Math.abs(quantity)
    let p = Math.max(price, 0);

    $('#curr_ord_type_cell').text(type);
    $('#curr_ord_quant_cell').text(q);
    $('#curr_ord_price_cell').text(p);

    if (price <= 0 ){
        $('#curr_ord_price_cell').addClass('curr_ord_alert');
        return null;
    }
    if (quantity == 0) {
        $('#curr_ord_quant_cell').addClass('curr_ord_alert');
        return null;
    }

    return {
        'type': type,
        'quantity': q,
        'price': price
    };
}

function reset_grid(){
    let mp = js_vars.market_price;
    draw_grid(mp);
    $('#curr_ord_type_cell').text("");
    $('#curr_ord_quant_cell').text("");
    $('#curr_ord_price_cell').text("");}

let GRID_BOX_SIZE = -1;
function draw_grid(market_price) {
    let c = document.getElementById("price-grid")
    let ctx=c.getContext("2d");

    if (GRID_BOX_SIZE < 0) {
        let parent = c.parentNode;
        let par_h = parent.offsetHeight;
        let par_w = parent.offsetWidth;

        /*To make this square, pick the smallest dimension */
        GRID_BOX_SIZE = Math.min(par_h, par_w) * 1;
    }
    c.height = GRID_BOX_SIZE;
    c.width = GRID_BOX_SIZE;

    let box = GRID_BOX_SIZE - (edgepad + textpad);

    let num_top = NUM_GRID_LINES;
    let num_bottom = Math.min(NUM_GRID_LINES, Math.floor(20/market_price))
    let num_hor_lines = num_top + 1 + num_bottom
    let vspace = box / (num_hor_lines);

    let num_vert_line = (2* NUM_GRID_LINES) + 1;
    let hspace = box/(num_vert_line + 1);

    /* Box */
    ctx.lineWidth=1
    ctx.strokeStyle = `rgb(90, 90, 90)`;
    ctx.strokeRect(edgepad,edgepad, box, box);

    ctx.save();

    /* Vertical lines*/
    ctx.strokeStyle = `rgb(200, 200, 200)`;
    for (let i = 1; i <= num_vert_line; i++) {
      ctx.setLineDash([2,2])
      ctx.beginPath();
      ctx.moveTo(edgepad+ hspace*i, edgepad);
      ctx.lineTo(edgepad + hspace*i, box+edgepad);
      ctx.stroke();
    }
    ctx.restore();


    /* Horizontal lines */
    ctx.strokeStyle = `rgb(200, 200, 200)`;
    for (let i = 1; i <= num_hor_lines; i++) {
      ctx.setLineDash([2,2])
      ctx.beginPath();
      ctx.moveTo(edgepad,  edgepad + vspace*i);
      ctx.lineTo(box+ edgepad, edgepad + vspace*i);
      ctx.stroke();
    }
    ctx.restore();

    /* Center lines */
    /* horizontal axis */
    ctx.lineWidth = 3;
    ctx.setLineDash([])
    let haxis_loc = (edgepad + vspace*(NUM_GRID_LINES +1));
    ctx.beginPath();
    ctx.strokeStyle = `rgb(75, 75, 75)`;
    ctx.moveTo(edgepad, haxis_loc);
    ctx.lineTo(box+edgepad, haxis_loc);
    ctx.stroke();
    ctx.restore();


    /* vertical axis */
    ctx.beginPath();
    let vaxis_loc = (edgepad + hspace* (NUM_GRID_LINES + 1));
    ctx.strokeStyle = `rgb(75, 75, 75)`;
    ctx.moveTo(vaxis_loc, edgepad);
    ctx.lineTo(vaxis_loc, box +edgepad);
    ctx.stroke();
    ctx.restore();


    // Price Label
    ctx.save()
    ctx.translate(edgepad+box+50, edgepad+box/2)
    ctx.rotate(-Math.PI/2);
    ctx.textAlign = "center";
    ctx.font = "15pt sans";
    ctx.fillText("Price", 0, 0);
    ctx.restore();

    //Price Grading
    ctx.save()
    ctx.font = "10pt sans";
    for (let i = 0; i <= num_hor_lines; i++) {
        let p = market_price + PRICE_EXTREME - (i* PRICE_EXTREME/(NUM_GRID_LINES + 1));
        if (p < 0){
            p=0;
        }
        ctx.fillText(p.toString(), edgepad+ box+5,edgepad + 5 + i*vspace);
    }
    ctx.restore();

    //Buy/Sell Labels
    ctx.save();
    ctx.font="15pt sans";
    ctx.textAlign = 'center';
    ctx.fillText("Sell", edgepad + box/4, edgepad + box + 45);
    ctx.fillText("Buy", edgepad + 3*box/4, edgepad + box + 45);
    ctx.restore()

    //Number of Shares
    ctx.save();
    ctx.font = "10pt sans";
    ctx.textAlign = 'center';
    let start_q = -1 * (NUM_GRID_LINES+1)
    let num_itr = 2*(NUM_GRID_LINES+1) +1
    for (let i = 0; i<num_itr; i++){
        n = start_q + i
        ctx.fillText(n.toString(), edgepad + i*hspace, edgepad+box+15)
    }
    ctx.restore();

    return {
        'ctx': ctx,
        'vspace': vspace,
        'hspace': hspace,
        'box': box,
    };
};



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
    console.log("Here:", data)
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





