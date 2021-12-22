'use strict';

/*
  Code to set the value of field-private to reflect the value of field-visibility. Note that the field-private is not
  displayed (display: none;).
*/

this.ckan.module('custom-dataset-visibility', function($) {
  return {

    initialize: function () {
      // Run the code once in the case of the visibility being already selected on page load (e.g. when opening the subsystem
      // in an edit mode)
      this.setVisibility();
      this.listenToChanges();
    },

    listenToChanges: function() {
      var el = $('#field-visibility-true');
      var el2 = $('#field-visibility-false');

      // Set the radio buttons to listen to changes to their value.
      el.on('change', (function () {
        this.setVisibility();
      }).bind(this));

      el2.on('change', (function () {
        this.setVisibility();
      }).bind(this));
    },

    setVisibility: function() {
      var visibilityPublic = $('#field-visibility-true')[0];
      var visibilityLimited = $('#field-visibility-false')[0];
      var fieldPrivate = $('#field-private')[0];

      // Yes, these are kind of backwards but imo it's more logical to have visibility be true when it's set
      // to public
      if (visibilityPublic.checked) {
        fieldPrivate.value = 'False'; // The dataset isn't private
      } else if (visibilityLimited.checked) {
        fieldPrivate.value = 'True'; // THe dataset is private
      }
    }
  }
})
