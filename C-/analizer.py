from globalTypes import TokenType, TreeNode, VarType, operation_operators, comparison_operators
from enum import Enum

MAXCHILDREN = 3  # adjust as needed
scope_stack = []  # Stack of symbol tables (dicts)
location_counter = 0  # Memory address counter for variables
current_function = None  # Track current function name
scope_info = {}  # Store scope information in a hashtable
ERROR = False  # Global error flag
error_message = []  # Error message for debugging


def scope_push():
    """Funcion para agregar un nuevo scope a la pila de scopes

    Returns:
        None
    """
    scope_stack.append({})


def create_error(name, lineno, message):
    """Funcion para crear un error semantico

    Args:
        name (str): Nombre de la variable que causo el error
        lineno (int): Linea donde ocurrio el error
        message (str): Mensaje descriptivo del error

    Returns:
        VarType: Tipo de error
    """
    global ERROR, error_message
    ERROR = True
    error_message.append(
        f"Error: Variable '{name}' {message} en la línea {lineno}")

    return VarType('error', None)


def scope_pop():
    """Funcion para remover el scope actual de la pila de scopes

    Returns:
        None
    """
    scope_stack.pop()


def current_scope():
    """Funcion para obtener el scope actual

    Returns:
        dict: Scope actual (ultimo en la pila)
    """
    return scope_stack[-1]


def st_insert(name, lineno, loc, var_type=None):
    """Funcion para insertar una variable en la tabla de simbolos del scope actual

    Args:
        name (str): Nombre de la variable
        lineno (int): Linea donde se declara la variable
        loc (int): Ubicacion en memoria
        var_type (VarType, optional): Tipo de la variable. Defaults to None.

    Returns:
        None
    """
    table = current_scope()

    if name not in table:
        table[name] = {"lines": [lineno], "type": var_type}

    else:
        table[name]["lines"].append(lineno)
        if var_type:
            table[name]["type"] = var_type


def st_add(name, lineno, loc):
    """Funcion para agregar una referencia a una variable existente

    Args:
        name (str): Nombre de la variable
        lineno (int): Linea donde se usa la variable
        loc (int): Ubicacion en memoria

    Returns:
        None
    """
    table = current_scope()

    if name in table:
        table[name]["lines"].append(lineno)

    elif name in scope_stack[0]:
        global_val = scope_stack[0][name]
        table[name] = {"lines": [lineno],
                       "type": VarType(global_val['type'].type, global_val['type'].size)}
    else:
        table[name] = {"lines": [lineno],
                       "type": create_error(name, lineno, "no definida")}


def st_lookup(name, index=None):
    """Funcion para buscar una variable en la tabla de simbolos

    Args:
        name (str): Nombre de la variable a buscar
        index (int, optional): Indice del scope donde buscar. Defaults to None.

    Returns:
        dict: Informacion de la variable si se encuentra, None en caso contrario
    """
    if index is None:
        for scope in reversed(scope_stack):
            if name in scope:
                return scope[name]
        return None
    else:
        if name in scope_stack[index]:
            return scope_stack[index][name]
        return None


def is_function_node(t):
    """Funcion para determinar si un nodo representa una funcion

    Args:
        t (TreeNode): Nodo a evaluar

    Returns:
        bool: True si el nodo representa una funcion, False en caso contrario
    """
    return (
        t.token == TokenType.ID and
        t.child and
        len(t.child) > 1 and
        t.child[1].token == TokenType.FUNCTION
    )


def checking_function_params(node):
    """Funcion para obtener los parametros de una funcion

    Args:
        node (TreeNode): Nodo que representa la funcion

    Returns:
        list: Lista de tipos de parametros
    """
    if node is None:
        return True
    params_arr = []
    children = node.child[0]

    if children.token == TokenType.PARAMS:
        for child in children.child:
            if len(child.child) == 1:
                pass
            elif child.child[1].child:
                params_arr.append("arr")
            else:
                params_arr.append(child.child[0].lexema)

    return params_arr


def get_node_type(node):
    """Funcion para obtener el tipo de un nodo

    Args:
        node (TreeNode): Nodo a evaluar

    Returns:
        VarType: Tipo del nodo
    """
    if not node or not node.child:
        return None

    # Check for function type
    if is_function_node(node):
        params = checking_function_params(node.child[1])
        child = node.child[0]
        if child.token == TokenType.VOID:
            return VarType("void", None, params)
        elif child.token == TokenType.INT:
            return VarType("int", None, params)

    # Check for variable type
    child = node.child[0] if node.child else None
    nex_child = node.child[1] if child and len(node.child) > 1 else None

    if nex_child and nex_child.token == TokenType.VARIABLE and nex_child.child:
        size = None
        if nex_child.child[0].token == TokenType.ENTERO:
            size = int(nex_child.child[0].lexema)
        elif nex_child.child[0].token == TokenType.ID:
            if st_lookup(nex_child.child[0].lexema):
                size = nex_child.child[0].lexema

        return VarType("arr", size)
    if child.token == TokenType.INT:
        return VarType("int", None)
    elif child.token == TokenType.VOID:
        return VarType("void", None)

    resp = st_lookup(node.lexema, index=0)
    if resp:
        return VarType(resp['type'].type, resp['type'].size)

    # Default to error type if none found
    return create_error(node.lexema, node.line, "unknown error")


