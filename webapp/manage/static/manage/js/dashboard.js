function load_wishlists() {
  var $wishlists = $('#wishlists');
  $.getJSON($wishlists.data('dataurl'), function(response) {
    var $tbody = $('tbody', $wishlists);
    $.each(response.wishlists, function(i, row) {
      console.dir(row);
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

function load_payments() {
  var $container = $('#wishlists');
  $.getJSON($container.data('dataurl'), function(response) {
    var $tbody = $('tbody', $container);
    $.each(response.payments, function(i, row) {
      console.dir(row);
      var tr = $('<tr>');
      tr.append($('<td>')
                .append($('<a>')
                        .attr('href', row.item.manage_url)
                        .attr('title', row.item.title)
                        .text(row.item.identifier)));
      tr.append($('<td>').addClass('price').text('$' + row.amount.toFixed(2)));
      tr.append($('<td>').addClass('price').text('$' + row.actual_amount.toFixed(2)));
      tr.append($('<td>').text(row.email));
      if (row.name) {
        tr.append($('<td>').text(row.name));
      } else {
        tr.append($('<td>').text('--'));
      }
      if (row.message) {
        tr.append($('<td>').append($('<abbr>')
                                   .text("Yes")
                                   .attr('title', row.message)));
      } else {
        tr.append($('<td>').text('--'));
      }
      if (row.receipt_emailed) {
        tr.append($('<td>').text(moment(row.receipt_emailed).fromNow()));
      } else {
        tr.append($('<td>').text('No!'));
      }
      if (row.notification_emailed) {
        tr.append($('<td>').text(moment(row.notification_emailed).fromNow()));
      } else {
        tr.append($('<td>').text('No!'));
      }
      tr.append($('<td>').text(moment(row.added).fromNow()));
      tr.appendTo($tbody);
    });
  });
}

$(function() {
  load_wishlists();
  load_payments();
});
