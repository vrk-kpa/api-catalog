'use strict';

/*
  Copy the title from "Title in Finnish" field to "Title in Data Exchange Layer" (Palveluväylä)
  field and to URL slug field.
  In the process first lowercase the whole string then capitalize the words separated by spaces, replace diacritics
  with their non-accented versions and remove non-alphanumerical characters.
*/

this.ckan.module('title-to-del-title-and-url-slug', function($) {
  return {

    initialize: function () {
      this.listenToChanges();
    },

    listenToChanges: function() {
      var el = $('#field-title_translated-fi');

      // Run the code once in the case of the title being already filled in on page load (e.g. when opening the subsystem
      // in an edit mode)
      this.processTitle(el[0]);

      // Set the input element to listen to changes to its value
      el.on('input', (function () {
        this.processTitle(el[0]);
      }).bind(this));
    },

    processTitle: function(element) {
      var capitalizedWords = this.processWords(element.value, true);
      var dashSeparatedWords = this.processWords(element.value, false);

      $('#title_in_data_exchange_layer')[0].value = capitalizedWords;
      $('.dataset-url-slug')[0].value = dashSeparatedWords
    },

    // Yes, extracting the loop into a function results in it being run multiple times when it could only run once
    // (well, twice) but it really shouldn't matter in this context
    processWords: function(string, shouldBeCapitalized) {
      var stringToProcess = string;
      if (string === undefined) stringToProcess = '';
      var words = stringToProcess.split(' ');
      var wordsAfterProcessing = '';
      for (var i = 0; i < words.length; i++)
      {
        var word = this.processWord(words[i], shouldBeCapitalized);
        if (shouldBeCapitalized) {
          wordsAfterProcessing = wordsAfterProcessing + word;
        } else {
          if (i === 0) {
            wordsAfterProcessing = wordsAfterProcessing + word;
          } else {
            wordsAfterProcessing = wordsAfterProcessing + "-" + word;
          }
        }
      }

      return wordsAfterProcessing;
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
    },

    capitalize: function(str) {
      var capitalizedCharacter = str.charAt(0).toUpperCase();
      return capitalizedCharacter + str.slice(1);
    }
  }
})
