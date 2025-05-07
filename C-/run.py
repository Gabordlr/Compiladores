''' Gabriel Rodriguez De Los Reyes - A01027384 '''

from globalTypes import *
from customParser import *
from mainSemantica import *

f = open('sample.c-', 'r')
programa = f.read()
progLong = len(programa)
programa = programa + '$'
posicion = 0  # lee todo el archivo a compilar
# longitud original del programa
# agregar un caracter $ que represente EOF
# posición del caracter actual del string
# función para pasar los valores iniciales de las variables globales
globales(programa, posicion, progLong)

ERROR = False
AST, ERROR = parser(False)

if not ERROR:
    print("---------------- Semantica ----------------")
    semantica(AST, True)
