$(window).on('load', function () {
    attach_pop_ups();
    $('.debug-info').detach();
});

function attach_pop_ups(){
    let pop_ups = document.getElementsByClassName("ins-pop-up")

    for (let index = 0; index < pop_ups.length; index++) {
        let elem = pop_ups[index];
        position_pop_up(elem);
        add_next_button(elem);
    }
}

// Position the element in its parent element
function position_pop_up(elem){
    let rel = elem.getAttribute('rel')
    if (rel) {
        elem.parentElement.removeChild(elem)
        let new_parent = document.getElementById(rel)
        new_parent.append(elem)
    }
}

function add_next_button(elem){
    if (elem.classList.contains('dont-add-button')){
        return;
    }
    let bottom_row = document.createElement('div')
    bottom_row.classList.add('bottom-row')
    bottom_row.innerHTML = "&nbsp;"
    let button_div =document.createElement('div');
    button_div.classList.add('ins-btn', 'btn', 'btn-primary', 'r_just');
    button_div.tabIndex = 1;
    button_div.innerHTML = 'Next'
    bottom_row.append(button_div);
    elem.append(bottom_row);
}

$(document).on('click', ".ins-btn", function(){
    go_to_next($(this))
});
$(document).on('keypress', ".ins-btn", function(event){
    if ( event.which == 13 ) {
        go_to_next($(this));
    }
});
function go_to_next(elem){
    let pop_up = elem.parents('.ins-pop-up');
    pop_up.removeClass('on')
    let next_id = pop_up[0].getAttribute('next')
    let next = document.getElementById(next_id)
    next.classList.add('on')
    // $('#'+next_id+ ' .ins-btn').focus();
}

function history_click(){
  $('#id_type option[value="-1"]').prop('selected', true)
}
$(document).on('click', "#06_history .ins-btn", function(){ history_click()});
$(document).on('keypress', "#06_history .ins-btn", function(){history_click()});


function type_click() {
    $('#id_quantity').val(4);
}
$(document).on('click', "#07_o_type .ins-btn", function(){type_click()});
$(document).on('keypress', "#07_o_type .ins-btn", function(){type_click()});

function quant_click() {
    $('#id_price').val(23.45);
}
$(document).on('click', "#08_o_quant .ins-btn", function(){quant_click()});
$(document).on('keypress', "#08_o_quant .ins-btn", function(){quant_click()});

function submit_clicked() {
    $('#id_type option[value="-1"]').prop('selected', false)
    $('#id_quantity').val('');
    $('#id_price').val('');

    $('#order_7').removeClass('off');
    $('#order_7').addClass('on');
}
$(document).on('click', "#10_submit .ins-btn", function(){submit_clicked()});
$(document).on('keypress', "#10_submit .ins-btn", function(){submit_clicked()});

function details_clicked() {
    $('.close-button').addClass('close-button-hover')
}
$(document).on('click', "#11_order_details .ins-btn", function(){details_clicked()});
$(document).on('keypress', "#11_order_details .ins-btn", function(){details_clicked()});

function cancel_clicked() {
    $('.close-button').removeClass('close-button-hover')
}
$(document).on('click', "#12_cancel .ins-btn", function(){cancel_clicked()});
$(document).on('keypress', "#12_cancel .ins-btn", function(){cancel_clicked()});


