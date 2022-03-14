$(window).on('load', function () {
    for (const n in js_vars.q_class){
        var cls = js_vars.q_class[n]
        $('#'+n).addClass(cls)
    }

    if (js_vars.success){
        $('.otree-form-errors').removeClass('alert-danger').addClass('alert-success')
    }
})