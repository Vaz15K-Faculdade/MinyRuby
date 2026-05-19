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
        self._constantes_zero = set()
        self.ast_anotada = None

    def _registrar_variavel(self, nome_var: str, tipo_var: str, linha: int, coluna: int,
                            atribuida_zero: bool = False):
        if nome_var in self.escopo_atual:
            info = self.escopo_atual[nome_var]
            self.logger.info(
                f"Variável '{nome_var}' reatribuída. "
                f"Tipo anterior: {info['type_name']}, Novo tipo: {tipo_var}."
            )
            info['type_name'] = tipo_var
        else:
            self.logger.info(
                f"Variável '{nome_var}' (tipo: {tipo_var}) declarada na linha {linha}, coluna {coluna}."
            )
            self.escopo_atual[nome_var] = {
                "linha": linha,
                "coluna": coluna,
                "usada": False,
                "type_name": tipo_var
            }
        self.variaveis_declaradas_globalmente.add(nome_var)
        self.escopo_atual[nome_var]["usada_como_alvo"] = True
        if atribuida_zero:
            self._constantes_zero.add(nome_var)
        else:
            self._constantes_zero.discard(nome_var)

    def _verificar_uso_variavel(self, nome_var: str, ctx):
        linha = ctx.start.line
        coluna = ctx.start.column + 1
        if nome_var not in self.escopo_atual:
            msg = f"Variável '{nome_var}' não declarada."
            self.erro_handler.registrar_erro(
                "Analisador Semântico", linha, coluna, msg, tipo_erro="SEMANTICO"
            )
            return None
        info = self.escopo_atual[nome_var]
        info["usada"] = True
        self.logger.info(
            f"Variável '{nome_var}' (tipo: {info['type_name']}) usada na linha {linha}, coluna {coluna}."
        )
        return info["type_name"]

    def _tem_zero_literal(self, ctx):
        if hasattr(ctx, 'unaryExpr'):
            unary = ctx.unaryExpr()
            if hasattr(unary, 'factor'):
                factor_ctx = unary.factor()
                if factor_ctx:
                    if factor_ctx.NUMBER():
                        try:
                            return float(factor_ctx.NUMBER().getText()) == 0.0
                        except ValueError:
                            pass
                    elif factor_ctx.ID():
                        nome = factor_ctx.ID().getText()
                        if nome in self._constantes_zero:
                            return True
                    elif factor_ctx.expr():
                        return self._expr_eh_zero(factor_ctx.expr())
        if hasattr(ctx, 'mulExpr'):
            right = ctx.mulExpr(0)
            if right:
                return self._tem_zero_literal(right)
        texto = ctx.getText().strip()
        try:
            return float(texto) == 0.0
        except ValueError:
            return False

    def _expr_eh_zero(self, expr_ctx):
        or_ctx = expr_ctx.orExpr()
        if or_ctx:
            and_count = len(or_ctx.andExpr())
            if and_count == 1:
                and_ctx = or_ctx.andExpr(0)
                eq_count = len(and_ctx.eqExpr())
                if eq_count == 1:
                    eq_ctx = and_ctx.eqExpr(0)
                    rel_count = len(eq_ctx.relExpr())
                    if rel_count == 1:
                        rel_ctx = eq_ctx.relExpr(0)
                        add_count = len(rel_ctx.addExpr())
                        if add_count == 1:
                            add_ctx = rel_ctx.addExpr(0)
                            mul_count = len(add_ctx.mulExpr())
                            if mul_count == 1:
                                mul_ctx = add_ctx.mulExpr(0)
                                unary = mul_ctx.unaryExpr()
                                if unary and hasattr(unary, 'factor'):
                                    factor_ctx = unary.factor()
                                    if factor_ctx:
                                        if factor_ctx.NUMBER():
                                            try:
                                                return float(factor_ctx.NUMBER().getText()) == 0.0
                                            except ValueError:
                                                pass
                                        elif factor_ctx.ID():
                                            nome = factor_ctx.ID().getText()
                                            if nome in self._constantes_zero:
                                                return True
        return False

    # ============================================================
    # Expressões: exit handlers (pós-ordem para propagação de tipos)
    # ============================================================

    def exitFactor(self, ctx: MiniRubyParser.FactorContext):
        self.logger.info(f"exitFactor: '{ctx.getText()}'")
        if ctx.NUMBER():
            ctx.type_name = "NUMERO"
        elif ctx.STRING():
            ctx.type_name = "STRING"
        elif ctx.GETS():
            ctx.type_name = "NUMERO"
        elif ctx.ID():
            nome_var = ctx.ID().getText()
            tipo = self._verificar_uso_variavel(nome_var, ctx)
            ctx.type_name = tipo if tipo else "ERRO_TIPO"
        elif ctx.expr():
            inner = ctx.expr()
            ctx.type_name = inner.type_name if hasattr(inner, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"  -> {ctx.type_name}")

    def exitUnaryExpr(self, ctx: MiniRubyParser.UnaryExprContext):
        self.logger.info(f"exitUnaryExpr: '{ctx.getText()}'")
        if ctx.NOT():
            inner = ctx.unaryExpr()
            inner_type = inner.type_name if hasattr(inner, 'type_name') else "ERRO_TIPO"
            if inner_type == "ERRO_TIPO" or inner_type.startswith("ERRO_"):
                ctx.type_name = "ERRO_TIPO"
            elif inner_type in ("NUMERO", "BOOLEANO"):
                ctx.type_name = "BOOLEANO"
            else:
                msg = (
                    f"Operador '!' requer operando numérico ou booleano. "
                    f"Obtido: {inner_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    ctx.start.line, ctx.start.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                ctx.type_name = "ERRO_TIPO"
        elif ctx.factor():
            factor_ctx = ctx.factor()
            ctx.type_name = factor_ctx.type_name if hasattr(factor_ctx, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"  -> {ctx.type_name}")

    def exitMulExpr(self, ctx: MiniRubyParser.MulExprContext):
        self.logger.info(f"exitMulExpr: '{ctx.getText()}'")
        left = ctx.unaryExpr()
        left_type = left.type_name if hasattr(left, 'type_name') else "ERRO_TIPO"

        if left_type == "ERRO_TIPO" or left_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            self.logger.info(f"  -> ERRO_TIPO (erro no operando esquerdo)")
            return

        if ctx.MUL(0) or ctx.DIV(0):
            op_node = ctx.getChild(1)
            op_text = op_node.getText()
            right_ctx = ctx.mulExpr(0)
            right_type = right_ctx.type_name if hasattr(right_ctx, 'type_name') else "ERRO_TIPO"

            if right_type == "ERRO_TIPO" or right_type.startswith("ERRO_"):
                ctx.type_name = "ERRO_TIPO"
                self.logger.info(f"  -> ERRO_TIPO (erro no operando direito)")
                return

            if left_type == "NUMERO" and right_type == "NUMERO":
                if op_text == '/' and self._tem_zero_literal(right_ctx):
                    msg = "Divisão por zero detectada."
                    self.erro_handler.registrar_erro(
                        "Analisador Semântico",
                        op_node.symbol.line, op_node.symbol.column + 1,
                        msg, tipo_erro="SEMANTICO"
                    )
                ctx.type_name = "NUMERO"
            else:
                msg = (
                    f"Operador '{op_text}' requer operandos numéricos. "
                    f"Obtidos: {left_type} e {right_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    op_node.symbol.line, op_node.symbol.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                ctx.type_name = "ERRO_TIPO"
        else:
            ctx.type_name = left_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitAddExpr(self, ctx: MiniRubyParser.AddExprContext):
        self.logger.info(f"exitAddExpr: '{ctx.getText()}'")
        current_type = "ERRO_TIPO"

        primeiro = ctx.mulExpr(0)
        if hasattr(primeiro, 'type_name'):
            current_type = primeiro.type_name
        else:
            ctx.type_name = "ERRO_TIPO"
            self.logger.info(f"  -> ERRO_TIPO (primeiro mulExpr sem type_name)")
            return

        if current_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            self.logger.info(f"  -> ERRO_TIPO (erro no primeiro mulExpr)")
            return

        num_ops = len(ctx.mulExpr())
        for i in range(num_ops - 1):
            op_node = ctx.getChild(i * 2 + 1)
            op_text = op_node.getText()
            right = ctx.mulExpr(i + 1)
            right_type = right.type_name if hasattr(right, 'type_name') else "ERRO_TIPO"

            if right_type.startswith("ERRO_"):
                current_type = "ERRO_TIPO"
                break

            if op_text in ('+', '-'):
                if current_type == "NUMERO" and right_type == "NUMERO":
                    current_type = "NUMERO"
                else:
                    msg = (
                        f"Operador '{op_text}' requer operandos numéricos. "
                        f"Obtidos: {current_type} e {right_type}."
                    )
                    self.erro_handler.registrar_erro(
                        "Analisador Semântico",
                        op_node.symbol.line, op_node.symbol.column + 1,
                        msg, tipo_erro="SEMANTICO"
                    )
                    current_type = "ERRO_TIPO"
                    break

        ctx.type_name = current_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitRelExpr(self, ctx: MiniRubyParser.RelExprContext):
        self.logger.info(f"exitRelExpr: '{ctx.getText()}'")
        current_type = "ERRO_TIPO"

        primeiro = ctx.addExpr(0)
        if hasattr(primeiro, 'type_name'):
            current_type = primeiro.type_name
        else:
            ctx.type_name = "ERRO_TIPO"
            return

        if current_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            return

        num_ops = len(ctx.addExpr())
        for i in range(num_ops - 1):
            op_node = ctx.getChild(i * 2 + 1)
            op_text = op_node.getText()
            right = ctx.addExpr(i + 1)
            right_type = right.type_name if hasattr(right, 'type_name') else "ERRO_TIPO"

            if right_type.startswith("ERRO_"):
                current_type = "ERRO_TIPO"
                break

            if current_type == "NUMERO" and right_type == "NUMERO":
                current_type = "BOOLEANO"
            else:
                msg = (
                    f"Operador relacional '{op_text}' requer operandos numéricos. "
                    f"Obtidos: {current_type} e {right_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    op_node.symbol.line, op_node.symbol.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                current_type = "ERRO_TIPO"
                break

        ctx.type_name = current_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitEqExpr(self, ctx: MiniRubyParser.EqExprContext):
        self.logger.info(f"exitEqExpr: '{ctx.getText()}'")
        current_type = "ERRO_TIPO"

        primeiro = ctx.relExpr(0)
        if hasattr(primeiro, 'type_name'):
            current_type = primeiro.type_name
        else:
            ctx.type_name = "ERRO_TIPO"
            return

        if current_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            return

        num_ops = len(ctx.relExpr())
        for i in range(num_ops - 1):
            op_node = ctx.getChild(i * 2 + 1)
            op_text = op_node.getText()
            right = ctx.relExpr(i + 1)
            right_type = right.type_name if hasattr(right, 'type_name') else "ERRO_TIPO"

            if right_type.startswith("ERRO_"):
                current_type = "ERRO_TIPO"
                break

            if current_type == right_type:
                current_type = "BOOLEANO"
            else:
                msg = (
                    f"Operador '{op_text}' requer operandos do mesmo tipo. "
                    f"Obtidos: {current_type} e {right_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    op_node.symbol.line, op_node.symbol.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                current_type = "ERRO_TIPO"
                break

        ctx.type_name = current_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitAndExpr(self, ctx: MiniRubyParser.AndExprContext):
        self.logger.info(f"exitAndExpr: '{ctx.getText()}'")
        current_type = "ERRO_TIPO"

        primeiro = ctx.eqExpr(0)
        if hasattr(primeiro, 'type_name'):
            current_type = primeiro.type_name
        else:
            ctx.type_name = "ERRO_TIPO"
            return

        if current_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            return

        num_ops = len(ctx.eqExpr())
        for i in range(num_ops - 1):
            op_node = ctx.getChild(i * 2 + 1)
            right = ctx.eqExpr(i + 1)
            right_type = right.type_name if hasattr(right, 'type_name') else "ERRO_TIPO"

            if right_type.startswith("ERRO_"):
                current_type = "ERRO_TIPO"
                break

            if current_type == "BOOLEANO" and right_type == "BOOLEANO":
                current_type = "BOOLEANO"
            else:
                msg = (
                    f"Operador '&&' / 'and' requer operandos booleanos. "
                    f"Obtidos: {current_type} e {right_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    op_node.symbol.line, op_node.symbol.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                current_type = "ERRO_TIPO"
                break

        ctx.type_name = current_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitOrExpr(self, ctx: MiniRubyParser.OrExprContext):
        self.logger.info(f"exitOrExpr: '{ctx.getText()}'")
        current_type = "ERRO_TIPO"

        primeiro = ctx.andExpr(0)
        if hasattr(primeiro, 'type_name'):
            current_type = primeiro.type_name
        else:
            ctx.type_name = "ERRO_TIPO"
            return

        if current_type.startswith("ERRO_"):
            ctx.type_name = "ERRO_TIPO"
            return

        num_ops = len(ctx.andExpr())
        for i in range(num_ops - 1):
            op_node = ctx.getChild(i * 2 + 1)
            right = ctx.andExpr(i + 1)
            right_type = right.type_name if hasattr(right, 'type_name') else "ERRO_TIPO"

            if right_type.startswith("ERRO_"):
                current_type = "ERRO_TIPO"
                break

            if current_type == "BOOLEANO" and right_type == "BOOLEANO":
                current_type = "BOOLEANO"
            else:
                msg = (
                    f"Operador '||' / 'or' requer operandos booleanos. "
                    f"Obtidos: {current_type} e {right_type}."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    op_node.symbol.line, op_node.symbol.column + 1,
                    msg, tipo_erro="SEMANTICO"
                )
                current_type = "ERRO_TIPO"
                break

        ctx.type_name = current_type
        self.logger.info(f"  -> {ctx.type_name}")

    def exitExpr(self, ctx: MiniRubyParser.ExprContext):
        or_ctx = ctx.orExpr()
        ctx.type_name = or_ctx.type_name if hasattr(or_ctx, 'type_name') else "ERRO_TIPO"

    # ============================================================
    # Statements
    # ============================================================

    def enterAssignStmt(self, ctx: MiniRubyParser.AssignStmtContext):
        nome_var = ctx.ID().getText()
        linha = ctx.start.line
        coluna = ctx.start.column + 1
        if nome_var not in self.escopo_atual:
            self.logger.info(
                f"Variável '{nome_var}' registrada (pré-declaração) na linha {linha}, coluna {coluna}."
            )
            self.escopo_atual[nome_var] = {
                "linha": linha,
                "coluna": coluna,
                "usada": False,
                "type_name": "NUMERO"
            }
            self.variaveis_declaradas_globalmente.add(nome_var)
        else:
            self.logger.info(
                f"Variável '{nome_var}' reatribuída na linha {linha}, coluna {coluna}."
            )

    def exitAssignStmt(self, ctx: MiniRubyParser.AssignStmtContext):
        nome_var = ctx.ID().getText()
        linha = ctx.start.line
        coluna = ctx.start.column + 1
        expr_ctx = ctx.expr()
        tipo_expr = expr_ctx.type_name if hasattr(expr_ctx, 'type_name') else "ERRO_TIPO"
        self.logger.info(f"Atribuição: {nome_var} = [expr tipo: {tipo_expr}]")
        if not tipo_expr.startswith("ERRO_"):
            eh_zero = self._expr_eh_zero(expr_ctx)
            self._registrar_variavel(nome_var, tipo_expr, linha, coluna, atribuida_zero=eh_zero)

    def exitPrintStmt(self, ctx: MiniRubyParser.PrintStmtContext):
        self.logger.info(f"exitPrintStmt: '{ctx.getText()}'")
        expr_list = ctx.exprList()
        if not expr_list:
            return
        for expr_item in expr_list.expr():
            tipo = expr_item.type_name if hasattr(expr_item, 'type_name') else "ERRO_TIPO"
            self.logger.info(f"  puts item: '{expr_item.getText()}' tipo: {tipo}")
            if tipo.startswith("ERRO_"):
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    expr_item.start.line, expr_item.start.column + 1,
                    f"Expressão '{expr_item.getText()}' no comando puts contém erro de tipo ({tipo}).",
                    tipo_erro="SEMANTICO"
                )

    def _verificar_condicao_booleana(self, expr_ctx, contexto: str):
        tipo = expr_ctx.type_name if hasattr(expr_ctx, 'type_name') else "ERRO_TIPO"
        if tipo.startswith("ERRO_"):
            return
        if tipo != "BOOLEANO":
            msg = f"Condição do {contexto} deve ser booleana. Obtido: {tipo}."
            self.erro_handler.registrar_erro(
                "Analisador Semântico",
                expr_ctx.start.line, expr_ctx.start.column + 1,
                msg, tipo_erro="SEMANTICO"
            )

    def exitIfStmt(self, ctx: MiniRubyParser.IfStmtContext):
        self.logger.info("exitIfStmt: if ... end")
        self._verificar_condicao_booleana(ctx.expr(), "if")

    def exitWhileStmt(self, ctx: MiniRubyParser.WhileStmtContext):
        self.logger.info("exitWhileStmt: while ... end")
        self._verificar_condicao_booleana(ctx.expr(), "while")

    # ============================================================
    # Finalização
    # ============================================================

    def exitProg(self, ctx: MiniRubyParser.ProgContext):
        self.logger.info("--- Verificação Final Semântica ---")
        for nome_var, info in self.escopo_atual.items():
            if info.get("usada_como_alvo", False) and not info["usada"]:
                msg = (
                    f"Variável '{nome_var}' declarada na linha {info['linha']} "
                    f"mas nunca utilizada."
                )
                self.erro_handler.registrar_erro(
                    "Analisador Semântico",
                    info['linha'], info['coluna'],
                    msg, tipo_erro="AVISO_SEMANTICO"
                )
        self.logger.info("Análise semântica concluída (com possíveis avisos/erros).")
        self.ast_anotada = ctx


class AnaliseSemantica:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)

    def executarAnaliseSemantica(self, ast_parser):
        self.logger.info("Iniciando análise semântica...")
        if not ast_parser:
            self.erro_handler.registrar_erro(
                "Analisador Semântico", 0, 0,
                "AST nula passada para análise semântica.",
                tipo_erro="SEMANTICO"
            )
            return None
        if self.erro_handler.houve_erro_fatal():
            self.logger.warning(
                "Erros fatais detectados em fases anteriores. "
                "Análise semântica não será executada."
            )
            return ast_parser

        try:
            listener_semantico = MiniRubySemanticoListenerImpl(self.erro_handler)
            walker = ParseTreeWalker()
            walker.walk(listener_semantico, ast_parser)

            if not self.erro_handler.tem_erros_semanticos:
                self.logger.info("Análise semântica concluída com sucesso (sem erros semânticos fatais).")
            else:
                self.logger.error("Análise semântica encontrou ERROS.")
            return ast_parser
        except Exception as e:
            self.erro_handler.registrar_erro(
                "Analisador Semântico", 0, 0,
                f"Erro inesperado na análise semântica: {e}",
                tipo_erro="SEMANTICO"
            )
            self.logger.exception("Detalhes da exceção:")
            return ast_parser
