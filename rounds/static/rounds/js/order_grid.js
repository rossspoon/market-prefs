
let rad = 5;

let NUM_GRID_LINES = js_vars.num_grid_lines;
let PRICE_EXTREME = js_vars.price_extreme;
let MINOR_TICK = js_vars.minor_tick;
let PRICE_PER_TICK = PRICE_EXTREME / ((NUM_GRID_LINES + 1) * MINOR_TICK);
let PRICE_PER_LINE = PRICE_EXTREME / ((NUM_GRID_LINES + 1));
let NUM_VERT_LINES = 4;
let START_MSG = "Submit an order by clicking on the grid."
let edgepad = 5;
let textpad = 50;

//  These are calculated when the grid is redrawn
let GRID_BOX_SIZE = -1;

let o_data = null;
let submitted_odata = null;
let enable_left = true;
let enable_right = true;
let m_pos_valid = true;

function is_on_left(x, box){
  return x < edgepad+box/2;
};

function is_on_right(x, box){
  return x > edgepad+box/2;
};

function is_outside_grid(x,y){
    return x<edgepad || x>edgepad+box || y<edgepad || y>edgepad+box;
};


$(window).on('load', function () {
    $('#curr_ord_msg').text( START_MSG );
    reset_grid();

    $("#price-grid").on("mousemove", function(e){

        // the grid canvas lives in a <div> with position: absolute.
        // I think that's why I can use e.offsetX directly because the coords are
        // referenced from the <div>
        let x = e.offsetX
        let y = e.offsetY

        // early out if mouse pointer is outside the grid box
        if (is_outside_grid(x,y)) {
            reset_grid();
            return;
        }

        $('#curr_ord_msg').text( "" );

        let c = draw_grid(dark_left=!enable_left, dark_right=!enable_right);
        let ctx = c.ctx;
        let hspace = c.hspace;
        let vspace = c.vspace / MINOR_TICK;
        let box = c.box;

        if ((is_on_left(x,box) && !enable_left) || (is_on_right(x, box) && !enable_right)){
            reset_grid();
            return;
        }

        // Snap
        let h_num_space = Math.round(x / hspace);
        let loc_x = edgepad + (h_num_space * hspace);
        let v_num_space = Math.round((y-edgepad) / vspace);
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
        mp = js_vars.market_price;
        let price = (mp + PRICE_EXTREME) - (v_num_space * PRICE_PER_TICK);

        o_data = update_current_order(price, quantity);
    });

    //Clear Grid
    $("#price-grid").on("mouseleave", function(e){
        reset_grid();
    });

    // Submit Order on Click
    $("#price-grid").on("click", function(e){
        if (o_data) {
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

function reset_order_form(){
    $('#curr_ord_type_cell').text("");
    $('#curr_ord_quant_cell').text("");
    $('#curr_ord_price_cell').text("");
    o_data = null;
}

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
    draw_grid(dark_left=!enable_left, dark_right=!enable_right);
    reset_order_form();
}

function draw_grid(dark_left=false, dark_right=false) {
    enable_left = !dark_left;
    enable_right = ! dark_right;

    let market_price = js_vars.market_price;
    let c = document.getElementById("price-grid")
    let ctx=c.getContext("2d");

    if (GRID_BOX_SIZE < 0) {
        let parent = c.parentNode.parentNode;
        let par_h = parent.offsetHeight;
        let par_w = parent.offsetWidth;

        /*To make this square, pick the smallest dimension */
        GRID_BOX_SIZE = Math.min(par_h, par_w) * 1;
    }
    c.height = GRID_BOX_SIZE;
    c.width = GRID_BOX_SIZE;

    box = GRID_BOX_SIZE - (edgepad + textpad);

    let num_top = NUM_GRID_LINES;
    let num_bottom = Math.min(NUM_GRID_LINES, Math.floor(market_price / PRICE_PER_LINE))
    let num_hor_lines = num_top + 1 + num_bottom
    let vspace = box / (num_hor_lines + 1);

    let num_vert_line = (2* NUM_VERT_LINES) + 1;
    let hspace = box/(num_vert_line + 1);


    /* box */
    ctx.save();
    if (dark_left) {
        ctx.fillStyle = "#efefef";
        ctx.fillRect(edgepad,edgepad, box/2, box);
    }
    if (dark_right) {
        ctx.fillStyle = "#efefef";
        ctx.fillRect(edgepad+ box/2,edgepad, box/2, box);
    }
    ctx.lineWidth=1
    ctx.strokeStyle = `rgb(90, 90, 90)`;
    ctx.strokeRect(edgepad,edgepad, box, box);
    ctx.restore();


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
    let vaxis_loc = (edgepad + hspace* (NUM_VERT_LINES + 1));
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
    let start_q = -1 * (NUM_VERT_LINES+1)
    let num_itr = 2*(NUM_VERT_LINES+1) +1
    for (let i = 0; i<num_itr; i++){
        let n = Math.abs(start_q + i)
        ctx.fillText(n.toString(), edgepad + i*hspace, edgepad+box+15)
    }
    ctx.restore();

    return {
        'ctx': ctx,
        'vspace': vspace,
        'hspace': hspace,
        'box': box
    };
};







