function load_payments() {
  var $container = $('#payments');
  $.getJSON($container.data('dataurl'), function(response) {
    var $tbody = $('tbody', $container);
    $.each(response.payments, function(i, row) {
      console.dir(row);
      var tr = $('<tr>');
      if (row.declined) {
        tr.addClass('declined');
      }
      tr.append($('<td>')
                .append($('<a>')
                        .attr('href', row.item.manage_url)
                        .attr('title', row.item.title)
                        .text(row.item.identifier))
                .append($('<span>')
                        .addClass('price')
                        .text(' ($' + row.item.price.toFixed(2) + ')')));
      tr.append($('<td>').addClass('price').text('$' + row.amount.toFixed(2)));
      tr.append($('<td>').addClass('price').text('$' + row.actual_amount.toFixed(2)));
      if (row.refund_amount) {
        tr.append($('<td>').addClass('price').text('$' + row.refund_amount.toFixed(2)));
      } else {
        tr.append($('<td>').text('--'));
      }
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
      tr.append($('<td>').append($('<a>').attr('href', row.url).text('Refund/Decline')));

      tr.appendTo($tbody);
    });
  });
}

$(function() {
  load_payments();
});
