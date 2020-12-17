"use strict";

ckan.module("submit-on-change", function($) {
  return {
    initialize: function() {
      let submitTriggers = $('[data-submit]', this.el);
      submitTriggers.change(() => {
        $(this.el).submit()
      });
    }
  };
});

