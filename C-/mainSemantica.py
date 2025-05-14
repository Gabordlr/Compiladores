from globalTypes import TokenType, TreeNode, VarType, operation_operators, comparison_operators
from enum import Enum

MAXCHILDREN = 3  # adjust as needed
scope_stack = []  # Stack of symbol tables (dicts)
location_counter = 0  # Memory address counter for variables
current_function = None  # Track current function name
scope_info = {}  # Store scope information in a hashtable


def scope_push():
    scope_stack.append({})


def scope_pop():
    scope_stack.pop()


def current_scope():
    return scope_stack[-1]


def st_insert(name, lineno, loc, var_type=None):
    table = current_scope()

    if name not in table:
        table[name] = {"lines": [lineno], "location": loc, "type": var_type}

    else:
        table[name]["lines"].append(lineno)
        if var_type:
            table[name]["type"] = var_type


def st_add(name, lineno, loc):
    table = current_scope()

    if name in table:
        table[name]["lines"].append(lineno)

    elif name in scope_stack[0]:
        global_val = scope_stack[0][name]
        table[name] = {"lines": [lineno], "location": loc,
                       "type": VarType(global_val['type'].type, global_val['type'].size)}
    else:
        table[name] = {"lines": [lineno], "location": loc,
                       "type": VarType('error', None)}


def st_lookup(name, index=None):
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
    return (
        t.token == TokenType.ID and
        t.child and
        len(t.child) > 1 and
        t.child[1].token == TokenType.FUNCTION
    )


def checking_function_params(node):
    if node is None:
        return True
    params_arr = []
    print("____________________", node.token)
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

    # print(
    #     f"Child token: {child.token}, Next child token: {nex_child.token if nex_child else 'None'}, next child.child: {nex_child.child if nex_child else 'None'}")

    if nex_child and nex_child.token == TokenType.VARIABLE and nex_child.child:
        size = nex_child.child[0].lexema if nex_child.child[0].token != TokenType.BOPEN else None
        return VarType("arr", size)
    if child.token == TokenType.INT:
        return VarType("int", None)
    elif child.token == TokenType.VOID:
        return VarType("void", None)

    resp = st_lookup(node.lexema, index=0)
    if resp:
        return VarType(resp['type'].type, resp['type'].size)

    return VarType('error', None)  # Default to error type if none found


def annotate_parents(node, parent=None):
    if node is None:
        return
    node.parent = parent
    for child in node.child:
        annotate_parents(child, node)


def traverse(t, preProc, postProc):
    global current_function, scope_info

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

        resp = postProc(t, current_function)
        print(f"Tipo de nodo: {t.token}, Tipo de función: {resp}")
        if not resp:
            print(f"Error de tipo en la línea {t.line}: {resp}")

        current_function = None


def insertNode(t):
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

        # Use of variable
        else:
            st_add(t.lexema, t.line, 0)


def print_symbol_tables():
    print("\n Tabla de símbolos por scope:")

    # Print global scope first
    print(f"\n Scope nivel 0 (global):")
    print(f"{'Nombre':<10} {'Tipo':<8} {'Loc':<5} {'Params':<15} Líneas")
    print("-" * 50)
    for name, data in scope_stack[0].items():
        lines_str = ', '.join(map(str, data['lines']))
        var_type = data.get('type', 'N/A') if data.get('type') else 'None'
        type_str = f"{var_type.type}[{var_type.size}]" if var_type.size else var_type.type

        # Format parameters for display
        params_str = ''
        if isinstance(var_type, VarType) and hasattr(var_type, 'params') and var_type.params:
            params_str = ', '.join(var_type.params)

        print(
            f"{name:<10} {type_str:<8} {data['location']:<5} {params_str:<15} {lines_str}")

    # Print function scopes
    for func_name, info in scope_info.items():
        print(
            f"\n Scope de función '{func_name}' (tipo: {info['type'].type}):")
        print(f"{'Nombre':<10} {'Tipo':<8} {'Loc':<5} Líneas")
        print("-" * 50)
        for name, data in info['scope'].items():
            lines_str = ', '.join(map(str, data['lines']))
            var_type = data.get('type', 'N/A') if data.get('type') else 'None'
            type_str = f"{var_type.type}[{var_type.size}]" if var_type.size else var_type.type

            print(
                f"{name:<10} {type_str:<8} {data['location']:<5} {lines_str}")


