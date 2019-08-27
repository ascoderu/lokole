(function ($, ctx) {
  $(document).ready(function () {
    (function setUserTimezone () {
      var timezoneOffsetMinutes = new Date().getTimezoneOffset()
      $(ctx.selectors.timezoneOffsetMinutesField).val(timezoneOffsetMinutes)
    })()
  })
})(window.jQuery, window.flask_jinja_context__register)
