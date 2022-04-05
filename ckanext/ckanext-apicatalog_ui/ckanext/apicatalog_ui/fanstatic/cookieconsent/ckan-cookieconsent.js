ckan.module('cookie_consent', function (jQuery){
    return {
        initialize: function() {
            window.cookieconsent.initialise({
                container: document.getElementById("cookie_consent"),
                position: "bottom",
                type: "opt-in",
                static: false,
                theme: "suomifi",
                content: {
                    policy: this._('Cookie Policy'),
                    message: this._('This website uses cookies to ensure you get the best experience on our website.'),
                    allow: this._('Allow cookies'),
                    deny: this._('Decline'),
                    link: this._('Learn more')

                },
                onStatusChange: function(status, chosenBefore) {
                    let type = this.options.type;
                    let didConsent = this.hasConsented();
                    if (type === 'opt-in' && didConsent) {
                        console.log("enable cookies")
                        window.location.reload();
                    }
                    if (type === 'opt-in' && !didConsent) {
                        console.log("disable cookies")
                        window.location.reload();
                    }
                }
            }, this.initPopupExtra)
        },
        // When popup is initialized, init yet extra listeners for keyboard
        initPopupExtra: function(popup) {
            // Check that element actually exists to avoid errors about undefined variable
            if (popup.element) {
                const allowBtn = popup.element.querySelector('.cc-allow');
                const denyBtn = popup.element.querySelector('.cc-deny');

                $(allowBtn).keydown(function(e) {
                    if (e.which === 13) {
                        popup.setStatus('allow');
                    }
                });
                $(denyBtn).keydown(function(e) {
                    if (e.which === 13) {
                        popup.setStatus('deny');
                    }
                });
                console.log(allowBtn, denyBtn)
            }
        }
    }
})
