from globalTypes import TokenType, TreeNode
from enum import Enum
from mainSemantica import st_lookup, is_function_node


class TypeKind(Enum):
    INT = 0
    VOID = 1
    ARRAY = 2
    ERROR = 3


class TypeInfo:
    def __init__(self, kind, size=None):
        self.kind = kind
        self.size = size  # For arrays


def get_type_from_node(node):
    if not node:
        return TypeInfo(TypeKind.ERROR)

    # Check if it's a function
    if is_function_node(node):
        return TypeInfo(TypeKind.INT if node.child[0].token == TokenType.INT else TypeKind.VOID)

    # Check if it's an array
    if node.child and len(node.child) > 1 and node.child[1].token == TokenType.VARIABLE:
        if node.child[1].child and len(node.child[1].child) > 0:
            if node.child[1].child[0].token == TokenType.BOPEN:
                return TypeInfo(TypeKind.ARRAY, node.child[1].child[1].lexema if len(node.child[1].child) > 1 else None)

    # Check if it's a basic type
    if node.child and node.child[0].token == TokenType.INT:
        return TypeInfo(TypeKind.INT)
    elif node.child and node.child[0].token == TokenType.VOID:
        return TypeInfo(TypeKind.VOID)

    return TypeInfo(TypeKind.ERROR)


def check_types(node):
    if not node:
        return True, None

    # Check children first (bottom-up)
    for child in node.child:
        is_valid, error = check_types(child)
        if not is_valid:
            return False, error

    # Now check the current node
    if node.token == TokenType.ID:
        # Check assignments
        if node.parent and node.parent.token == TokenType.ASIGNAR:
            left_type = get_type_from_node(node)
            right_type = get_type_from_node(node.parent.child[1]) if len(
                node.parent.child) > 1 else TypeInfo(TypeKind.ERROR)

            # Check if right side is a function call
            if right_type.kind == TypeKind.INT and node.parent.child[1].token == TokenType.ID:
                func_info = st_lookup(node.parent.child[1].lexema)
                if func_info and is_function_node(node.parent.child[1]):
                    right_type = TypeInfo(TypeKind.INT)

            # Type compatibility checks
            if left_type.kind == TypeKind.ARRAY and right_type.kind != TypeKind.ARRAY:
                return False, f"Error: Cannot assign non-array to array in line {node.line}"
            if left_type.kind == TypeKind.INT and right_type.kind not in [TypeKind.INT, TypeKind.ARRAY]:
                return False, f"Error: Cannot assign non-integer to integer in line {node.line}"
            if left_type.kind == TypeKind.VOID:
                return False, f"Error: Cannot assign to void type in line {node.line}"

        # Check array access
        if node.parent and node.parent.token == TokenType.POSITION:
            var_type = get_type_from_node(node)
            if var_type.kind != TypeKind.ARRAY:
                return False, f"Error: Array access on non-array type in line {node.line}"

        # Check function calls
        if node.parent and node.parent.token == TokenType.PARAMS:
            func_info = st_lookup(node.lexema)
            if func_info and is_function_node(node):
                return True, None
            return False, f"Error: Undefined function '{node.lexema}' in line {node.line}"

    return True, None
