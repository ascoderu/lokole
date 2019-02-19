(function($) {
var API_BASE = '/api/mkwvconf';

var $modal = $('#wvdial-modal');
var $countrySelect = $('#wvdial-country');
var $providerSelect = $('#wvdial-provider');
var $apnSelect = $('#wvdial-apn');
var $submitButton = $('#generate-wvdial-config');

function updateModalState() {
  var country = $countrySelect.val();
  var provider = $providerSelect.val();
  var apn = $apnSelect.val();

  var providerDisabled = !country;
  var apnDisabled = !country || !provider;
  var submitDisabled = !country || !provider || !apn;

  $providerSelect.prop('disabled', providerDisabled);
  $apnSelect.prop('disabled', apnDisabled);
  $submitButton.prop('disabled', submitDisabled);

  if (providerDisabled) $providerSelect.empty();
  if (apnDisabled) $apnSelect.empty();
}

function autoSelectOption($select) {
  var options = $select.find('option');

  var hasDummyOption = options.length > 0 && options[0].value === '';
  var hasOnlyOneRealOption = hasDummyOption && options.length === 2;

  if (hasOnlyOneRealOption) {
    $select.val(options[1].value).trigger('change');
  }
}

function populateSelect($select, items) {
  $('<option/>').text('').appendTo($select);

  items.forEach(function(item) {
    $('<option/>').text(item).appendTo($select);
  });

  autoSelectOption($select);
}

$modal.on('show.bs.modal', function() {
  $.getJSON(API_BASE + '/', function(response) {
    populateSelect($countrySelect, response.countries);
  });

  updateModalState();
});

$countrySelect.on('change', function() {
  var country = $countrySelect.val();

  if (country) {
    $providerSelect.empty();
    $apnSelect.empty();

    $.getJSON(API_BASE + '/' + country, function(response) {
      populateSelect($providerSelect, response.providers);
    });
  }

  updateModalState();
});

$providerSelect.on('change', function() {
  var provider = $providerSelect.val();
  var country = $countrySelect.val();

  if (country && provider) {
    $apnSelect.empty();

    $.getJSON(API_BASE + '/' + country + '/' + provider, function(response) {
      populateSelect($apnSelect, response.apns);
    });
  }

  updateModalState();
});

$apnSelect.on('change', function() {
  updateModalState();
});

$submitButton.on('click', function() {
  var country = $countrySelect.val();
  var provider = $providerSelect.val();
  var apn = $apnSelect.val();

  if (country && provider && apn) {
    $.getJSON(API_BASE + '/' + country + '/' + provider + '/' + apn, function(response) {
      $('#wvdial').val(response.config);
      $('#sim_type').val('wvdial');
      $modal.modal('hide');
    });
  }
});
})(window.jQuery);
