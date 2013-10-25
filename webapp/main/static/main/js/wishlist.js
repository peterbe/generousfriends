function _please_wait(form) {
  $('.please-wait', form).show();
  $('button[type="submit"]', form).attr('disabled', 'disabled');
}
function _stop_waiting(form) {
  $('.please-wait', form).hide();
  $('button[type="submit"]', form).removeProp('disabled');
}

function _show_field_error($input, message) {
  var $parent = $input.closest('.form-group');
  $('.help-block', $parent).text(message).show();
  $parent.addClass('has-error');
  $input.on('keypress', _repent);
}

function handleBalancedCallback(response, form) {

  switch (response.status) {
   case 201:
    // it worked!
    var data = {};
    data.csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]', form).val();
    data.uri = response.data.uri;
    data.amount = $('#id_amount').val();
    data.id = response.data.id;
    data.hash = response.data.hash;
    data.email = $('#id_email').val();
    var req = $.post($(form).attr('action'), data);
    req.done(function(response) {
      if (response.error) {
        console.dir(response.error);
        if (response.error.email) {
          alert("Problem with that email address");
          _show_field_error($('#id_email'), response.error.email[0]);
        }
        if (response.error.amount) {
          alert("Problem with that amount");
          _show_field_error($('#id_amount'), response.error.amount[0]);
        }
        if (!(response.error.email || response.error.amount)) {
          console.log('OTHER ERROR');
          $('form.pay .other-error').show();
        }
      } else {
        $('form.pay').hide();
        $('.thank-you .amount').text('$' + response.amount.toFixed(2));
        $('.thank-you').show();
        setTimeout(function() {
          $('.progress .progress-bar').css('width', response.progress_percent + '%');
          $('.progress .label, .progress .sr-only').text(response.progress_percent + '%');
          $('.progress-amount').text('$' + response.progress_amount.toFixed(2));
        }, 1000);
      }
    });
    req.fail(function() {
      console.log('FAILED!');
      $('form.pay .other-error').show();
    });
    req.always(function() {
      _stop_waiting(form);
    });
    break;
   case 400:
    // missing fields
    _stop_waiting(form);
    $.each(response.error, function(field, message) {
      var $input = $('[name="' + field + '"]');
      if ($input.length) {
        _show_field_error($input, message);
      } else {
        console.log(field, message);
      }
    });
    break;
   case 402:
    // we couldn't authorize the buyer's credit card
    // check response.error for details
    _stop_waiting(form);
    console.dir(response.error);
    alert(response.error);
    break;
   case 404:
    // your marketplace URI is incorrect
    _stop_waiting(form);
    alert('Marketplace URI not correct');
    break;
   case 500:
    // Balanced did something bad, please retry the request
    _stop_waiting(form);
    alert("Something unexpected happened with Balanced Payments. Please try again a little later.");
    break;
  }
}

function _repent() {
  var $input = $(this);
  var $parent = $input.closest('.has-error');
  var $parent2 = $input.closest('.form-group');
  $parent.removeClass('has-error');
  $('.help-block', $parent).hide();
}

$(function() {

  $('form.your-name').submit(function() {
    var form = this;
    var _any_error = false;
    $('input[type="text"]', form).each(function() {
      var $input = $(this);
      var value = $.trim($input.val());
      if (!value) {
        _any_error = true;
        var $parent = $input.closest('.form-group');
        $parent.addClass('has-error');
        $('.help-block', $parent).show();
        $input.on('keypress', _repent);
      }
    });
    if (_any_error) return false;
    return true;
  });


  $('.has-error input').on('change', function() {
    console.log("CHANGED FROM ERROR");
    var $parent = $(this).parent('.has-error');
    console.dir($parent);
    $parent.removeClass('has-error');
    $('.help-block', $parent).hide();
  });

  $('form.pay').on('submit', function() {
    var form = this;
    $('.other-error', form).hide();
    _please_wait(form);
    var data = {}
    data.card_number =  $('#id_card_number').val();
    data.expiration_month = $('#id_expiration_month').val();
    data.expiration_year = $('#id_expiration_year').val();
    data.security_code = $('#id_security_code').val();
    balanced.card.create(data, function(response) {
      console.log('STATUS', response.status);
      console.log('ERROR', response.error);
      console.log('DATA', response.data);
      handleBalancedCallback(response, form);

    });
    return false;
  });

  if ($('#id_amount').val()) {
    $('.credit-card').show();
  } else {
    $('#id_amount').on('keypress', function() {
      if ($('.credit-card:hidden').length) {
        $('.credit-card').fadeIn(300);
        $(this).off('keypress');
      }
    });
  }
  $('#absolute_url').on('focus', function() {
    $(this).off('focus');
    $(this).select();
  });

  $('form.name').submit(function() {
    var first_name = $('form.name input[name="first_name"]').val();
    if (!$.trim(first_name)) {
      return false;
    }

  });

  $('button[disabled]').removeProp('disabled');

});