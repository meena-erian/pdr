/**
 * This script is meant to be interpreted whenever the user changes the destination table
 *  or the source table in the from HTML elements for the Reflection admin form.
 * 
 * Once triggered, it connects to the API `/api/source/<sourceTableId>/fields`, retrives the structure
 * of of the selected source table and then it selects the DOM element for the destination_table and 
 * retrives from it the current value for the destination table. and based on thes values it generates
 * reflection configurations (Source fields, destination fields and reflections statment)
 */
var source = document.querySelector("#id_source_table");
if (!source.value) return;
api = `/api/source/${source.value}/fields`;
console.log('Fetching: ', api);
fetch(api).then(function (r) {
    r.json().then(function (j) {
        var editors = document.querySelectorAll(".ace_editor");
        var sourceEditor = editors[0].env.editor;
        var destinationEditor = editors[1].env.editor;
        var statmentEditor = editors[2].env.editor;
        var destination_table = document.querySelector("#id_destination_table").value;
        if(!destination_table.length) destination_table = 'destination_table';
        destination_table = destination_table.split('.').map(item => `"${ item }"`).join('.')
        if (j.columns) {
            var reflection_source = {
                "columns" : j.columns,
                "key" : j.key
            };
            var reflection_template_destination = {
                "columns" : j.columns,
                "key" : j.key
            };
            key_binding  = { };
            key_binding[j.key] = j.key;
            reflection_template_destination['key_binding'] = key_binding;
            let columns_array = Object.keys(j.columns);
            var update_query = `UPDATE\n\t${ destination_table }\nSET\n${ columns_array.map(f => `\t"${ f }" = :${ f }`).join(',\n')}\nWHERE\n\t"${ j.key }" = :${ j.key };`;
            sourceEditor.setValue(JSON.stringify(reflection_source, null, 2));
            destinationEditor.setValue(JSON.stringify(reflection_template_destination, null, 2));
            statmentEditor.setValue(update_query)
        }
        else {
            sourceEditor.setValue("");
            destinationEditor.setValue("");
        }
    })
});
