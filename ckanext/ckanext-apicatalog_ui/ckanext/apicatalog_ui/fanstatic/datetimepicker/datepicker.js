// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module("datepicker", function($) {
  return {
    initialize: function() {
      //this.el.find("[data-datepicker]").each(function() {
        let dp = $(this.el)
          .datetimepicker({
            format: "YYYY-MM-DD"
          });

        if($(this.el.attr('autosubmit'))) {
          dp.on('dp.change', () => {
            this.el.parents('form:first').submit()
          });
        }
          /*.on("dp.hide", function(e) {
            if (!e.oldDate && e.date.isSame(moment(), "day")) {
              $(".advanced-search-form").submit();
            }

          })
          .on("dp.change", function(e) {
            if (!e.date && e.oldDate || e.oldDate && !e.date.isSame(e.oldDate, "day")) {
              $(".advanced-search-form").submit();
            }
        })*/;
      //});
    }
  };
});
