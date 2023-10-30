$(window).on('load', function () {
    //Set content size to document size.
    let size_window = function () {
        let wh = $(window).height();
        console.log(wh);
        $('.layout-box').css('height', wh);
    };
    size_window();
    $(window).resize(size_window);
});