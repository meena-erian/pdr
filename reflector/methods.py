def make_query(query_name, *args):
    import os
    import reflector
    file_path = "{0}\\sql\\{1}.sql".format(os.path.dirname(reflector.__file__),query_name)
    f = open(file_path)
    d = f.read()
    return d.format(*args)

def exec_query(engine, query_name, *args):
    query = make_query(query_name, *args)
    query = query.split('\n\n\n')
    with engine.connect().execution_options(autocommit=True) as dbconnection:
        for statment in query:
            dbconnection.execute(statment)

def make_script(script_name, *args):
    import os
    import reflector
    file_path = "{0}\\js\\{1}.js".format(os.path.dirname(reflector.__file__),script_name)
    f = open(file_path)
    d = f.read()
    import re
    d = re.sub(r'\{(\w*)\}', r'(((<<<\1>>>)))',d)
    d = re.sub('{', '{{', d)
    d = re.sub('}', '}}', d)
    d = re.sub(r'\(\(\(\<\<\<(\w*)\>\>\>\)\)\)', r'{\1}',d)
    return d.format(*args)