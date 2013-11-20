function _please_wait(form) {
  $('.please-wait', form).show();
  $('button[type="submit"]', form).attr('disabled', 'disabled');
}
function _stop_waiting(form) {
  $('.please-wait', form).hide();
  $('button[type="submit"]', form).removeProp('disabled');
}

$(function() {
  $('form.refresh').submit(function() {
    var form = this;
    _please_wait(form);
    var data = {};
    data.csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]', form).val();
    data.refresh = true;
    var req = $.post(location.href, data);
    req.done(function(response) {
      if (response.redirect) {

        var $fp = $('.form-progress', form);
        $fp.show(300);
        var percent = 0;
        var $bar = $('.progress-bar', $fp);
        var progress = setInterval(function() {
          percent += 1;
          if (percent >= 100) {
            clearInterval(progress);
          } else {
            $bar.css('width', percent + '%');
          }
        }, 200);
        location.href = response.redirect;
        return;
      }

    });
    req.always(function() {
      _stop_waiting(form);
    });
    req.fail(function() {
      $('.other-error', form).show();
    });
    return false;
  });
});
