from typing import Tuple, List, Optional, Dict
from globalTypes import *

# Global variables to mimic the example code's approach
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
        # The AST structure has child list, so iterating over it
        for i in range(len(t.child)):
            traverse(t.child[i], preProc, postProc,
                     symbol_table, location_counter)

        # Post-order processing
        postProc(t, symbol_table)


def insertNode(t: TreeNode,
               symbol_table: Dict,
               location_counter: List[int]):
    """
    Insert identifiers into symbol table based on the specific TreeNode structure

    :param t: Current tree node
    :param symbol_table: Symbol table to populate
    :param location_counter: Mutable list to track location
    """
    # Check if this is a variable declaration
    if hasattr(t, 'token'):
        # Case 1: Handle variable declarations - look for 'ID' tokens
        if t.token == TokenType.ID and hasattr(t, 'child') and len(t.child) > 0:
            # This likely indicates a variable declaration
            # The variable name is stored in t.lexema for this structure
            var_name = t.lexema
            if var_name and hasattr(t, 'line'):
                if st_lookup(var_name, symbol_table) == -1:
                    # New variable declaration
                    st_insert(var_name, t.line,
                              location_counter[0], symbol_table)
                    location_counter[0] += 1
                else:
                    # Variable already exists, just add the line number
                    st_insert(var_name, t.line, 0, symbol_table)

        # Case 2: Check for variable references
        if t.token == TokenType.ID and hasattr(t, 'lexema'):
            var_name = t.lexema
            if var_name and hasattr(t, 'line'):
                if st_lookup(var_name, symbol_table) == -1:
                    # First time seeing this variable
                    st_insert(var_name, t.line,
                              location_counter[0], symbol_table)
                    location_counter[0] += 1
                else:
                    # Variable already exists, just add the line number
                    st_insert(var_name, t.line, 0, symbol_table)


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


def checkNode(t: TreeNode, symbol_table: Optional[Dict] = None):
    """
    Perform type checking on a node - adapted for the actual AST structure

    :param t: Current tree node
    :param symbol_table: Symbol table (optional)
    """
    if hasattr(t, 'token'):
        # Type checking for expressions
        if t.token in [TokenType.SUMA, TokenType.RESTA, TokenType.MULT, TokenType.DIV]:
            # Check if operands are integers
            for child in t.child:
                if hasattr(child, 'token') and child.token != TokenType.ENTERO and child.token != TokenType.ID:
                    typeError(t, f"Operation {t.token} applied to non-integer")

        # Type checking for comparison operators
        elif t.token in [TokenType.IGUAL, TokenType.MENOR, TokenType.MAYOR,
                         TokenType.MENORI, TokenType.MAYORI, TokenType.NIGUAL]:
            # Check if operands are integers
            for child in t.child:
                if hasattr(child, 'token') and child.token != TokenType.ENTERO and child.token != TokenType.ID:
                    typeError(
                        t, f"Comparison {t.token} applied to non-integer")

        # Type checking for assignment
        elif t.token == TokenType.ASIGNAR and len(t.child) > 0:
            # Check if right-hand side is an integer
            rhs = t.child[0]
            if hasattr(rhs, 'token') and rhs.token != TokenType.ENTERO and rhs.token != TokenType.ID:
                typeError(t, "Assignment of non-integer value")

        # Type checking for if statements
        elif t.token == TokenType.IF and len(t.child) > 0:
            # Check if condition is a boolean (result of comparison)
            condition = t.child[0]
            if hasattr(condition, 'token') and condition.token not in [
                TokenType.IGUAL, TokenType.MENOR, TokenType.MAYOR,
                TokenType.MENORI, TokenType.MAYORI, TokenType.NIGUAL
            ]:
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

    # Perform type checking
    typeCheck(ast)

    # Log completion
    if imprime:
        print("Type Checking Finished")

    return not Error, []  # Return whether there were no errors
