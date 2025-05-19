from globalTypes import * 
from symtab import *
import sys

# pc = program counter
pc = 7
# mp = "memory pointer" points to top of memory (for temp storage)
mp = 6
# gp = "global pointer" points to bottom of memory for (global)
# variable storage
gp = 5
# accumulator
ac = 0
# 2nd accumulator
ac1 = 1
# TM location number for current instruction emission
emitLoc = 0
# Highest TM location emitted so far for use in conjunction with emitSkip,
# emitBackup, and emitRestore
highEmitLoc = 0

# Procedure emitComment prints a comment line with comment c in the code file
def emitComment(c):
    if (TraceCode):
        print("* " + c)

# Procedure emitRO emits a register-only TM instruction, where
# op = the opcode
# r = target register
# s = 1st source register
# t = 2nd source register
# c = a comment to be printed if TraceCode is TRUE
def emitRO( op, r, s, t, c):
    global emitLoc
    global highEmitLoc
    print("%3d:  %5s  %d,%d,%d  " % (emitLoc,op,r,s,t), end='')
    emitLoc += 1
    if (TraceCode):
        print("\t" + c, end='')
    print()
    if (highEmitLoc < emitLoc):
        highEmitLoc = emitLoc

# Procedure emitRM emits a register-to-memory TM instruction, where
# op = the opcode
# r = target register
# d = the offset
# s = the base register
# c = a comment to be printed if TraceCode is TRUE
def emitRM( op, r, d, s, c):
    global emitLoc
    global highEmitLoc
    print("%3d:  %5s  %d,%d(%d) " % (emitLoc,op,r,d,s), end='')
    emitLoc += 1
    if (TraceCode):
        print("\t" + c, end='')
    print()
    if (highEmitLoc < emitLoc):
        highEmitLoc = emitLoc

# Function emitSkip skips "howMany" code locations for later backpatch.
# It also returns the current code position
def emitSkip(howMany):
    global emitLoc
    global highEmitLoc
    i = emitLoc
    emitLoc += howMany
    if (highEmitLoc < emitLoc):
        highEmitLoc = emitLoc
    return i

# Procedure emitBackup backs up to loc = a previously skipped location
def emitBackup(loc):
    global emitLoc
    if (loc > highEmitLoc):
        emitComment("BUG in emitBackup")
    emitLoc = loc

# Procedure emitRestore restores the current code position to the highest
# previously unemitted position
def emitRestore():
    global emitLoc
    emitLoc = highEmitLoc

# Procedure emitRM_Abs converts an absolute reference to a pc-relative
# reference when emitting a register-to-memory TM instruction, where
# op = the opcode
# r = target register
# a = the absolute location in memory
# c = a comment to be printed if TraceCode is TRUE
def emitRM_Abs(op, r, a, c):
    global emitLoc
    global highEmitLoc
    print("%3d:  %5s  %d,%d(%d) " % (emitLoc,op,r,a-(emitLoc+1),pc), end='')
    emitLoc+=1
    if (TraceCode):
        print("\t" + c, end='')
    print()
    if (highEmitLoc < emitLoc):
        highEmitLoc = emitLoc

# tmpOffset is the memory offset for temps. It is decremented each time a temp
# is stored, and incremeted when loaded again
tmpOffset = 0

# Procedure genStmt generates code at a statement node
def genStmt(tree):
    if tree.stmt == StmtKind.IfK:
        if (TraceCode):
            emitComment("-> if")
        p1 = tree.child[0]
        p2 = tree.child[1]
        p3 = tree.child[2]
        # generate code for test expression */
        cGen(p1)
        savedLoc1 = emitSkip(1)
        emitComment("if: jump to else belongs here")
        # recurse on then part */
        cGen(p2)
        savedLoc2 = emitSkip(1)
        emitComment("if: jump to end belongs here")
        currentLoc = emitSkip(0)
        emitBackup(savedLoc1)
        emitRM_Abs("JEQ",ac,currentLoc,"if: jmp to else")
        emitRestore()
        # recurse on else part */
        cGen(p3)
        currentLoc = emitSkip(0)
        emitBackup(savedLoc2)
        emitRM_Abs("LDA",pc,currentLoc,"jmp to end")
        emitRestore()
        if (TraceCode):
            emitComment("<- if")
    elif tree.stmt == StmtKind.RepeatK:
        if (TraceCode):
                emitComment("-> repeat")
        p1 = tree.child[0]
        p2 = tree.child[1]
        savedLoc1 = emitSkip(0)
        emitComment("repeat: jump after body comes back here")
        # generate code for body */
        cGen(p1)
        # generate code for test */
        cGen(p2)
        emitRM_Abs("JEQ",ac,savedLoc1,"repeat: jmp back to body")
        if (TraceCode):
            emitComment("<- repeat")
    elif tree.stmt == StmtKind.AssignK:
        if (TraceCode):
            emitComment("-> assign")
        # generate code for rhs */
        cGen(tree.child[0])
        # now store value */
        loc = st_lookup(tree.name)
        emitRM("ST",ac,loc,gp,"assign: store value")
        if (TraceCode):
            emitComment("<- assign")
    elif  tree.stmt == StmtKind.ReadK:
        emitRO("IN",ac,0,0,"read integer value")
        loc = st_lookup(tree.name)
        emitRM("ST",ac,loc,gp,"read: store value")
    elif tree.stmt == StmtKind.WriteK:
        # generate code for expression to write */
        cGen(tree.child[0])
        # now output it */
        emitRO("OUT",ac,0,0,"write ac")

