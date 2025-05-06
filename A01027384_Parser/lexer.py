''' Gabriel Rodriguez De Los Reyes - A01027384 '''

from LexerStatesTable import states_table
from globalTypes import TokenType, resreved_words, char_map, rewind_states, final_states

# Variables globales para el análisis léxico.
global programa, posicion, progLong
# La cadena del programa a analizar (se establecerá en globales())
programa = ""
posicion = 0    # Índice actual en la cadena
progLong = 0    # Longitud de la cadena del programa
current_line = 1   # Línea actual en el análisis
current_column = 1  # Columna actual en el análisis


class Lexer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Lexer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Inicializar solo una vez para preservar el estado de singleton.
        if not hasattr(self, '_initialized'):
            self.state_table = states_table
            self.final_states = final_states
            self.rewind_states = rewind_states
            self.initial_state = 0
            self._initialized = True

    def get_char_column(self, a: str) -> int:
        for column, chars in char_map.items():
            if a in chars:
                return column
        return len(char_map)

    def check_reserved_word(self, lex: str, token: TokenType):
        """
        Si el lexema coincide con alguna palabra reservada, se devuelve el enum correspondiente.
        De lo contrario, se devuelve el token original.
        """
        if lex in resreved_words:
            return resreved_words[lex]
        return token

    def get_token(self, return_eof=True):
        """
        Devuelve el siguiente token desde el 'programa' global comenzando en 'posicion'
        usando una estrategia de máxima absorción, ignorando espacios, tabulaciones y saltos de línea iniciales.
        También ignora comentarios en formato /* ... */

        Devuelve una tupla (token, lexema, línea, columna) donde:
        - token: un miembro de TokenType (o un miembro de ReservedWords si el lexema coincide),
                 o TokenType.ERROR si se encuentra un error.
        - lexema: la subcadena que constituye el token, con espacios extra eliminados.
        - línea: número de línea donde comienza el token.
        - columna: número de columna donde comienza el token.

        La variable global 'posicion' se actualiza al índice inmediatamente después del token.
        Si no se encuentra ningún token o se alcanza el marcador de fin ('$') al inicio (después de espacios),
        y return_eof es True, entonces devuelve (TokenType.ENDFILE, "$", línea, columna).
        """
        global programa, posicion, progLong, current_line, current_column

        # Procesar comentarios o espacios hasta encontrar un token válido
        while True:
            i = posicion
            token_line = current_line
            token_column = current_column

            # Saltar espacios en blanco iniciales (espacios, tabulaciones, saltos de línea)
            while i < progLong and programa[i] in (' ', '\t', '\n'):
                if programa[i] == '\n':
                    current_line += 1
                    current_column = 1
                else:
                    current_column += 1
                i += 1
            posicion = i

            # Actualizar posición de inicio del token después de los espacios
            token_line = current_line
            token_column = current_column

            # Manejar marcador de fin después de espacios.
            if i < progLong and programa[i] == '$':
                posicion = i
                if return_eof:
                    return TokenType.ENDFILE, "$", token_line, token_column
                else:
                    return None, None, token_line, token_column

            # Verificar inicio de comentario /*
            if i + 1 < progLong and programa[i] == '/' and programa[i+1] == '*':
                # Se encontró el inicio de un comentario
                # Saltar hasta encontrar */
                i += 2  # Saltar /*
                current_column += 2
                comment_closed = False

                while i + 1 < progLong and not comment_closed:
                    if programa[i] == '*' and programa[i+1] == '/':
                        comment_closed = True
                        i += 2  # Saltar */
                        current_column += 2
                    else:
                        if programa[i] == '\n':
                            current_line += 1
                            current_column = 1
                        else:
                            current_column += 1
                        i += 1

                if not comment_closed and i < progLong:
                    # Se alcanzó el final sin cerrar el comentario
                    if programa[i] == '\n':
                        current_line += 1
                        current_column = 1
                    else:
                        current_column += 1
                    i += 1  # Saltar último carácter

                posicion = i
                # Continuar el bucle externo para encontrar el siguiente token
                continue

            # Si llegamos aquí, no estamos en comentario o espacio, procesar el token
            break

        current_state = self.initial_state
        lexema = ""
        last_final_state = None
        last_final_lexema = ""
        last_final_index = -1

        # Guardar la posición de inicio del token actual
        token_start_line = current_line
        token_start_column = current_column

        # Procesar caracteres usando máxima absorción (maximal munch)
        while i < progLong:
            char = programa[i]
            # Detener si se encuentra el marcador de fin
            if char == '$':
                break

            column = self.get_char_column(char)
            new_state = self.state_table[current_state][column]

            # Si la transición es inválida (estado de error), salir del bucle
            if new_state == 8:
                break

            current_state = new_state
            lexema += char

            # Actualizar posición actual
            if char == '\n':
                current_line += 1
                current_column = 1
            else:
                current_column += 1

            # Si el estado actual es final, registrarlo
            if current_state in self.final_states:
                last_final_state = current_state
                last_final_lexema = lexema
                last_final_index = i
            i += 1

        # Si se registró un estado final, tenemos un token válido
        if last_final_state is not None:
            # Si el estado final requiere retroceso, no consumir el carácter extra
            if last_final_state in self.rewind_states:
                last_final_lexema = last_final_lexema[:-1]
                posicion = last_final_index

                # Si retrocedemos, también hay que ajustar la posición actual
                if programa[last_final_index] == '\n':
                    # Esto es un caso especial que requeriría rastrear la columna anterior
                    # Por simplicidad, ajustamos solo si el carácter no es un salto de línea
                    current_column = 1  # Esto es una aproximación
                else:
                    current_column -= 1
            else:
                posicion = last_final_index + 1
            token_type = self.final_states[last_final_state]

            # Si el token es un identificador, verificar si es una palabra reservada
            if token_type == TokenType.ID:
                token_type = self.check_reserved_word(
                    last_final_lexema.strip(), token_type)
            return token_type, last_final_lexema.strip(), token_start_line, token_start_column
        else:
            # No se formó un token válido
            if i < progLong:
                # Recoger caracteres hasta espacio o delimitador
                error_start = i

                # Continuar hasta encontrar espacio o delimitador
                while i < progLong and programa[i] not in (' ', '\t', '\n', '$'):
                    lexema += programa[i]
                    if programa[i] == '\n':
                        current_line += 1
                        current_column = 1
                    else:
                        current_column += 1
                    i += 1

                posicion = i
                print("Error: Token invalido en la posición ",
                      error_start, "=>", lexema.strip())
                return TokenType.ERROR, lexema.strip(), token_start_line, token_start_column
            else:
                posicion = i
                if return_eof:
                    return TokenType.ENDFILE, "$", token_start_line, token_start_column
                else:
                    return None, None, token_start_line, token_start_column


def getToken(imprimir=True):
    lexer = Lexer()
    token, tokenString, line, column = lexer.get_token(True)
    if imprimir:
        print(token, " = ", tokenString, " at line:", line, " column:", column)
    return token, tokenString, line, column


def def_globales(prog, pos, long_):
    global programa, posicion, progLong, current_line, current_column
    programa = prog
    posicion = pos
    progLong = long_
    current_line = 1
    current_column = 1
    # Crear la instancia singleton (si no existe aún)
