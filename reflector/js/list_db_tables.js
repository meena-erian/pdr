var dbSelect = this;
if (!dbSelect.value) return;
api = `/api/db/${this.value}/tables`;
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