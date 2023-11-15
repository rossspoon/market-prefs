
$(window).on('load', function () {
  $('.slider').on('input', function () {
    let target = $(this).attr('target')
    let val = $(this).val();
    if (parseInt(val) < 1){
        val = ''
    }
    $('#' + target).text(val);
    $(this).parents('.fcast-box').children('input').val(val);

    let mp = js_vars.market_price;
    let fcast_price = Math.round(mp * (1 + val/100));
  });
});