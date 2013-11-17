$(function() {

  // Because `readonly` looks weird works badly on mobile
  $('input.share-url').on('focus', function() {
    this.select();
    $(this).off('focus');
  }).on('keypress', function() {
    $(this).val($(this).data('original'));
  }).on('blur', function() {
    $(this).val($(this).data('original'));
  });

  $('#share-by-email form').submit(function() {
    var form = this;
    var val = $.trim($('textarea', form).val());
    if (!val) return false;
    var data = {};
    data.emails = val;
    if ($('input[name="send_copy"]:checked', form).length) {
      data.send_copy = true;
    }
    data.csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]', form).val();
    _please_wait(form);
    $('#share-by-email .share-success').hide();
    $('#share-by-email .share-error').hide();

    var req = $.post($(form).attr('action'), data);
    req.done(function(response) {
      console.dir(response);
      if (response.error) {
        $('#share-by-email .share-error .message').html(response.error);
        $('#share-by-email .share-error').show();
      } else if (response.emails) {
        $('#share-by-email .share-success .emails').text("Sent to: " + response.emails.join(', '));
        $('#share-by-email .share-success').show();
        $('textarea', form).val('');
      }
    });
    req.fail(function() {
      $('#share-by-email .share-error').show();
    });
    req.always(function() {
      _stop_waiting(form);
    });

    return false;
  });

  $('.share-options a').click(function() {
    var id = $(this).attr('href');
    $('.share-option').not(id).hide();
    $(id).fadeIn(400);
    var nav = $('li.active', $(this).closest('.nav')).removeClass('active');
    $(this).closest('li').addClass('active');
    return false;
  });


});
