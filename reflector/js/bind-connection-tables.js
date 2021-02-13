//Variables
// {0} target select element 
var connectionSelect = this;
if (!connectionSelect.value) return;
api = `/api/db/${this.value}/tables`;
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