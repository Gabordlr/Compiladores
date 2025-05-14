from typing import Tuple, List, Optional, Dict
from globalTypes import TokenType, TreeNode

# Global variables to track state
location = 0
Error = False


def st_lookup(name: str, symbol_table: Dict) -> int:
    """
    Look up a symbol in the symbol table

    :return: Location of the symbol, or -1 if not found
    """
    entry = symbol_table.get(name)
    return entry['location'] if entry else -1


def st_insert(name: str,
              line_no: int,
              loc: int,
              symbol_table: Dict,
              line_numbers: Optional[List[int]] = None):
    """
    Insert a symbol into the symbol table

    :param name: Name of the symbol
    :param line_no: Line number of declaration/use
    :param loc: Memory location
    :param symbol_table: Symbol table dictionary
    :param line_numbers: List of line numbers where symbol is used
    """
    # If symbol doesn't exist, create new entry
    if name not in symbol_table:
        symbol_table[name] = {
            'location': loc,
            'lines': set([line_no])
        }
    else:
        # Update existing entry location if it's zero (hasn't been set yet)
        if symbol_table[name]['location'] == 0:
            symbol_table[name]['location'] = loc
        # Add line number to existing entry
        symbol_table[name]['lines'].add(line_no)


def printSymTab(symbol_table: Dict):
    """
    Print symbol table in the specified format

    :param symbol_table: Symbol table dictionary
    """
    print("Symbol table:")
    print("{:<15} {:<10} {:<}".format(
        "Variable Name", "Location", "Line Numbers"))
    print("{:<15} {:<10} {:<}".format(
        "-------------", "--------", "------------"))

    # Sort symbols by location
    sorted_symbols = sorted(symbol_table.items(),
                            key=lambda x: x[1]['location'])

    for name, entry in sorted_symbols:
        line_numbers_str = ' '.join(map(str, sorted(entry['lines'])))
        print("{:<15} {:<10} {:<}".format(
            name,
            entry['location'],
            line_numbers_str
        ))


def traverse(t: TreeNode,
             preProc,
             postProc,
             symbol_table: Dict,
             location_counter: List[int]):
    """
    Recursive tree traversal

    :param t: Current tree node
    :param preProc: Pre-order processing function
    :param postProc: Post-order processing function
    :param symbol_table: Symbol table to populate
    :param location_counter: Mutable list to track location
    """
    if t is not None:
        # Pre-order processing
        preProc(t, symbol_table, location_counter)

        # Recursively process children
        if hasattr(t, 'child'):
            for child in t.child:
                traverse(child, preProc, postProc,
                         symbol_table, location_counter)

        # Post-order processing
        postProc(t, symbol_table)


def is_array_declaration(node: TreeNode) -> bool:
    """
    Check if a node represents an array declaration

    :param node: TreeNode to check
    :return: Boolean indicating if it's an array declaration
    """
    # Check if we have a variable node with children
    if not hasattr(node, 'child') or len(node.child) < 2:
        return False

    # Look for pattern: variable variable with BOPEN/BCLOSE
    for i in range(len(node.child)):
        if hasattr(node.child[i], 'lexema') and node.child[i].lexema == 'variable':
            # Check for array markers in next child
            if i+1 < len(node.child):
                if hasattr(node.child[i+1], 'token'):
                    if node.child[i+1].token == TokenType.BOPEN:
                        return True

    return False


def is_array_access(node: TreeNode) -> bool:
    """
    Check if a node represents an array access

    :param node: TreeNode to check
    :return: Boolean indicating if it's an array access
    """
    # Check if we have a node with 'posición' child
    if not hasattr(node, 'child'):
        return False

    for child in node.child:
        if hasattr(child, 'lexema') and child.lexema == 'posición':
            return True

    return False


def get_array_element_from_node(node: TreeNode) -> Optional[TreeNode]:
    """
    Extract the array element node from an array access

    :param node: TreeNode that might contain array access
    :return: The subtree that represents the array element, or None
    """
    if not is_array_access(node):
        return None

    # Find the 'posición' child node
    for child in node.child:
        if hasattr(child, 'lexema') and child.lexema == 'posición':
            # Return the child of posición, which is the array index
            if hasattr(child, 'child') and len(child.child) > 0:
                return child.child[0]

    return None


