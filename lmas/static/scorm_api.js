// static/scorm_api.js
var API = {
    initialized: false,
    data: {},
    lastError: "0",  // pipwerks expects error codes

    LMSInitialize: function() {
        console.log("LMSInitialize called");
        this.initialized = true;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSInitialize' })
        }).then(response => console.log("LMSInitialize response:", response));
        return "true";
    },

    LMSSetValue: function(key, value) {
        console.log(`LMSSetValue called: ${key}=${value}`);
        if (!this.initialized) {
            this.lastError = "101";  // General exception
            return "false";
        }
        this.data[key] = value;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSSetValue', key: key, value: value })
        }).then(response => console.log("LMSSetValue response:", response));
        this.lastError = "0";  // No error
        return "true";
    },

    LMSGetValue: function(key) {
        console.log(`LMSGetValue called: ${key}`);
        if (!this.initialized) {
            this.lastError = "101";
            return "";
        }
        this.lastError = "0";
        return this.data[key] || "";
    },

    LMSFinish: function() {
        console.log("LMSFinish called");
        if (!this.initialized) {
            this.lastError = "101";
            return "false";
        }
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSFinish' })
        }).then(response => console.log("LMSFinish response:", response));
        this.initialized = false;
        this.lastError = "0";
        return "true";
    },

    LMSCommit: function() {
        console.log("LMSCommit called");
        if (!this.initialized) {
            this.lastError = "101";
            return "false";
        }
        this.lastError = "0";
        return "true";
    },

    LMSGetLastError: function() {
        console.log("LMSGetLastError called:", this.lastError);
        return this.lastError;
    },

    LMSGetErrorString: function(errorCode) {
        console.log("LMSGetErrorString called:", errorCode);
        return "Error " + errorCode;
    },

    LMSGetDiagnostic: function(errorCode) {
        console.log("LMSGetDiagnostic called:", errorCode);
        return "Diagnostic for " + errorCode;
    }
};
console.log("scorm_api.js loaded, defining window.API");
window.API = API;