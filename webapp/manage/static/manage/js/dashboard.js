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

  var $news = $('#news');
  $.getJSON($news.data('url')).then(function(response) {
    var tbody = $('tbody', $news);
    $.each(response.newsitems, function(i, item) {
      console.log(i, item);
      $('<tr>')
        .append($('<td>')
                .append($('<a>').attr('href', item.url).text(item.description)))
        .append($('<td>').text(moment(item.date).fromNow()))
        .appendTo(tbody);
    });
  });
});
