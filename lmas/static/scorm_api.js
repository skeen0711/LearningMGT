// static/scorm_api.js
var API = {
    initialized: false,
    data: {},
    lastError: "0",

    LMSInitialize: function(param) {
        console.log("LMSInitialize called with param:", param);
        if (param !== "") {
            this.lastError = "201";  // Argument error
            return "false";
        }
        this.initialized = true;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSInitialize' })
        }).then(response => console.log("LMSInitialize response:", response))
          .catch(error => console.error("LMSInitialize fetch error:", error));
        this.lastError = "0";
        return "true";
    },

    LMSFinish: function(param) {
        console.log("LMSFinish called with param:", param);
        if (param !== "") {
            this.lastError = "201";
            return "false";
        }
        if (!this.initialized) {
            this.lastError = "301";  // Not initialized
            return "false";
        }
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSFinish' })
        }).then(response => console.log("LMSFinish response:", response))
          .catch(error => console.error("LMSFinish fetch error:", error));
        this.initialized = false;
        this.lastError = "0";
        return "true";
    },

    LMSGetValue: function(element) {
        console.log("LMSGetValue called:", element);
        if (!this.initialized) {
            this.lastError = "301";
            return "";
        }
        this.lastError = "0";
        return this.data[element] || "";
    },

    LMSSetValue: function(element, value) {
        console.log(`LMSSetValue called: ${element}=${value}`);
        if (!this.initialized) {
            this.lastError = "301";
            return "false";
        }
        this.data[element] = value;
        fetch('/scorm_api', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'LMSSetValue', key: element, value: value })
        }).then(response => console.log("LMSSetValue response:", response))
          .catch(error => console.error("LMSSetValue fetch error:", error));
        this.lastError = "0";
        return "true";
    },

    LMSCommit: function(param) {
        console.log("LMSCommit called with param:", param);
        if (param !== "") {
            this.lastError = "201";
            return "false";
        }
        if (!this.initialized) {
            this.lastError = "301";
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
console.log("scorm_api.js loaded, defining window.API and API_1484_11");
window.API = API;          // SCORM 1.2
window.API_1484_11 = API;  // SCORM 2004