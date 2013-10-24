$(function() {
  $('form').submit(function() {
    var $form = $(this);
    $('.form-error, .form-progress').hide();
    $('button[type="submit"]', $form).attr('disabled', 'disabled');
    var data = {};
    $.each($form.serializeArray(), function(i, each) {
      data[each.name] = each.value;
    });

    var $fp = $('.form-progress');
    $fp.show(300);
    var percent = 0;
    var $bar = $('.progress-bar', $fp);
    var progress = setInterval(function() {
      percent += 3;
      if (percent >= 100) {
        clearInterval(progress);
      } else {
        $bar.css('width', percent + '%');
      }
    }, 350);
    var req = $.post(location.href, data);
    req.done(function(response) {
      if (response.redirect) {
        location.href = response.redirect;
      }
      $bar.css('width', '100%');
      if (response.redirect) {
        location.href = response.redirect;
      } else {
        if (response.error) {
          console.dir($('.form-error'));
          $fp.hide();
          $('.form-error p').html(response.error);
          $('.form-error').show(300);
        }
      }
    });
    req.fail(function() {
      $('.form-error p').html('Sorry. Some unknown error happened on the server. Try again later.');
      $('.form-error').show(300);
    });
    req.always(function() {
      clearInterval(progress);
      $('button[type="submit"]').removeAttr('disabled');
      $('.form-progress').hide();
    });
    return false;
  });

  $('form button[type="submit"]').removeAttr('disabled');
});
