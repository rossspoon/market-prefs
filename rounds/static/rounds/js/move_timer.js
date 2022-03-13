$(window).on('load', function () {
    //Move the timer
    var timer = $('.otree-timer').detach();
    $('#timer_box').prepend(timer);
})