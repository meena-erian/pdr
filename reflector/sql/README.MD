# SQL

In this folder, you can write SQL code to add more advanced functionalities. However, please try to use SQLAlchemy instead whenever applicable because raw SQL code is less manageable than SQLAlchemy's abstraction layer. Files in this folder are meant to be loaded using the [methods](/reflector/methods.py) ```make_query(file_name, *args)``` or ```exec_query(engine, file_name, *args)``` where you can as well insert arguments from the python runtime to the template SQL code. 

## Example:
If you have the file **listall.sql** with the content:
```SQL
SELECT * FROM {0};
```
Running 
```py
print(make_query('listall', 'employees'))
```
Will print:
```SQL
SELECT * FROM employees;
```
and running 
```py
exec_query(engine, 'listall', 'employees')
```
will execute
```SQL
SELECT * FROM employees;
```

Where it uses the python string.format(*args) function to insert variables into the template.
Thus, the number inside the curly brackets is the order of the variable when making the function call.

## **WARNING**

The make_query and exec_query functions do not escape arguments. 
When using these functions you must make sure arguments are properly
 escaped before using them in such functions, in order to avoid SQL injection.

<br />
<br />
<br />


## Rules and Conventions for this folder

Before writing any SQL files in this director, 
Please read the following rules as failing to comply with them will conflict with the functionality of the SQL methods.

### **Rule#1 Dialect-Specific Directory**

All SQL files must be grouped in directories where each directory's name is 
the same as the SQL dialect used in SQL queries inside of that directory. 
    An SQL file can be placed directly inside the sql directory (not inside any 
    child directories) only if the SQL syntax in it is native SQL syntax that 
    can be used across all SQL RDBMS.
A complete list of all used dialects can be found inside datasources class
 in [models.py](/reflector/models.py)


### **Rule#2 Complete Compatibility**

When writing any SQL file in a dialect directory as explained in Rule#1, Files with 
the same name and functionality must be added to all other dialects as well after 
translating to each dialect whenever applicable.


### **Rule#3 Predefine Variables**

All variables being using in an SQL template file must be defined at the 
begging of the file. (if any)


### **Rule#3 self-explainatory filnames**

The name of each SQL file should provide a clear idea of what the queries inside of it
does, just like a function name.