# Procedure genExp generates code at an expression node */
def genExp(tree):
    global tmpOffset
    if tree.exp == ExpKind.ConstK:
        if (TraceCode):
            emitComment("-> Const")
        # gen code to load integer constant using LDC */
        emitRM("LDC",ac,tree.val,0,"load const")
        if (TraceCode):
            emitComment("<- Const")
    elif tree.exp == ExpKind.IdK:
        if (TraceCode):
            emitComment("-> Id")
        loc = st_lookup(tree.name)
        emitRM("LD",ac,loc,gp,"load id value")
        if (TraceCode):
            emitComment("<- Id")
    elif tree.exp == ExpKind.OpK:
        if (TraceCode):
            emitComment("-> Op")
        p1 = tree.child[0]
        p2 = tree.child[1]
        # gen code for ac = left arg */
        cGen(p1);
        # gen code to push left operand */
        emitRM("ST",ac,tmpOffset,mp,"op: push left")
        tmpOffset-=1
        # gen code for ac = right operand */
        cGen(p2);
        # now load left operand */
        tmpOffset+=1;
        emitRM("LD",ac1,tmpOffset,mp,"op: load left")
        if tree.op == TokenType.PLUS:
            emitRO("ADD",ac,ac1,ac,"op +")
        elif tree.op == TokenType.MINUS:
            emitRO("SUB",ac,ac1,ac,"op -")
        elif tree.op == TokenType.TIMES:
            emitRO("MUL",ac,ac1,ac,"op *")
        elif tree.op == TokenType.OVER:
            emitRO("DIV",ac,ac1,ac,"op /")
        elif tree.op == TokenType.LT:
            emitRO("SUB",ac,ac1,ac,"op <")
            emitRM("JLT",ac,2,pc,"br if true") 
            emitRM("LDC",ac,0,ac,"false case") 
            emitRM("LDA",pc,1,pc,"unconditional jmp") 
            emitRM("LDC",ac,1,ac,"true case") 
        elif tree.op == TokenType.EQ:
            emitRO("SUB",ac,ac1,ac,"op ==")
            emitRM("JEQ",ac,2,pc,"br if true")
            emitRM("LDC",ac,0,ac,"false case")
            emitRM("LDA",pc,1,pc,"unconditional jmp") 
            emitRM("LDC",ac,1,ac,"true case")
        else:
            emitComment("BUG: Unknown operator")
        if (TraceCode):
            emitComment("<- Op")

# Procedure cGen recursively generates code by tree traversal
def cGen(tree):
    if (tree != None):
        if tree.nodekind == NodeKind.StmtK:
            genStmt(tree)
        elif tree.nodekind == NodeKind.ExpK:
            genExp(tree)
        cGen(tree.sibling)

#********************************************
# the primary function of the code generator 
#********************************************
# Procedure codeGen generates code to a code
# file by traversal of the syntax tree. The
# second parameter (codefile) is the file name
# of the code file, and is used to print the
# file name as a comment in the code file
def codeGen(syntaxTree, codefile, trace):
    global TraceCode
    global code
    #print(BucketList) # ¿Por qué se mantiene esta variable si está declarada en symtab.py?
    TraceCode = trace # Si es True imprime comentarios
    stdout = sys.stdout
    sys.stdout = open(codefile + '.tm', 'w')
    s = "File: " + codefile
    emitComment("TINY Compilation to TM Code")
    emitComment(s);
    # generate standard prelude
    emitComment("Standard prelude:")
    emitRM("LD",mp,0,ac,"load maxaddress from location 0")
    emitRM("ST",ac,0,ac,"clear location 0")
    emitComment("End of standard prelude.")
    # generate code for TINY program
    cGen(syntaxTree)
    # finish
    emitComment("End of execution.");
    emitRO("HALT",0,0,0,"");
    sys.stdout.close()
    sys.stdout = stdout
    

