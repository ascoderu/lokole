(function($) {
$(document).ready(function() {

(function setUserTimezone() {
  var timezoneOffsetMinutes = (new Date()).getTimezoneOffset();
  document.getElementById(register_user_form.timezone_offset_minutes.id).value = timezoneOffsetMinutes;
}());

});
})(window.jQuery);