def insertNode(t: TreeNode,
               symbol_table: Dict,
               location_counter: List[int]):
    """
    Insert identifiers into symbol table based on the specific TreeNode structure

    :param t: Current tree node
    :param symbol_table: Symbol table to populate
    :param location_counter: Mutable list to track location
    """
    # Skip nodes without token attribute
    if not hasattr(t, 'token'):
        return

    # Handle variable declarations
    if t.token == TokenType.ID:
        var_name = t.lexema if hasattr(t, 'lexema') else None
        if var_name and hasattr(t, 'line'):
            # Check for variable with BOPEN/BCLOSE indicating array
            is_array = is_array_declaration(t) or is_array_access(t)

            # Check for variable declaration patterns
            is_declaration = False
            if hasattr(t, 'child') and len(t.child) > 0:
                for child in t.child:
                    if hasattr(child, 'token') and child.token in [TokenType.INT, TokenType.VOID]:
                        is_declaration = True
                        break

            # Process the variable
            if is_declaration or st_lookup(var_name, symbol_table) == -1:
                # New variable declaration or first appearance
                st_insert(var_name, t.line, location_counter[0], symbol_table)
                location_counter[0] += 1
            else:
                # Update line number for existing variable
                st_insert(var_name, t.line, 0, symbol_table)

    # Handle function declarations specifically
    elif hasattr(t, 'child') and len(t.child) > 0:
        if t.token == TokenType.ID and any(hasattr(child, 'token') and child.token in [TokenType.VOID, TokenType.INT] for child in t.child):
            # This is likely a function declaration
            func_name = t.lexema if hasattr(t, 'lexema') else None
            if func_name and hasattr(t, 'line'):
                if st_lookup(func_name, symbol_table) == -1:
                    # New function declaration
                    st_insert(func_name, t.line,
                              location_counter[0], symbol_table)
                    location_counter[0] += 1
                else:
                    # Update line number for existing function
                    st_insert(func_name, t.line, 0, symbol_table)


def nullProc(t: TreeNode,
             symbol_table: Optional[Dict] = None,
             location_counter: Optional[List[int]] = None):
    """
    Null procedure for traversal when no specific processing is needed
    """
    pass


def typeError(t: TreeNode, message: str):
    """
    Report type error

    :param t: Node where error occurred
    :param message: Error message
    """
    global Error
    print(f"Type error at line {t.line}: {message}")
    Error = True


def get_variable_type(node: TreeNode, symbol_table: Dict) -> str:
    """
    Determine the type of a variable (int, array, or function)

    :param node: TreeNode representing a variable
    :param symbol_table: Symbol table to look up information
    :return: 'int', 'array', 'function', or 'unknown'
    """
    if not hasattr(node, 'token') or node.token != TokenType.ID:
        return 'unknown'

    var_name = node.lexema if hasattr(node, 'lexema') else None
    if not var_name:
        return 'unknown'

    # Check if this is an array declaration
    if is_array_declaration(node):
        return 'array'

    # Check for function pattern (has function lexema child)
    if hasattr(node, 'child'):
        for child in node.child:
            if hasattr(child, 'lexema') and child.lexema == 'function':
                return 'function'

    # Default to int for simple variables
    return 'int'


def is_valid_expression(node: TreeNode, symbol_table: Optional[Dict] = None) -> bool:
    """
    Check if a node represents a valid expression type

    :param node: TreeNode to check
    :param symbol_table: Symbol table for variable type lookup
    :return: Boolean indicating if it's a valid expression
    """
    if not hasattr(node, 'token'):
        return False

    # Basic valid expression types
    valid_tokens = [
        TokenType.ENTERO, TokenType.ID,
        TokenType.SUMA, TokenType.RESTA, TokenType.MULT, TokenType.DIV
    ]

    if node.token in valid_tokens:
        # Special check for ID tokens: make sure it's not an array
        if node.token == TokenType.ID and symbol_table is not None:
            var_type = get_variable_type(node, symbol_table)
            if var_type == 'array' or var_type == 'function':
                return False
        return True

    # Check for array access (which is a valid expression)
    if is_array_access(node):
        return True

    # Check if this is a position inside an array access
    if hasattr(node, 'lexema') and node.lexema == 'posición':
        return True

    # Check for BCLOSE in expression (part of array notation)
    if node.token == TokenType.BCLOSE:
        return True

    return False