def check3ing_types(node, scope):
    return True


def checking_types(node, scope):
    print(
        f"Checking types in node: {node.lexema} of token {node.token} in scope: {scope}")

    if node is None:
        return True

    if node.token in operation_operators:
        left_child = checking_types(node.child[0], scope)
        right_child = checking_types(node.child[1], scope)

        print(
            f"Comparando tipos: {left_child} y {right_child}")

        if not left_child or not right_child:
            return False

        if left_child.type != right_child.type:
            print(
                f"Error de tipo en la línea {node.line}: {left_child.type} no es compatible con {right_child.type}")
            return False

        return left_child

    elif node.token in comparison_operators:
        left_child = checking_types(node.child[0], scope)
        right_child = checking_types(node.child[1], scope)

        print(
            f"Comparando tipos: {left_child.type} y {right_child.type}")

        if not left_child or not right_child:
            return False

        if left_child.type != right_child.type:
            print(
                f"Error de tipo en la línea {node.line}: {left_child.type} no es compatible con {right_child.type}")
            return False

        return left_child

    elif node.child:
        if node.child[0].token == TokenType.POSITION:
            return VarType('int', None)

        if node.child[0].token == TokenType.PARAMS and node.token != TokenType.FUNCTION:
            print(
                f"Comparando tipos: {node.child[0].token} y {node.token}")
            if node.child[0].child:
                var_type = scope_stack[0].get(node.lexema, None)
                if len(node.child[0].child) != len(var_type['type'].params):
                    print(
                        f"Error de tipo en la línea {node.line}: {len(node.child[0].child)} no es compatible con {len(var_type['type'].params)}")
                    return False

                for i, child in enumerate(node.child[0].child):
                    print("CHILD: ", child)
                    type_resp = checking_types(child, scope)

                    print(
                        f"Compp arando tipos: {var_type['type'].params[i]} y {type_resp.type}")
                    if var_type['type'].params[i] == type_resp.type:
                        pass
                    else:
                        return False
                return type_resp.type
            else:
                print(
                    f"NO tipos: y {node.token}")
                print(scope_stack[0])
                var_type = scope_stack[0].get(node.lexema, None)
                print(
                    f"var_type: {var_type}, tipo: {var_type['type']}")
                if var_type['type'].params:
                    return False
                else:
                    return VarType(var_type['type'].type, None)

        for child in node.child:
            type_resp = checking_types(child, scope)
            print(
                f"Tipo de nodo hijo: {child.token}, Tipo de respuesta: {type_resp}")
            if not type_resp:
                return False

    elif node.token == TokenType.ID:
        print("======================================================")
        print(scope_info[scope])
        print(f"ID encontrado: {node.lexema}")
        print(
            f"Scope actual: {scope_info[scope]['scope'].get(node.lexema, None).get('type', None).type}")
        var_type = scope_info[scope]['scope'].get(node.lexema, None)
        if var_type is None:
            var_type = scope_stack[0].get(node.lexema, None)
            if var_type is None:
                return False

        print(f"Tipo de variable: {var_type}")

        return var_type.get('type', VarType('error', None))

    elif node.token == TokenType.ENTERO:
        print("++++++++++++++++++++++++++++++++++++++++++")
        return VarType('int', None)

    return True


def semantica(ast, imprime):
    global scope_info
    print("Iniciando análisis semántico...")

    annotate_parents(ast)
    scope_info = {}  # Reset scope info to empty hashtable

    def_input = VarType("int", None)
    def_output = VarType("void", None, ["int"])

    scope_push()
    st_insert("input", -1, -1, def_input)
    st_insert("output", -1, -1, def_output)
    traverse(ast, insertNode, checking_types)

    # Perform type checking
    # is_valid = checking_types(ast)
    # print(f"Tipo de nodo raíz: {is_valid.type}")
    # if not is_valid:
    #     print(f"Error de tipado")
    #     print(error)
    # else:
    #     print("Análisis semántico completado sin errores.")

    if imprime:
        print_symbol_tables()

    scope_pop()
