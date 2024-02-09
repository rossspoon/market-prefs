
$(window).on('load', function () {
  $('.slider').on('input', function () {
    let target = $(this).attr('target')
    let val = $(this).val();
    if (parseInt(val) < 1){
        val = ''
    }
    $('#' + target).text(val);
    $(this).parents('.fcast-box').children('input').val(val);
  });
});