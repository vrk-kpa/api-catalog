this.ckan.module('form-change-listener', function($) {
  return {
    /* options object can be extended using data-module-* attributes */
    options: {
      confirmModalSelector: null, // selector for modal
    },

    initialize: function () {
      console.log("Init", this);
      if (this.options?.confirmModalSelector === null) {
        throw new Error("Can't initialize form listener without modal selector");
      }

      this.confirmModal = document.querySelector(this.options.confirmModalSelector);
      this.listenChanges();
      this.modal = new Modal(this.confirmModal);
    },

    // Listen changes in form and set's state when changed
    listenChanges: function() {
      this.el.find(':input').change((function () {
        this.el.data('form-changed', true);
      }).bind(this));

      // $(window).bind('beforeunload', (function(e) {
      //   console.log(e);
      //   if (this.el.data('form-changed') === true) {
      //     return "Are you sure you want to exit page with unsaved changes?"
      //   }
      //   return;
      // }).bind(this));
    }
  }
})
