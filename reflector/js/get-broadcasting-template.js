var source = document.querySelector("#id_source_table");
if (!source.value) return;
api = `/api/broadcaster/${source.value}/fields`;
console.log('Fetching: ', api);
fetch(api).then(function (r) {
    r.json().then(function (j) {
        var editors = document.querySelectorAll(".ace_editor");
        var sourceEditor = editors[0].env.editor;
        var destinationEditor = editors[1].env.editor;
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
            let columns_array = Object.keys(j.columns);
            reflection_template_destination.insert_query = `insert into ${ destination_table }(${ columns_array.join(', ') })`;
            reflection_template_destination.insert_query += `\nvalues (${ columns_array.map(c => `{${ c }}`).join(', ')});`;
            reflection_template_destination.update_query = `update ${ destination_table } set ${ columns_array.map(f => `${ f } = {${ f }}`).join(', ')} where ${ j.key } = {${ j.key }};`;
            reflection_template_destination.delete_query = `delete from ${ destination_table } where ${ j.key } = {${ j.key }};`;
            sourceEditor.setValue(JSON.stringify(reflection_source, null, 2));
            destinationEditor.setValue(JSON.stringify(reflection_template_destination, null, 2));
        }
        else {
            sourceEditor.setValue("");
            destinationEditor.setValue("");
        }
    })
});
