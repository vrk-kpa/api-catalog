this.ckan.module('datepicker', function (jQuery, _) {
  return {
    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.ready(this._onReady);
    },

    _onReady: function() {
      var editor = $(this.el).datetimepicker();

      if($(this.el.attr('autosubmit'))) {
        editor.on('dp.change', () => {
          editor.parents('form:first').submit()
        });
      }
    }
  }
});
