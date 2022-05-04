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
          var icons = $('.collapsible-icon');
          if (content.style.display === 'block') {
            content.style.display = 'none';
            for (var i = 0; i < icons.length; i++) {
              icons[i].classList.remove("fa-chevron-up")
              icons[i].classList.add("fa-chevron-down")
            }
          } else {
            content.style.display = 'block';
            for (var i = 0; i < icons.length; i++) {
              icons[i].classList.remove("fa-chevron-down")
              icons[i].classList.add("fa-chevron-up")
            }
          }
        });
      }
    }
  }
})