this.ckan.module('tablesorter', function($) {
  return {
    /* options object can be extended using data-module-* attributes */
    options: {},

    initialize: function () {
      this.el.tablesorter();
    }
  }
})
