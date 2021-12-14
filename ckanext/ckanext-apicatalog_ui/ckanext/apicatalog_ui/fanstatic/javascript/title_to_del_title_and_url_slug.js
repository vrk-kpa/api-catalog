'use strict';

/*
  Copy the title from "Title in Finnish" field to "Title in Data Exchange Layer" (Palveluväylä)
  field and to URL slug field.
  In the process first lowercase the whole string then capitalize the words separated by spaces, replace diacritics
  with their non-accented versions and remove non-alphanumerical characters.
*/

this.ckan.module('title_to_del_title_and_url_slug', function($) {
  return {

    initialize: function () {
      this.listenToChanges();
    },

    listenToChanges: function() {
      var el = $('#field-title_translated-fi');
      el.on('input', (function () {
        var string = el[0].value;
        var words = string.split(' ');
        var capitalizedWords = '';
        var dashSeparatedWords = '';

        for (var i = 0; i < words.length; i++)
        {
          var capitalizedWord = this.processWord(words[i], true);
          var word = this.processWord(words[i], false);

          capitalizedWords = capitalizedWords + capitalizedWord;

          if (i === 0) {
            dashSeparatedWords = dashSeparatedWords + word;
          } else {
            dashSeparatedWords = dashSeparatedWords + "-" + word;
          }
        }

        $('#title_in_data_exchange_layer')[0].value = capitalizedWords;
        $('#dataset-url-slug')[0].textContent = dashSeparatedWords
      }).bind(this));
    },

    capitalize: function(str) {
      var capitalizedCharacter = str.charAt(0).toUpperCase();
      return capitalizedCharacter + str.slice(1);
    },

    processWord: function(word, shouldBeCapitalized) {
      var wordBeingProcessed = word.trim(); // Remove the remaining whitespace from the string(s)
      wordBeingProcessed = wordBeingProcessed.toLowerCase(); // Lowercase the whole string before capitalization & for URL slug

      if (shouldBeCapitalized) {
        wordBeingProcessed = this.capitalize(wordBeingProcessed);
      }

      // Replace diacritics with their non-accented versions
      // Also removes non-alphanumerical characters
      wordBeingProcessed = wordBeingProcessed.normalize('NFKD').replace(/[^\w]/g, '');

      return wordBeingProcessed;
    }
  }
})
