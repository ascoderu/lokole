(function($, ctx) {
$(document).ready(function() {

(function styleEmailAttachmentsField() {
  $(ctx.selectors.attachments).fileinput({
    showPreview: false,
    showUpload: false,
    msgSelected: "{n} " + ctx.i8n.filesSelected,
    layoutTemplates: {
      fileIcon: '<span class="fa fa-file-o"></span>&nbsp;',
    },
    removeTitle: "",
    removeIcon: '<span class="fa fa-trash-o"></span>',
    removeLabel: ctx.i8n.remove,
    browseLabel: ctx.i8n.chooseFiles,
    browseIcon: '<span class="fa fa-paperclip"></span>',
    browseClass: 'btn btn-default'
  });
}());

(function turnEmailBodyFieldIntoRichEditor() {
  $(ctx.selectors.formBody).wysihtml5({
    toolbar: {
      "font-styles": false,
      "link": false,
      "image": false,
      "outdent": false,
      "indent": false,
      "blockquote": false,
      "fa": true,
    },
    customTemplates: {
      emphasis: function(context) {
        return '<li><div class="btn-group">'
                + '<a title="' + ctx.i8n.bold + '" class="btn btn-default" data-wysihtml5-command="bold" tabindex="-1" href="javascript:;" unselectable="on">'
                + '  <span class="fa fa-bold"></span></a>'
                + '<a title="' + ctx.i8n.italic + '" class="btn btn-default" data-wysihtml5-command="italic" tabindex="-1" href="javascript:;" unselectable="on">'
                + '  <span class="fa fa-italic"></span></a>'
                + '<a title="' + ctx.i8n.underline + '" class="btn btn-default" data-wysihtml5-command="underline" tabindex="-1" href="javascript:;" unselectable="on">'
                + '  <span class="fa fa-underline"></span></a>'
                + '</div></li>';
      },
      lists: function(context) {
        return '<li><div class="btn-group">'
                + '<a title="' + ctx.i8n.unorderedList + '" class="btn btn-default" data-wysihtml5-command="insertUnorderedList" tabindex="-1" href="javascript:;" unselectable="on">'
                + '  <span class="fa fa-list-ul" aria-hidden="true"></span></a>'
                + '<a title="' + ctx.i8n.orderedList + '" class="btn btn-default" data-wysihtml5-command="insertOrderedList" tabindex="-1" href="javascript:;" unselectable="on">'
                + '  <span class="fa fa-list-ol" aria-hidden="true"></span></a>'
                + '</div></li>';
      }
    }
   });
 }());

});
})(window.jQuery, window.flask_jinja_context__email_new);
