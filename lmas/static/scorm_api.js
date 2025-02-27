// static/scorm_api.js
var API = {
    initialized: false,
    data: {},

    LMSInitialize: function() {
        this.initialized = true;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSInitialize' })
        });
        return "true";
    },

    LMSSetValue: function(key, value) {
        if (!this.initialized) return "false";
        this.data[key] = value;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSSetValue', key: key, value: value })
        });
        return "true";
    },

    LMSGetValue: function(key) {
        return this.data[key] || "";
    },

    LMSFinish: function() {
        if (!this.initialized) return "false";
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSFinish' })
        });
        this.initialized = false;
        return "true";
    },

    LMSCommit: function() {
        return "true";
    }
};
window.API = API;