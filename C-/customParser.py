from lexer import Lexer, def_globales
from globalTypes import *


class Parser:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Parser, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Inicializar solo una vez para preservar el estado de singleton.
        if not hasattr(self, '_initialized'):
            self.prev_token = None
            self.prev_token_lexema = None
            self.token = None
            self.token_lexema = None
            self.line = None
            self.column = None
            self.root = None
            self.count = 0
            self.error = None

    def create_node(self, token, lexema, val=0, no_line=False):
        """
        Crea un nuevo nodo de árbol con el token y lexema dados.
        """

        if no_line:
            return TreeNode(token=token, lexema=lexema)

        return TreeNode(token=token, lexema=lexema, line=self.line + val, column=self.column)

    def create_error_node(self, token, lexema, error_msg):
        """Crea un nodo de error con el token y lexema dados.

        Returns:
            ErrorNode: Nodo del tipo ErrorNode
        """

        err = ErrorNode(lexema=lexema, column=self.column,
                        line=self.line, errorMessage=error_msg)

        if not self.error:
            self.error = err

        self.match([TokenType.ERROR], force=True)

        return err

    def match(self, token_arr, force=False):
        """ Funcion para hacer match con el token actual y el token esperado, y solicitar el siguiente token

        Args:
            token_arr (TokenType): Tipo del token esperado
            force (bool, optional): Flag para solcitar el siguiente token, pese a que no coincida. Defaults to False.

        Returns:
            bool: True si el token coincide, False en caso contrario
        """

        if self.token in token_arr or force:
            self.prev_token = self.token
            self.prev_token_lexema = self.token_lexema
            self.token, self.token_lexema, self.line, self.column = Lexer().get_token()
            return True

        if self.token == TokenType.ERROR:
            self.create_error_node(
                self.token, self.token_lexema, "Error de sintaxis")

        return False

    def parser(self):
        """Funcion para procesar el arbol de sintaxis

        Returns:
            TreeNode: 
        """
        self.token, self.token_lexema, self.line, self.column = Lexer().get_token()

        self.root = self.create_node(TokenType.PROGRAM, "program")

        while (self.token != TokenType.ENDFILE):
            n = self.program_tk()

            if type(n) == ErrorNode:
                self.root.child.append(n)

            else:
                for x in n:
                    self.root.child.append(x)

        return self.root, self.error

    def program_tk(self):
        """Funcion para procesar el programa

        Returns:
            Node: Devuelve un nodo que representa el programa
        """
        n = self.type_tk()

        n_child = None
        if self.token == TokenType.POPEN:
            n_child = self.fun_tk()

        elif self.token == TokenType.BOPEN or self.token == TokenType.SEMICOLON:
            n_child = self.var_decl_tk()

        if n_child == None:
            n_child = self.create_error_node(
                self.token, self.token_lexema, "Error de segmentación")

        if n:
            n.child.append(n_child)

            return [n]

        else:
            n_child = self.create_error_node(
                self.token, self.token_lexema, "Error de segmentación")

            return n_child

    def fun_tk(self):
        """Funcion para procesar una funcion

        Returns:
            Node: Devuelve un nodo que representa la funcion marcada por un nodo (function)
        """
        n = self.create_node(TokenType.FUNCTION, "function")
        n_open = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.POPEN]):
            n_child = self.params_tk()
            n_c = None

            self.match([TokenType.ID])

            if self.token == TokenType.PCLOSE:
                n_close = self.create_node(self.token, self.token_lexema)
                self.match([TokenType.PCLOSE])

                if self.token == TokenType.LLOPEN:
                    n_c = self.compound_tk()

            if not n_c:
                n_c = self.create_error_node(
                    self.token, self.token_lexema, "Error de segmentación")

            n.child = [n_child, n_c]
        return n

    def decimal_tk(self):
        """Funcion para procesar un entero

        Returns:
            Node: Devuelve un nodo que representa el entero
        """
        n = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.ENTERO]):
            return n

    def param_tk(self):
        """Funcion para procesar un parametro

        Returns:
            Node: Devuelve un nodo que representa el parametro
        """

        n_t = self.type_tk()
        n_id = self.var_decl_tk(inParams=True)

        if n_id and n_t:
            n_t.child.append(n_id)

        return n_t

    def params_tk(self):
        """Funcion para procesar un conjunto de  parametros de una funcion

        Returns:
            Node: Devuelve un nodo que representa el conjunto de parametros
        """
        n_child = []
        n = self.create_node(TokenType.PARAMS, "params")
        n_child.append(self.param_tk())

        while self.token == TokenType.COMA:
            if self.match([TokenType.COMA]):
                n_child.append(self.param_tk())

        n.child = n_child

        return n

    def type_tk(self):
        """Funcion para procesar el tipo de dato

        Returns:
            Node: Devuelve un nodo que representa el tipo de dato
        """
        n = self.create_node(self.token, self.token_lexema)
        if self.match([TokenType.INT, TokenType.VOID]):
            n_id = self.create_node(self.token, self.token_lexema)
            if self.token == TokenType.ID:
                self.match([TokenType.ID])
                n_id.child.append(n)

                return n_id

            return n

    def compound_tk(self):
        """Funcion para procesar un bloque de instrucciones

        Returns:
            Node: Devuelve un nodo que representa el bloque de instrucciones
        """
        n_open = self.create_node(self.token, self.token_lexema)
        if self.match([TokenType.LLOPEN]):

            n_child = self.compounds_tk()

            n_close = self.create_node(self.token, self.token_lexema)
            if self.match([TokenType.LLCLOSE]):

                return n_child

    def compounds_tk(self):
        """Funcion para procesar concatenacion de bloques de instrucciones

        Returns:
            Node: Devuelve un nodo que representa la concatenacion de bloques de instrucciones
        """
        n = self.create_node("compound", "compound")
        n_child = []
        n_val = self.stmt_decl_tk()
        n_child.append(n_val)

        while self.token != TokenType.LLCLOSE and n_val.token != TokenType.ERROR:
            n_val = self.stmt_decl_tk()
            n_child.append(n_val)

        n.child = n_child
        return n

    def stmt_decl_tk(self):
        """Funcion para procesar una declaracion de sentencia

        Returns:
            Node: Devuelve un nodo que representa la declaracion de sentencia
        """

        if self.token == TokenType.LLOPEN:
            n = self.compound_tk()

        elif self.token == TokenType.VOID or self.token == TokenType.INT:
            n = self.type_tk()
            n_child = self.var_decl_tk()

            n.child.append(n_child)

        elif self.token == TokenType.ID or self.token == TokenType.ENTERO:
            n = self.exp_tk()

        elif self.token == TokenType.IF:
            n = self.if_tk()

        elif self.token == TokenType.WHILE:
            n = self.while_tk()

        elif self.token == TokenType.RETURN:
            n = self.return_tk()

        else:
            n = self.create_error_node(
                self.token, self.token_lexema, "Error de segmentación")

        return n

    def return_tk(self):
        """Funcion para procesar una sentencia de return

        Returns:
            Node: Devuelve un nodo que representa la sentencia de return
        """
        n = self.create_node(self.token, self.token_lexema)
        if self.match([TokenType.RETURN]):
            if self.token == TokenType.SEMICOLON:
                self.match([TokenType.SEMICOLON])
                return n

            else:
                n_child = self.exp_tk()
                n.child.append(n_child)

                return n

    def while_tk(self):
        """Funcion para procesar una sentencia de while

        Returns:
            Node: Devuelve un nodo que representa la sentencia de while
        """
        n = self.create_node(self.token, self.token_lexema)
        if self.match([TokenType.WHILE]):
            if self.match([TokenType.POPEN]):
                n_exp = self.exp_tk()
                if self.match([TokenType.PCLOSE]):
                    n_head = self.create_node("stmt", "stmt")
                    n.child.append(n_exp)
                    n_head.child.append(self.stmt_decl_tk())
                    n.child.append(n_head)
                    return n

    def if_tk(self):
        """Funcion para procesar una sentencia de if

        Returns:
            Node: Devuelve un nodo que representa la sentencia de if
        """
        n = self.create_node(self.token, self.token_lexema)
        if self.match([TokenType.IF]):
            if self.match([TokenType.POPEN]):
                n_exp = self.exp_tk()
                if self.match([TokenType.PCLOSE]):
                    n_head = self.create_node("stmt", "stmt")
                    n.child.append(n_exp)
                    n_head.child.append(self.stmt_decl_tk())
                    n.child.append(n_head)

                    if self.token == TokenType.ELSE:
                        n_else = self.create_node(
                            self.token, self.token_lexema)
                        self.match([TokenType.ELSE])
                        n_else_c = self.stmt_decl_tk()
                        n_else.child.append(n_else_c)
                        n.child.append(n_else)

                    return n

    def exp_tk(self):
        """Funcion para procesar expresiones

        Returns:
            Node: la cabeza del arbol de expresion
        """
        n = self.create_node(self.token, self.token_lexema)

        if n:
            if n.token == TokenType.SEMICOLON:
                n = self.create_error_node(
                    self.token, self.token_lexema, "Error de segmentación")
                return n

            n_child = self.add_exp_tk()

            return n_child

    def sin_exp_tk(self):
        """Funcion para procesar una sumatoria (additive expresion)

        Returns:
            Node: Devuelve un nodo que representa lo que se le iguala a la variable
        """
        n_child = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.ASIGNAR]):

            n_resp = self.exp_tk()
            n_child.child.append(n_resp)

            return n_child

    def add_exp_tk(self):
        """Funcion para procesar una sumatoria (additive expresion)

        Returns:
            Node: Devuelve un nodo que representa lo que se le iguala a la variable
        """
        n = self.opp_varint_tk()

        if n:
            n_child = self.create_node(self.token, self.token_lexema)

            if self.token == TokenType.SEMICOLON:
                self.match([TokenType.SEMICOLON])
                return n

            elif self.token == TokenType.SUMA or self.token == TokenType.RESTA:
                n_arr = self.add_exp_tk2()

                n_arr.child[0] = n

                return n_arr

            elif self.token == TokenType.MULT or self.token == TokenType.DIV:
                n_arr = self.add_exp_tk2()

                n_arr.child[0] = n

                return n_arr

            elif self.token in comparison_operators:
                n_arr = self.add_exp_tk2()

                n_arr.child[0] = n

                return n_arr

            elif self.token == TokenType.ASIGNAR:
                new_n = self.sin_exp_tk()

                new_n.child.insert(0, n)

                return new_n

            return n

    def add_exp_tk2(self):
        """Función recursiva para procesar conatneacion de expresiones

        Returns:
            Node: Cabeza del arbol de las expresiones
        """
        n_prev = self.create_node(self.prev_token, self.prev_token_lexema)
        n_op = self.create_node(self.token, self.token_lexema)

        if self.token == TokenType.SUMA or self.token == TokenType.RESTA:
            self.match([TokenType.SUMA, TokenType.RESTA])
            n_op.child.append(n_prev)
            n_op.child.append(self.add_exp_tk())

            return n_op

        elif self.token == TokenType.MULT or self.token == TokenType.DIV:
            self.match([TokenType.MULT, TokenType.DIV])
            n_op.child.append(n_prev)
            n_op.child.append(self.term_exp_tk())

            return n_op

        elif self.token in comparison_operators:
            self.match(comparison_operators)
            n_op.child.append(n_prev)
            n_op.child.append(self.add_exp_tk())

            return n_op

        elif self.match([TokenType.ID, TokenType.ENTERO]):
            n_op2 = self.create_node(self.token, self.token_lexema)
            if self.token == TokenType.SUMA or self.token == TokenType.RESTA:
                self.match([TokenType.SUMA, TokenType.RESTA])
                n_op2.child.append(n_op)
                n_op2.child.append(self.add_exp_tk())

                return n_op2

            elif self.token == TokenType.MULT or self.token == TokenType.DIV:
                self.match([TokenType.MULT, TokenType.DIV])
                n_op2.child.append(n_op)
                n_op2.child.append(self.factor_tk())

                return n_op2

            elif self.match([TokenType.SEMICOLON]):
                return n_op

    def term_exp_tk(self):
        """Funcion para procesar una multiplicacion (multiplicative expresion)

        Returns:
            Node: Devuelve un nodo que representa la multiplicacion
        """
        n_op = self.create_node(self.prev_token, self.prev_token_lexema)
        n = self.opp_varint_tk()

        if self.token == TokenType.MULT or self.token == TokenType.DIV:
            n_op2 = self.create_node(self.token, self.token_lexema)
            self.match([TokenType.MULT, TokenType.DIV])
            n_op2.child.append(n)
            n_op2.child.append(self.factor_tk())

            return n_op2

        if self.token == TokenType.SEMICOLON:
            self.match([TokenType.SEMICOLON])
            return None

        return n

        # while self.token == TokenType.MULT or self.token == TokenType.DIV:
        #     n_head = self.create_node(self.token, self.token_lexema)
        #     self.match([TokenType.MULT, TokenType.DIV])
        #     n_child = self.factor_tk()

        #     n_head.child = [n, n_child]

    def factor_tk(self):
        """Funcion para procesar un factor

        Returns:
            Node: Devuelve un nodo que representa el factor al que se le aplica la multiplicacion
        """
        n = self.create_node(self.token, self.token_lexema)

        if self.token == TokenType.POPEN:
            n = self.create_node("paren", "paren")
            n_open = self.create_node(self.token, self.token_lexema)
            self.match([TokenType.POPEN])
            n_child = self.exp_tk()

            if self.token == TokenType.PCLOSE:
                n_close = self.create_node(self.token, self.token_lexema)
                self.match([TokenType.PCLOSE])
                n.child = [n_child]

                n_new = self.term_exp_tk()

                n.child.append(n_new)

                return n

        elif self.token == TokenType.ID:
            n_child = self.var_call_tk()

            n_new = self.term_exp_tk()

            n_child.child.append(n_new)
            n_child.child.insert(0, n)

            return n_child

        elif self.token == TokenType.ENTERO:
            n_child = self.decimal_tk()
            n_new = self.term_exp_tk()

            n_child.child.append(n_new)
            n_child.child.insert(0, n)

            return n_child

        return n

    def opp_varint_tk(self):
        """Funcion para procesar una variable, un llamado a una funcion o un entero

        Returns:
            Node: Devuelve un nodo que representa la variable, el llamado a funcion o el entero
        """
        n_id = self.create_node(self.token, self.token_lexema)

        if self.token == TokenType.ID:
            n_id = self.var_call_tk()

        elif self.token == TokenType.ENTERO:
            n_id = self.decimal_tk()

        return n_id

    def var_tk(self):
        """Funcion para procesar una variable con o sin []  

        Returns:
            Node: Variable con posicion en caso de ser una posicion
        """
        n_t = self.create_node(TokenType.POSITION, "posición")
        n = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.ID]):
            if self.token == TokenType.BOPEN:
                n_open = self.create_node(self.token, self.token_lexema)
                self.match([TokenType.BOPEN])

                n_child = self.exp_tk()

                n_close = self.create_node(self.token, self.token_lexema)
                if self.match([TokenType.BCLOSE]):
                    n_t.child = [n_child]

                n.child.append(n_t)

            return n_t

    def var_call_tk(self):
        """Funcion para procesar una llamada a funcion

        Returns:
            Node: Devuelve un nodo que representa la llamada a funcion, con sus parametros
        """
        n = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.ID]):
            if self.token == TokenType.BOPEN:
                n_t = self.create_node(TokenType.POSITION, "posición")
                n_open = self.create_node(self.token, self.token_lexema)
                self.match([TokenType.BOPEN])
                n_child = self.exp_tk()

                n_close = self.create_node(self.token, self.token_lexema)
                if self.match([TokenType.BCLOSE]):
                    n_t.child = [n_child]

                n.child.append(n_t)

            elif self.token == TokenType.POPEN:
                n_t = self.create_node(TokenType.PARAMS, "params")
                n_t.child = self.def_calls_tk()
                n.child.append(n_t)

            return n

    def var_decl_tk(self, inParams=False):
        """Funcion para procesar una declaracion de variable

        Returns:
            Node: Devuelve un nodo que representa la declaracion de variable
        """
        n = self.create_node(TokenType.VARIABLE, "variable")
        n_open = self.create_node(self.token, self.token_lexema)
        n_child = None

        if self.match([TokenType.BOPEN]):
            if not inParams:
                n_child = self.exp_tk()

            if self.token == TokenType.BCLOSE:
                n_close = self.create_node(self.token, self.token_lexema)
                self.match([TokenType.BCLOSE])

                if n_child:
                    n.child = [n_child]
                else:
                    n.child = [n_open, n_close]

        n_semi = self.create_node(self.token, self.token_lexema)

        if not inParams:
            if self.match([TokenType.SEMICOLON]):
                return n

        else:
            return n

    def def_calls_tk(self):
        """Funcion para procesar una llamada a funcion

        Returns:
            Node: Devuelve un nodo que representa la llamada a funcion, con sus parametros
        """
        n_open = self.create_node(self.token, self.token_lexema)

        if self.match([TokenType.POPEN]):
            if not self.token == TokenType.PCLOSE:
                n_child = self.def_call_tk()
            else:
                n_child = []

            n_close = self.create_node(self.token, self.token_lexema)
            if self.match([TokenType.PCLOSE]):

                return n_child

    def def_call_tk(self):
        """Funcion para procesar paraetros con los que se llama a una funcion

        Returns:
            Node: Devuelve un nodo que representa la llamada a funcion, con sus parametros
        """
        n_child = []

        n = self.exp_tk()
        if n:
            n_child.append(n)

        while self.token == TokenType.COMA:
            if self.match([TokenType.COMA]):
                n_child.append(self.exp_tk())

        return n_child


