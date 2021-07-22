def make_query(query_name, *args):
    """
    A function used to generate SQL code from SQL templates
    saved in the SQL folder.

    For more information see django_pdr/sql/README.MD
    """
    import os
    import django_pdr
    file_path = os.path.join(
        os.path.dirname(django_pdr.__file__),
        "sql",
        query_name + ".sql"
    )
    f = open(file_path)
    d = f.read()
    return d.format(*args)


def exec_query(engine, query_name, *args):
    """
    A wrapper function for make_query where in addition to
    generating SQL code using make_query it also excecutes
    the code using provided engine.
    """
    query = make_query(query_name, *args)
    query = query.split('\n\n\n')
    with engine.connect().execution_options(autocommit=True) as dbconnection:
        for statment in query:
            dbconnection.execute(statment)


def make_script(script_name, *args):
    """
    A function used to generate JavaScript code based on the JavaScript
    templates in the js folder. For more information see
    django_pdr/js/README.MD
    """
    import os
    import django_pdr
    file_path = os.path.join(
        os.path.dirname(django_pdr.__file__),
        "js",
        script_name + ".js"
    )
    f = open(file_path)
    d = f.read()
    import re
    d = re.sub(r'\{(\w*)\}', r'(((<<<\1>>>)))', d)
    d = re.sub('{', '{{', d)
    d = re.sub('}', '}}', d)
    d = re.sub(r'\(\(\(\<\<\<(\w*)\>\>\>\)\)\)', r'{\1}', d)

    return d.format(*args)
