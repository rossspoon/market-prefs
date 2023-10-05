$(window).on('load', function () {

    // Handle card clicks
    $('.elic-card').click(function(){
        $('.elic-card').removeClass('elic-clicked');
        $(this).addClass('elic-clicked');

        const rfield = $("#risk")
        if ($(this).attr('id') == 'risky_card'){
            rfield.val(1)
        } else {
            rfield.val(0)
        }

    });

});