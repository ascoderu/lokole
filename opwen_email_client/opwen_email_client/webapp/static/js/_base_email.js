(function ($, appRoot) {
  $(document).ready(function () {
    (function activateLazyload () {
      $('.email-body img').lazyload()
    })();

    (function markEmailsAsReadOnOpen () {
      $('.panel-info').click(function () {
        var $el = $(this)
        if ($el.hasClass('panel-info')) {
          var emailId = $el.data('email_id')
          if (emailId) {
            $.ajax({
              url: appRoot + '/email/read/' + emailId,
              success: function () {
                $el.removeClass('panel-info').addClass('panel-default')
              }
            })
          }
        }
      })
    })();

    (function printEmailOnPrintButtonClick () {
      $('.print-trigger').click(function () {
        var $printRoot = $(this).closest('.print-root')
        $printRoot.printThis()
      })
    })()
  })
})(window.jQuery, window.flask_jinja_context__base.appRoot)
