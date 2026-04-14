# Generated from MiniRuby.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .MiniRubyParser import MiniRubyParser
else:
    from MiniRubyParser import MiniRubyParser

# This class defines a complete listener for a parse tree produced by MiniRubyParser.
class MiniRubyListener(ParseTreeListener):

    # Enter a parse tree produced by MiniRubyParser#prog.
    def enterProg(self, ctx:MiniRubyParser.ProgContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#prog.
    def exitProg(self, ctx:MiniRubyParser.ProgContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#stmt.
    def enterStmt(self, ctx:MiniRubyParser.StmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#stmt.
    def exitStmt(self, ctx:MiniRubyParser.StmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#simpleStmt.
    def enterSimpleStmt(self, ctx:MiniRubyParser.SimpleStmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#simpleStmt.
    def exitSimpleStmt(self, ctx:MiniRubyParser.SimpleStmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#printStmt.
    def enterPrintStmt(self, ctx:MiniRubyParser.PrintStmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#printStmt.
    def exitPrintStmt(self, ctx:MiniRubyParser.PrintStmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#assignStmt.
    def enterAssignStmt(self, ctx:MiniRubyParser.AssignStmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#assignStmt.
    def exitAssignStmt(self, ctx:MiniRubyParser.AssignStmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#ifStmt.
    def enterIfStmt(self, ctx:MiniRubyParser.IfStmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#ifStmt.
    def exitIfStmt(self, ctx:MiniRubyParser.IfStmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#elsePart.
    def enterElsePart(self, ctx:MiniRubyParser.ElsePartContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#elsePart.
    def exitElsePart(self, ctx:MiniRubyParser.ElsePartContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#whileStmt.
    def enterWhileStmt(self, ctx:MiniRubyParser.WhileStmtContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#whileStmt.
    def exitWhileStmt(self, ctx:MiniRubyParser.WhileStmtContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#exprList.
    def enterExprList(self, ctx:MiniRubyParser.ExprListContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#exprList.
    def exitExprList(self, ctx:MiniRubyParser.ExprListContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#expr.
    def enterExpr(self, ctx:MiniRubyParser.ExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#expr.
    def exitExpr(self, ctx:MiniRubyParser.ExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#orExpr.
    def enterOrExpr(self, ctx:MiniRubyParser.OrExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#orExpr.
    def exitOrExpr(self, ctx:MiniRubyParser.OrExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#andExpr.
    def enterAndExpr(self, ctx:MiniRubyParser.AndExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#andExpr.
    def exitAndExpr(self, ctx:MiniRubyParser.AndExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#eqExpr.
    def enterEqExpr(self, ctx:MiniRubyParser.EqExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#eqExpr.
    def exitEqExpr(self, ctx:MiniRubyParser.EqExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#relExpr.
    def enterRelExpr(self, ctx:MiniRubyParser.RelExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#relExpr.
    def exitRelExpr(self, ctx:MiniRubyParser.RelExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#addExpr.
    def enterAddExpr(self, ctx:MiniRubyParser.AddExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#addExpr.
    def exitAddExpr(self, ctx:MiniRubyParser.AddExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#mulExpr.
    def enterMulExpr(self, ctx:MiniRubyParser.MulExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#mulExpr.
    def exitMulExpr(self, ctx:MiniRubyParser.MulExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#unaryExpr.
    def enterUnaryExpr(self, ctx:MiniRubyParser.UnaryExprContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#unaryExpr.
    def exitUnaryExpr(self, ctx:MiniRubyParser.UnaryExprContext):
        pass


    # Enter a parse tree produced by MiniRubyParser#factor.
    def enterFactor(self, ctx:MiniRubyParser.FactorContext):
        pass

    # Exit a parse tree produced by MiniRubyParser#factor.
    def exitFactor(self, ctx:MiniRubyParser.FactorContext):
        pass



del MiniRubyParser