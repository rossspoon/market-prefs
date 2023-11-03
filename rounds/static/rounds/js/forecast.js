
$(window).on('load', function () {
  $('.slider').on('input', function () {
    let target = $(this).attr('target')
    let val = $(this).val();
    $('#' + target).text(val + '%');
    $(this).parents('.fcast-box').children('input').val(val);
  });
});