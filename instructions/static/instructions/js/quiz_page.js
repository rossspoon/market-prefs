$(window).on('load', function () {
    for (const n in js_vars.q_class){
        var cls = js_vars.q_class[n]
        $('#'+n).addClass(cls)
    }

    //disable the form items if the quiz was already attempted
    if (js_vars.attempted) {
        $("select").prop("disabled", true)
        $("input").prop("disabled", true)
    }

    $('.debug-info').detach();

    if (js_vars.success){
        $('.otree-form-errors').removeClass('alert-danger').addClass('alert-success')
    }
})