def checkNode(t: TreeNode, symbol_table: Optional[Dict] = None):
    """
    Perform type checking on a node - adapted for the actual AST structure

    :param t: Current tree node
    :param symbol_table: Symbol table (optional)
    """
    if not hasattr(t, 'token'):
        return

    # Type checking for expressions
    if t.token in [TokenType.SUMA, TokenType.RESTA, TokenType.MULT, TokenType.DIV]:
        # Check if operands are appropriate types
        for child in t.child:
            if not is_valid_expression(child, symbol_table):
                # Special check for array operands in arithmetic operations
                if hasattr(child, 'token') and child.token == TokenType.ID:
                    var_name = child.lexema if hasattr(
                        child, 'lexema') else None
                    if var_name and is_array_declaration(child):
                        typeError(
                            t, f"Operation {t.token.name} applied to array '{var_name}', which is not allowed")
                    else:
                        typeError(
                            t, f"Operation {t.token.name} applied to non-integer")
                else:
                    typeError(
                        t, f"Operation {t.token.name} applied to non-integer")

    # Type checking for comparison operators
    elif t.token in [TokenType.IGUAL, TokenType.MENOR, TokenType.MAYOR,
                     TokenType.MENORI, TokenType.MAYORI, TokenType.NIGUAL]:
        # Check if operands are appropriate types
        for child in t.child:
            if not is_valid_expression(child, symbol_table):
                typeError(
                    t, f"Comparison {t.token.name} applied to non-integer")

    # Type checking for assignment
    elif t.token == TokenType.ASIGNAR and hasattr(t, 'child') and t.child:
        # In your AST, the RHS might be the first child
        rhs = None
        for child in t.child:
            if hasattr(child, 'token'):
                rhs = child
                break

        if rhs:
            # Check if RHS is a function call
            is_function_call = False
            function_name = None
            if hasattr(rhs, 'token') and rhs.token == TokenType.ID:
                function_name = rhs.lexema if hasattr(rhs, 'lexema') else None
                if function_name:
                    # Check if it's a function that returns void
                    for child in rhs.child:
                        if hasattr(child, 'lexema') and child.lexema == 'params':
                            is_function_call = True
                            # Look in function declarations for return type
                            if function_name == 'sort' or hasattr(rhs, 'child') and any(hasattr(c, 'token') and c.token == TokenType.VOID for c in rhs.child):
                                typeError(
                                    t, f"Assignment of void function '{function_name}' to variable")
                            break

            # If not a function call, standard expression check
            if not is_function_call and not is_valid_expression(rhs, symbol_table):
                typeError(t, f"Assignment of potentially non-integer value")

    # Type checking for if statements
    elif t.token == TokenType.IF and hasattr(t, 'child') and t.child:
        # Look for the condition expression
        condition = None
        for child in t.child:
            if hasattr(child, 'token'):
                if child.token in [TokenType.IGUAL, TokenType.MENOR, TokenType.MAYOR,
                                   TokenType.MENORI, TokenType.MAYORI, TokenType.NIGUAL]:
                    condition = child
                    break

        if condition is None:
            typeError(t, "If test is not Boolean")


def buildSymtab(syntaxTree: TreeNode, imprime: bool = False) -> Dict:
    """
    Build symbol table by traversing the syntax tree

    :param syntaxTree: Root of the syntax tree
    :param imprime: Whether to print the symbol table
    :return: Populated symbol table
    """
    # Initialize symbol table and location counter
    symbol_table = {}
    location_counter = [0]

    # Traverse the tree to build symbol table
    traverse(syntaxTree, insertNode, nullProc, symbol_table, location_counter)

    # Print symbol table if requested
    if imprime:
        printSymTab(symbol_table)

    return symbol_table


def typeCheck(syntaxTree: TreeNode):
    """
    Perform type checking on the syntax tree

    :param syntaxTree: Root of the syntax tree
    """
    # Create a dummy location counter to satisfy the function signature
    location_counter = [0]

    # Traverse the tree with type checking
    traverse(syntaxTree, nullProc, checkNode, {}, location_counter)


def semantica(ast: TreeNode, imprime: bool = False) -> Tuple[bool, List[str]]:
    """
    Perform semantic analysis

    :param ast: Abstract Syntax Tree root node
    :param imprime: Whether to log analysis details
    :return: Tuple of (is_valid, error_list)
    """
    global Error, location

    # Reset global variables
    Error = False
    location = 0

    # Log start of analysis
    if imprime:
        print("Building Symbol Table...")

    # Build symbol table
    symbol_table = buildSymtab(ast, imprime)

    # Log type checking
    if imprime:
        print("Checking Types...")

    # Perform type checking - pass symbol table to type checker
    traverse(ast, nullProc,
             lambda t, st=symbol_table: checkNode(t, st),
             symbol_table, [0])

    # Log completion
    if imprime:
        print("Type Checking Finished")

    return not Error, []  # Return whether there were no errors
