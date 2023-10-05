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

    let size_window = function() {
        let wh = $(document).height();
        $('.layout-box-grid').css('height', wh);
    };
    size_window();
    $(window).resize(size_window);

    set_tool_tips();

    ///////////////////////////
    // EVENT HANDLERS

    $(".q-slide").on('input', function(){
        let id = $(this).attr('id');
       $('#'+id+'_val').html($(this).val());
    });
});