def parser(imprimir):
    parser = Parser()
    acl, error = parser.parser()

    if imprimir:
        print(" ")
        print(" ")
        print(" ")
        print("-------------------------------------------------------------")

        if error:
            print(
                f"Error: {error.errorMessage} en la posicion {error.line}:{error.column}, lexema inesperado '{error.lexema}'")

        else:
            print("No se encontraron errores en el procesamiento del arbol")

        print("-------------------------------------------------------------")
        print(" ")
        print_tree(acl)

    return acl, error


def globales(prog, pos, long_):
    def_globales(prog, pos, long_)
    # Crear la instancia singleton (si no existe aún)
    Lexer()
    Parser()


def print_tree(node, level=0, prefix="", is_last=True, visited=None):
    """Funcion para mostrar el abrol de forma visual 
    (para el dibujo del arbol con lineas continuas se apoyo en herramientas de AI)

    Args:
        node (TreeNode): Nodo del arbol que representa el token
        level (int, optional): Representa el nivel de profunididad del arbol. Valor default en 0.
        prefix (str, optional): Representa un acumulador para dibujar las lineas. Valor default en "".
        is_last (bool, optional): Representa si es el ultimo nodo de la rama. Valor default en True.
        visited (_type_, optional): Representa un conjunto de nodos visitados para buscar y evitar imprimir infinitamente en caso de ciclos. Valor default en None.
    """
    if visited is None:
        visited = set()

    if node is None:
        return

    # Check for cycles
    node_id = id(node)
    if node_id in visited:
        print(prefix + ("└── " if is_last else "├── ") + "CYCLE DETECTED")
        return

    # Add current node to visited set
    visited.add(node_id)

    # Determine the branch symbol
    branch = "└── " if is_last else "├── "

    # Handle the node information safely
    try:
        if hasattr(node, 'token') and node.token is not None:
            token_repr = " (" + str(node.line) + ":" + \
                str(node.column) + ")" + str(node.token)
            node_info = token_repr
        else:
            node_info = "ROOT"

        # Add lexema if available
        if hasattr(node, 'lexema') and node.lexema:
            node_info += f" {node.lexema}"
    except Exception:
        node_info = f"Error: Se encontro el token inesperado {node.token} en la posicion {node.line}:{node.column}"

    print(prefix + branch + node_info)

    # Prepare prefix for children
    child_prefix = prefix + ("    " if is_last else "│   ")

    # Print all children
    if hasattr(node, 'child'):
        try:
            children = node.child
            for i, child in enumerate(children):
                is_last_child = i == len(children) - 1
                print_tree(child, level + 1, child_prefix,
                           is_last_child, visited.copy())
        except Exception as e:
            print(child_prefix + f"Error accessing children: {str(e)}")
