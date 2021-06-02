# JavaScript

In this folder you can write JavaScript code to be used in the client side using the [method](/django_pdr/methods.py) ```make_script(file_name, *args)``` where you can as well insert arguments from the python runtime to the template JavaScript code. 

## Example:
If you have the file **hello.js** with the content:
```JS
for(var i=0; i<{1} i++){
    console.log('Hello {0}');
}
```
And then run the following python code:
```py
from .methods import make_script

print(make_script('hello', 'World', 3))
```
It will print:
```js
for(var i=0; i<3 i++){
    console.log('Hello World');
}
```
Where it uses the python string.format(*args) function to insert variables into the template.
Thus, the number inside the curly brackets is the order of the variable when making the function call.