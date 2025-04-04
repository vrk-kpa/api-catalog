this.ckan.module('modal-dialog', function (jQuery) {
  return {
    options: {
      contentId: '',
      withData: '',
      title: '',
      okButtonLabel: '',
      cancelButtonLabel: '',

      template: [
        '<div class="modal fade">',
        '<div class="modal-dialog">',
        '<div class="modal-content">',
        '<div class="modal-header">',
        '<button type="button" class="close" data-dismiss="modal">×</button>',
        '<h3 class="modal-title"></h3>',
        '</div>',
        '<div class="modal-body"></div>',
        '<div class="modal-footer">',
        '<button class="btn btn-primary"></button>',
        '<button class="btn btn-secondary btn-cancel"></button>',
        '</div>',
        '</div>',
        '</div>',
        '</div>'
      ].join('\n')
    },

    initialize: function () {
      jQuery.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
      // Detach content node
      this.content = document.getElementById(this.options.contentId);
      this.content.parentElement.removeChild(this.content);
    },

    confirm: function () {
      this.sandbox.body.append(this.createModal());
      this.modal.modal('show');

      this.modal.css({
        'margin-top': this.modal.height() * -0.5,
        'top': '50%'
      });
    },

    performAction: function () {
      var form = jQuery('<form/>', {
        action: this.el.attr('href'),
        method: 'POST'
      });

      if (this.options.withData) {
        var form = this.content.closest('form');
      }

      form.submit();
    },

    createModal: function () {
      if (!this.modal) {
        var element = this.modal = jQuery(this.options.template);
        element.on('click', '.btn-primary', this._onConfirmSuccess);
        element.on('click', '.btn-cancel', this._onConfirmCancel);
        element.modal({show: false});

        element.find('.modal-title').text(this.options.title);
        element.find('.modal-body').append(this.content);
        element.find('.btn-primary').text(this.options.okButtonLabel || this._('Confirm'));
        element.find('.btn-cancel').text(this.options.cancelButtonLabel || this._('Cancel'));
      }
      return this.modal;
    },

    _onClick: function (event) {
      event.preventDefault();
      this.confirm();
    },

    _onConfirmSuccess: function (event) {
      this.performAction();
    },

    _onConfirmCancel: function (event) {
      this.modal.modal('hide');
    }
  };
});

