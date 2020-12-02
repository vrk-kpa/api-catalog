window.cookieconsent.initialise({
    container: document.getElementById("cookie_consent"),
    position: "top",
    type: "opt-in",
    static: false,
    theme: "suomifi",
    onInitialise: function (status){
        let type = this.options.type;
        let didConsent = this.hasConsented();
        if (type === 'opt-in' && didConsent) {
            console.log("enable cookies")
        }
        if (type === 'opt-out' && !didConsent) {
            console.log("disable cookies")
        }
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
})