import logging
from antlr4 import ParseTreeWalker
from MiniRubyParser import MiniRubyParser
from MiniRubyListener import MiniRubyListener
from erro import Erro

class MiniRubySemanticoListenerImpl(MiniRubyListener):
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)
        self.escopo_atual = {}
        self.variaveis_declaradas_globalmente = set()
        self.ast_anotada = None

    def enterAssignStmt(self, ctx: MiniRubyParser.AssignStmtContext):
        if ctx.ID():
            nome_var = ctx.ID().getText()
            if nome_var not in self.escopo_atual:
                self.escopo_atual[nome_var] = {"linha": ctx.start.line, "coluna": ctx.start.column + 1, "usada": False}
                self.variaveis_declaradas_globalmente.add(nome_var)

    def enterFactor(self, ctx: MiniRubyParser.FactorContext):
        if ctx.ID():
            nome_var = ctx.ID().getText()
            if nome_var not in self.escopo_atual:
                msg = f"Variável '{nome_var}' não declarada."
                self.erro_handler.registrar_erro("Analisador Semântico", ctx.start.line, ctx.start.column + 1, msg, tipo_erro="SEMANTICO")

class AnaliseSemantica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)

    def executarAnaliseSemantica(self, ast_parser):
        self.logger.info("Iniciando análise semântica...")
        if not ast_parser:
             self.erro_handler.registrar_erro("Analisador Semântico", 0, 0, "AST nula passada para análise semântica.", tipo_erro="SEMANTICO")
             return None
             
        try:
            listener_semantico = MiniRubySemanticoListenerImpl(self.erro_handler)
            walker = ParseTreeWalker()
            walker.walk(listener_semantico, ast_parser)
            listener_semantico.ast_anotada = ast_parser

            if not self.erro_handler.tem_erros_semanticos:
                self.logger.info("Análise semântica concluída sem erros.")
            else:
                self.logger.error("Erros semânticos detectados.")
            return ast_parser
        except Exception as e:
             self.erro_handler.registrar_erro("Analisador Semântico", 0, 0, f"Erro inesperado na análise semântica: {e}", tipo_erro="SEMANTICO")
             return None
