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
api = `/api/db/config`;
console.log('Fetching: ', api);
fetch(api).then(function (r) {
    r.json().then(function (j) {
        var editor = document.querySelectorAll(".ace_editor")[0].env.editor;
        editor.setValue(JSON.stringify(j[source.value].config, null, 2));
    });
});