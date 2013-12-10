function load_wishlists() {
  var $wishlists = $('#wishlists');
  var data = {};
  if ($('#id_include_not_verified').prop('checked')) {
    data.include_not_verified = true;
  }
  $.getJSON($wishlists.data('dataurl'), data, function(response) {
    var $tbody = $('tbody', $wishlists);
    $('tr', $tbody).remove();
    $.each(response.wishlists, function(i, row) {
      //console.dir(row);
      var tr = $('<tr>');
      tr.append($('<td>')
                .append($('<a>').attr('href', row.url).text(row.identifier)));
      tr.append($('<td>').text(row.status));
      if (row.email) {
        tr.append($('<td>').text(row.email));
      } else {
        tr.append($('<td>').text('--'));
      }
      tr.append($('<td>').text(moment(row.modified).fromNow()));
      if (row.price) {
        tr.append($('<td>').addClass('price').text('$' + row.price.toFixed(2)));
      } else {
        tr.append($('<td>').text('--'));
      }
      if (row.total_amount) {
        tr.append($('<td>').addClass('price').text('$' + row.total_amount.toFixed(2)));
        tr.append($('<td>').addClass('price').text('$' + row.total_actual_amount.toFixed(2)));
      } else {
        tr.append($('<td>').text('--'));
        tr.append($('<td>').text('--'));
      }
      if (row.days_left !== null) {
        tr.append($('<td>').text(row.days_left));
      } else {
        tr.append($('<td>').text('--'));
      }
      tr.appendTo($tbody);
    });
  });
}


$(function() {
  load_wishlists();
  $('#id_include_not_verified').change(function() {
    load_wishlists();
  });
});
