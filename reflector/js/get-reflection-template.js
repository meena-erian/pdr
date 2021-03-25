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
            var update_query = `UPDATE\n\t${ destination_table }\nSET\n${ columns_array.map(f => `\t${ f } = :${ f }`).join(',\n')}\nWHERE\n\t${ j.key } = :${ j.key };`;
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
