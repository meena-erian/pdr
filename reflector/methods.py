def make_query(query_name, *args):
    import os
    import reflector
    file_path = "{0}\\sql\\{1}.sql".format(os.path.dirname(reflector.__file__),query_name)
    f = open(file_path)
    d = f.read()
    return d.format(*args)

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
    print(d)
    return d.format(*args)