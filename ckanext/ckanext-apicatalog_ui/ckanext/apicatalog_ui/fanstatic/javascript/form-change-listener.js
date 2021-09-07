this.ckan.module('form-change-listener', function($) {
  return {
    /* options object can be extended using data-module-* attributes */
    options: {},

    initialize: function () {
      this.listenChanges();
    },

    // Listen changes in form and initialize confirm dialog to prevent accidental page changes
    listenChanges: function() {
      // If form is submitted, we shouldn't pop up dialog to confirm exit from page
      // so unbind beforeunload in that case
      this.el.submit(this.unbindBeforeunload);
      this.el.find(':input').change((function () {
        // Binding beforeunload prevents browsers from caching Back-Forward cache, so init only once form changes
        // https://developers.google.com/web/updates/2018/07/page-lifecycle-api#the-beforeunload-event
        if (this.el.data('form-changed') !== true) {
          this.bindBeforeunload();
        }
        this.el.data('form-changed', true);
      }).bind(this));
    },

    bindBeforeunload: function() {
      $(window).bind('beforeunload', this.beforeunload.bind(this));
    },

    unbindBeforeunload: function() {
      $(window).unbind('beforeunload', this.beforeunload);
    },

    beforeunload: function(e) {
      console.log(e);
      e.returnValue = "Are you sure you want to exit page with unsaved changes?";
      return e;
    }
  }
})
