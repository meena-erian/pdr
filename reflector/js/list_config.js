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