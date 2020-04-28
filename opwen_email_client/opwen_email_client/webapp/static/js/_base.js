(function ($, ctx, appRoot) {
  $(document).ready(function () {
    (function pollForNewEmails () {
      function checkForNewEmails () {
        $.getJSON(appRoot + '/email/unread', function (response) {
          if (!response.unread || document.location.pathname.startsWith('/email/') || $('.alert.new-emails').length) {
            return
          }

          var $flashes = $('.flashes')
          if (!$flashes.length) {
            $flashes = $('<ul class="flashes list-unstyled" />')
            $('nav').after($flashes)
          }

          var $li = $('<li class="success" />')
          var $div = $('<div class="alert alert-info new-emails" role="alert" />')
          var $link = $('<a href="/email/inbox" />').append(ctx.i8n.openMailbox)

          $flashes.append($li)
          $li.append($div)
          $div.append($('<span class="fa fa-info-circle" aria-hidden="true" />'))
          $div.append($('<span class="sr-only">Success:</span>'))
          $div.append(' ')
          $div.append(ctx.i8n.newEmails)
          $div.append(' ')
          $div.append($link)
          document.title = ctx.i8n.newEmails
        })
      }
      window.setInterval(checkForNewEmails, 1000 * 60 * 5)
    })()
  })
})(window.jQuery, window.flask_jinja_context__base, window.flask_jinja_context__base.appRoot)
