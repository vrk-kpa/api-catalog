'use strict';

this.ckan.module('collapsible', function($) {
  return {

    initialize: function() {
      this.activateCollapsibles()
    },

    activateCollapsibles: function() {
      var elements = $('.collapsible');

      for (var i = 0; i < elements.length; i++) {
        elements[i].addEventListener('click', function () {
          this.classList.toggle('collapsible-active');
          var content = this.nextElementSibling;
          if (content.style.display === 'block') {
            content.style.display = 'none';
          } else {
            content.style.display = 'block';
          }
        });
      }
    }
  }
})