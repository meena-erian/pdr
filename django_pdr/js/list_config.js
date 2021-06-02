/**
 * This script is meant to be interpreted whenever the user selects an RDBMS type 
 *  from the HTML select element for the Database admin form.
 * 
 * Once triggered, if connects to the API `/api/db/config`, retrives a list
 * of all default configurations for supported RDBMS types and insets the 
 * default configuration for the selected type in the JSON config editor
 */
var source = document.querySelector("#id_source");
if (!source.value) return;
/**
 * First, lets find the current relative base path of the django_pdr app
 *  based on the last index of '/django_pdr/ in the url.
 */
var pureBaseIndex = location.pathname.lastIndexOf('/database/');
var pureBasePath = location.pathname.slice(0, pureBaseIndex);
var api = `${ pureBasePath }/database/config`;
console.log('Fetching: ', api);
fetch(api).then(function (r) {
    r.json().then(function (j) {
        var editor = document.querySelectorAll(".ace_editor")[0].env.editor;
        editor.setValue(JSON.stringify(j[source.value].config, null, 2));
    });
});