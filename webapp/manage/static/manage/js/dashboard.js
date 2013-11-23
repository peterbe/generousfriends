$(function() {
  var $table = $('#dashboard-data');
  $.getJSON($table.data('url')).then(function(response) {
    $.each(response, function(key, value) {
      var c = $('#' + key);
      if (c.length) {
        if (c.hasClass('price')) {
          value = '$' + parseFloat(value).toFixed(2);
        }
        c.text(value);
      } else {
        console.warn(key);
      }
    });
  });
});
