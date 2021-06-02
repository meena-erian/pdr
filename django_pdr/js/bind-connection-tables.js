//Variables
// {0} target select element 
/**
 * This script is meant to be interpreted whenever the user selects a destination database 
 *  from the HTML select element for the Reflection admin form.
 * 
 * Once triggered, it connects to the API `/api/db/<dbId>/tables`, retrives a list
 * of all tables existing in the selected database and inserts them in the DOM as a
 * an html <datalist> element for the destination table input of the form
 */
var connectionSelect = this;
if (!connectionSelect.value) return;
/**
 * First, lets find the current relative base path of the django_pdr app
 *  based on the last index of '/django_pdr/ in the url.
 */
var pureBaseIndex = location.pathname.lastIndexOf('/reflection/');
var pureBasePath = location.pathname.slice(0, pureBaseIndex);
var api = `${ pureBasePath }/sourcetable/${ this.value }/tables`;
fetch(api).then(function (r) {
    r.json().then(function (tables) {
        var tableSelect = document.querySelector(`#{0}`);
        if (!tableSelect) return;
        tableSelect.setAttribute(`list`, `connection_tables_dlist`);
        var dlist = document.querySelector(`#connection_tables_dlist`);
        if (!dlist) {
            dlist = document.createElement(`datalist`);
            dlist.id = `connection_tables_dlist`;
            tableSelect.parentNode.insertBefore(dlist, tableSelect.nextSibling);
        }
        while (dlist.firstChild) {
            dlist.removeChild(dlist.firstChild);
        }
        if (tables) {
            console.log(tables);
            tableSelect.removeAttribute(`disabled`);
            tables.forEach(
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