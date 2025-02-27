// static/scorm_api.js
var API = {
    initialized: false,
    data: {},

    LMSInitialize: function() {
        console.log("LMSInitialize called");  // Browser debug
        this.initialized = true;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSInitialize' })
        }).then(response => console.log("LMSInitialize response:", response));
        return "true";
    },

    LMSSetValue: function(key, value) {
        console.log(`LMSSetValue called: ${key}=${value}`);  // Browser debug
        if (!this.initialized) return "false";
        this.data[key] = value;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSSetValue', key: key, value: value })
        }).then(response => console.log("LMSSetValue response:", response));
        return "true";
    },

    LMSGetValue: function(key) {
        console.log(`LMSGetValue called: ${key}`);  // Browser debug
        return this.data[key] || "";
    },

    LMSFinish: function() {
        console.log("LMSFinish called");  // Browser debug
        if (!this.initialized) return "false";
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSFinish' })
        }).then(response => console.log("LMSFinish response:", response));
        this.initialized = false;
        return "true";
    },

    LMSCommit: function() {
        console.log("LMSCommit called");  // Browser debug
        return "true";
    }
};
console.log("scorm_api.js loaded, defining window.API");  // Confirm loading
window.API = API;