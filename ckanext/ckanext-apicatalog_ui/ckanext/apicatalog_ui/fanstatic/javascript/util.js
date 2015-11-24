// Create a submit handler function that redirects browser to a url 
// if the supplied form has not changed since the handler was created.
ckan.module('form_redirect_if_unchanged', function ($, _) {
  return {
    initialize: function () {
      var form;
      var options = this.options;
      if(options.formSelector) {
        form = $(options.formSelector, this.el);
      } else {
        form = $(this.el);
      }
      var initialContent = form.serialize();
      form.submit(function(e) {
        var currentContent = form.serialize();
        if(initialContent === currentContent) {
          window.location = options.cancelUrl;
          e.preventDefault();
        }
      });
    }
  };
});