def traverse(t, preProc, postProc):
    """Funcion para recorrer el arbol de sintaxis

    Args:
        t (TreeNode): Nodo actual
        preProc (function): Funcion a crear tablas antes de procesar los hijos
        postProc (function): Funcion a checar tipos despues de procesar los hijos

    Returns:
        None
    """
    global current_function, scope_info, error_message

    if t is None:
        return

    # Process the node first
    preProc(t)

    # If this is a function node, create a new scope for its body
    if is_function_node(t):
        current_function = t.lexema
        scope_push()

    # Process children
    for child in t.child:
        traverse(child, preProc, postProc)

    # If this was a function node, store its scope info and pop
    if is_function_node(t):
        # Store the current scope info after processing all variables
        scope_info[current_function] = {
            "scope": scope_stack[-1].copy(),
            "type": get_node_type(t)
        }
        scope_pop()

        resp = False

        if len(error_message) == 0:
            resp = postProc(t, current_function)
            if not resp:
                printing_errors(current_function, "Error de tipado")

            else:
                print(
                    f"Revisión de tipos '{current_function}' procesado de forma exitosa.")
        else:
            printing_errors(current_function, "Error semantico")

        current_function = None


def printing_errors(current_function, error_type):
    """Funcion para imprimir los errores encontrados

    Args:
        current_function (str): Nombre de la funcion donde ocurrio el error
        error_type (str): Tipo de error

    Returns:
        None
    """
    global error_message
    if error_message:
        print(f"\n{error_type} en la función '{current_function}':")
        print(20*"-")
        print(error_message[0])
        print(20*"-")

        error_message = []


def insertNode(t):
    """Funcion para insertar un nodo en la tabla de simbolos

    Args:
        t (TreeNode): Nodo a insertar

    Returns:
        None
    """
    global location_counter

    if t.token == TokenType.ID:
        left_children_token = t.child[0].token if t.child else None

        # Variable declaration
        if (left_children_token == TokenType.INT and any(c.token == TokenType.VARIABLE for c in t.child)) or is_function_node(t):
            st_lookup(t.lexema)
            st_insert(t.lexema, t.line, location_counter, get_node_type(t))
            location_counter += 1

        # Function parameter
        elif left_children_token == TokenType.PARAMS:
            st_lookup(t.lexema, index=0)
            st_insert(t.lexema, t.line, location_counter, get_node_type(t))
            location_counter += 1

        else:
            st_add(t.lexema, t.line, 0)


def print_symbol_tables():
    """Funcion para imprimir las tablas de simbolos

    Returns:
        None
    """
    # Helper to draw any table

    def draw_table(title, headers, rows):
        # Calculate max-width for each column
        col_widths = [
            max(len(headers[i]), *(len(row[i]) for row in rows))
            for i in range(len(headers))
        ]
        # Box‐drawing pieces
        h_lines = ["─" * (w + 2) for w in col_widths]
        top = "┌" + "┬".join(h_lines) + "┐"
        sep = "├" + "┼".join(h_lines) + "┤"
        bottom = "└" + "┴".join(h_lines) + "┘"

        # Bold on ANSI (most terminals) for header
        BOLD = "\033[1m"
        RESET = "\033[0m"

        # Title centered over full width
        print(f"\n{title}\n")

        print(top)
        # Header row
        hdr = "│" + "│".join(
            f" {headers[i].center(col_widths[i])} "
            for i in range(len(headers))
        ) + "│"
        print(f"{BOLD}{hdr}{RESET}")
        print(sep)
        # Data rows
        for row in rows:
            print("│" + "│".join(
                f" {row[i].ljust(col_widths[i])} "
                for i in range(len(row))
            ) + "│")
        print(bottom)

    # --- GLOBAL SCOPE ---
    # Build rows: [name, type, params, lines]
    global_rows = []
    for name, data in scope_stack[0].items():
        # lines
        lines_str = ', '.join(map(str, data['lines']))
        # type
        vt = data.get('type')
        if vt:
            type_str = f"{vt.type}[{vt.size}]" if vt.size else vt.type
            params_str = ", ".join(vt.params) if getattr(
                vt, 'params', None) else ""
        else:
            type_str, params_str = "None", ""
        global_rows.append([name, type_str, params_str, lines_str])

    draw_table(
        title="Scope nivel 0 (global)",
        headers=["Nombre", "Tipo", "Parametros", "Líneas"],
        rows=global_rows
    )

    # --- FUNCTION SCOPES ---
    for func_name, info in scope_info.items():
        func_rows = []
        for name, data in info['scope'].items():
            lines_str = ', '.join(map(str, data['lines']))
            vt = data.get('type')
            if vt:
                type_str = f"{vt.type}[{vt.size}]" if vt.size else vt.type
            else:
                type_str = "None"
            func_rows.append([name, type_str, lines_str])

        draw_table(
            title=f"Scope de función '{func_name}' (tipo: {info['type'].type})",
            headers=["Nombre", "Tipo", "Líneas"],
            rows=func_rows
        )


