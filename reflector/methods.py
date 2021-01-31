def make_query(query_name, *args):
    import os
    import reflector
    file_path = "{0}\\sql\\{1}.sql".format(os.path.dirname(reflector.__file__),query_name)
    f = open(file_path)
    d = f.read()
    return d.format(*args)