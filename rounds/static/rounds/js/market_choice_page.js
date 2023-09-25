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


    $(".q-slide").on('input', function(){
        let id = $(this).attr('id');
       $('#'+id+'_val').html($(this).val());
    });
});
