// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module("mutexfield", function($) {
  return {
    initialize: function() {
      // Added timeout to make mutexfield hide non-active sections after other modules are initialized
      // so that this won't break dom-calculations.
      setTimeout(() => {
        $('[data-mutex-field]', this.el).each((i, el) => {
          let children = $('[data-mutex-value]', el);
          let mutexField = $(el).attr('data-mutex-field');
          let mutexElement = $(`[name=${mutexField}]`);

          const handleMutex = (newValue) => {
            children.each((i, child) => {
              let mutexValue = $(child).attr('data-mutex-value');
              $(child).toggleClass('hidden', newValue != mutexValue);
            });
          };
          handleMutex(mutexElement.val());
          mutexElement.change((ev) => {
            handleMutex(ev.target.value)
          });
        });
      }, 0);
    }
  };
});

