(function($) {
$(document).ready(function() {

(function activateLazyload() {
  $(".email-body img").lazyload();
}());

(function markEmailsAsReadOnOpen() {
  $(".panel-info").click(function() {
    var $el = $(this);
    if ($el.hasClass("panel-info")) {
      var email_id = $el.data("email_id");
      if (email_id) {
        $.ajax({
          url: "/email/read/" + email_id,
          success: function() {
            $el.removeClass("panel-info").addClass("panel-default");
          }
        });
      }
    }
  });
}());

(function printEmailOnPrintButtonClick() {
  $(".print-trigger").click(function() {
    var $printRoot = $(this).closest(".print-root");
    $printRoot.printThis();
  });
}());

});
})(window.jQuery);