def checking_types(node, scope):
    """Funcion para verificar los tipos en el arbol de sintaxis

    Args:
        node (TreeNode): Nodo a verificar
        scope (str): Nombre del scope actual

    Returns:
        VarType: Tipo del nodo si es valido, False en caso contrario
    """
    if node is None:
        return True

    if node.token in operation_operators:
        left_child = checking_types(node.child[0], scope)
        right_child = checking_types(node.child[1], scope)

        if not left_child or not right_child:
            create_error(
                node.lexema, node.line, "expresión inválida")
            return False

        if left_child.type != right_child.type:
            create_error(
                node.lexema, node.line, "los tipos no coinciden")
            return False

        return left_child

    elif node.token in comparison_operators:
        left_child = checking_types(node.child[0], scope)
        right_child = checking_types(node.child[1], scope)

        if not left_child or not right_child:
            create_error(
                node.lexema, node.line, "expresión inválida")
            return False

        if left_child.type != right_child.type:
            create_error(
                node.lexema, node.line, "los tipos no coinciden")
            return False

        return left_child

    elif node.token == TokenType.RETURN:
        # Get current function's return type
        current_type = scope_info[scope]['type']
        if current_type.type == "void":
            if node.child:
                create_error(node.lexema, node.line,
                             "función void no puede retornar un valor")
                return False
            return True

        elif node.child:
            if node.child[0].token in [TokenType.ID, TokenType.ENTERO]:
                child_type = checking_types(node.child[0], scope)
                if child_type.type != current_type.type:
                    create_error(
                        node.lexema, node.line, "tipo de retorno inválido")
                    return False
                return child_type

        else:
            create_error(node.lexema, node.line,
                         "falta valor de retorno")
            return False

    elif node.child:
        if node.child[0].token == TokenType.POSITION:
            var_type = scope_info[scope]['scope'].get(node.lexema, None)

            if var_type is None:
                var_type = scope_stack[0].get(node.lexema, None)
                if var_type is None:
                    create_error(node.lexema, node.line, "no está definida")
                    return False

            if node.child[0].child[0].token == TokenType.ID:
                child_type = checking_types(
                    node.child[0].child[0], scope)

                if child_type.type != 'int':
                    create_error(node.lexema, node.line,
                                 "tipo de índice inválido")
                    return False

            if var_type['type'].size:
                if isinstance(var_type['type'].size, int) and node.child[0].child[0].token == TokenType.ENTERO:
                    if int(node.child[0].child[0].lexema) < int(var_type['type'].size) - 1:
                        return VarType('int', None)
                    else:
                        create_error(node.lexema, node.line,
                                     "índice fuera de rango")
                        return False

            return VarType('int', None)

        if node.child[0].token == TokenType.PARAMS and node.token != TokenType.FUNCTION:

            if node.child[0].child:
                var_type = scope_stack[0].get(node.lexema, None)

                if len(node.child[0].child) != len(var_type['type'].params):
                    create_error(
                        node.lexema, node.line, "número inválido de parámetros")
                    return False

                for i, child in enumerate(node.child[0].child):
                    type_resp = checking_types(child, scope)

                    if type_resp and var_type['type'].params[i] == type_resp.type:
                        pass
                    else:
                        create_error(
                            node.lexema, node.line, "tipo de parámetro inválido")
                        return False

                return var_type['type']
            else:
                var_type = scope_stack[0].get(node.lexema, None)
                if var_type['type'].params:
                    create_error(
                        node.lexema, node.line, "número inválido de parámetros")
                    return False
                else:
                    return VarType(var_type['type'].type, None)

        for child in node.child:
            type_resp = checking_types(child, scope)
            if not type_resp:
                create_error(
                    node.lexema, node.line, "expresión inválida")
                return False

    elif node.token == TokenType.ID:
        var_type = scope_info[scope]['scope'].get(node.lexema, None)
        if var_type is None:
            var_type = scope_stack[0].get(node.lexema, None)
            if var_type is None:
                create_error(node.lexema, node.line, "no está definida")
                return False

        t = var_type.get('type', VarType('error', None))

        return t

    elif node.token == TokenType.ENTERO:
        return VarType('int', None)

    return True


def semantica(ast, imprime):
    """Funcion principal para el analisis semantico

    Args:
        ast (TreeNode): Arbol de sintaxis a analizar
        imprime (bool): Flag para indicar si se deben imprimir las tablas de simbolos

    Returns:
        None
    """
    global ERROR
    print("Iniciando análisis semántico...")

    def_input = VarType("int", None, [])
    def_output = VarType("void", None, ["int"])

    scope_push()
    st_insert("input", -1, -1, def_input)
    st_insert("output", -1, -1, def_output)
    traverse(ast, insertNode, checking_types)

    # Check if main is the last function and has correct return type
    main_info = scope_stack[0].get("main", None)
    if not main_info or main_info['type'].type != "int":
        print("\nError: el programa debe terminar con una función int main()")
        ERROR = True

    if imprime:
        print_symbol_tables()

    scope_pop()

    return ERROR
