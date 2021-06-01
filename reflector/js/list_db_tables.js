/**
 * This script is meant to be interpreted whenever the user selects a database 
 *  from the HTML select element for the SourceTable admin form.
 * 
 * Once triggered, it connects to the API `/api/db/<dbId>/tables`, retrives a list
 * of all tables existing in the selected database and inserts them in the DOM as a
 * an html <datalist> element for the table input of the form
 */
var dbSelect = this;
if (!dbSelect.value) return;
/**
 * First, lets find the current relative base path of the reflector app
 *  based on the last index of '/reflector/ in the url.
 */
var pureBaseIndex = location.pathname.lastIndexOf('/sourcetable/');
var pureBasePath = location.pathname.slice(0, pureBaseIndex);
var api = `${ pureBasePath }/sourcetable/${ this.value }/tables`;
fetch(api).then(function (r) {
    r.json().then(function (j) {
        var tableSelect = document.querySelector(`#id_source_table`);
        if (!tableSelect) return;
        tableSelect.setAttribute(`list`, `db_tables_dlist`);
        var dlist = document.querySelector(`#db_tables_dlist`);
        if (!dlist) {
            dlist = document.createElement(`datalist`);
            dlist.id = `db_tables_dlist`;
            tableSelect.parentNode.insertBefore(dlist, tableSelect.nextSibling);
        }
        while (dlist.firstChild) {
            dlist.removeChild(dlist.firstChild);
        }
        if (j.length) {
            console.log(j);
            tableSelect.removeAttribute(`disabled`);
            j.forEach(
                function (table) {
                    var item = document.createElement('option');
                    item.innerText = table;
                    dlist.append(item);
                }
            );
        }
        else {
            tableSelect.setAttribute(`disabled`, `disabled`);
        }
    })
});