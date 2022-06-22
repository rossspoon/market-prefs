$(window).on('load', function () {
    for (const n in js_vars.q_class){
        var cls = js_vars.q_class[n]
        $('#'+n).addClass(cls)
    }

    if (js_vars.attempted) {
        //disable the form items if the quiz was already attempted
        $("select").prop("disabled", true)
        $("input").prop("disabled", true)

        $('.quiz-question').each(function() {
            let name = this.id;
            console.log(name)
            let msg = js_vars.errors[name]
            console.log(msg)
            $("#"+name + " .form-control-errors").text(msg)
        });
    }

    //$('.debug-info').detach();
})