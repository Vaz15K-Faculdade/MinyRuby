"""Gerador de código BIRL a partir da AST anotada do MiniRuby.

Mapeamento MiniRuby → BIRL (Bambam's "It's show time" Recursive Language):

  MiniRuby                       →  BIRL
  -----------------------------------------------------------
  puts expr_list                 →  CE QUER VER ESSA PORRA? (fmt, args);
  x = expr  (NUMERO, primeira)   →  MONSTRO x = expr;
  x = gets                       →  MONSTRO x;
                                     QUE QUE CE QUER MONSTRAO? ("%d", &x);
  x = gets.chomp (STRING)        →  FRANGO x[256];
                                     QUE QUE CE QUER MONSTRAO? ("%s", x);
  x = expr  (reatribuição)       →  x = expr;
  if expr ... [else ...] end     →  ELE QUE A GENTE QUER? (expr)
                                       ...
                                       NAO VAI DAR NAO
                                       ...
                                       BIRL
  while expr ... end             →  NEGATIVA BAMBAM (expr)
                                       ...
                                       BIRL

Strings são representadas como arrays de char (`FRANGO[256]`) porque a
linguagem BIRL não possui tipo string primitivo. Toda comparação entre
strings gerará `==`/`!=` (comparação de ponteiros em C); o programador
é responsável por usar `strcmp` se desejar semântica por conteúdo.

Limitação conhecida: o primeiro `x = "literal"` apenas declara o array
sem inicialização (BIRL/C não permitem inicializar array de char com
string literal nesta forma simples).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from MiniRubyParser import MiniRubyParser
from erro import Erro

# Tipos BIRL (somente os necessários para este subconjunto)
TIPO_INT: str = "MONSTRO"  # int (32 bits)
TIPO_STR: str = "FRANGO"  # char / char[] (string)
STR_SIZE: int = 256  # tamanho default para arrays de char

# Regex para detectar interpolações de string: #{expr}
_INTERPOLACAO_RE: re.Pattern[str] = re.compile(r"#\{[^}]*\}")

# Operadores por nível de precedência (para cadeias associativas à esquerda)
OPS_EQ: tuple[str, ...] = ("==", "!=")
OPS_REL: tuple[str, ...] = ("<", "<=", ">", ">=")
OPS_ADD: tuple[str, ...] = ("+", "-")


class GeracaoBIRL:
    """Transpila a AST anotada do MiniRuby para código BIRL."""

    INDENTACAO: str = "    "

    def __init__(self, erro_handler: Erro) -> None:
        self.erro_handler: Erro = erro_handler
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._linhas: list[str] = []
        self._indent: int = 0
        self._variaveis: dict[str, str] = {}  # nome → tipo BIRL

    # ============================================================
    # Ponto de entrada
    # ============================================================

    def gerarCodigoBIRL(self, ast: Any) -> str | None:
        """Gera o código BIRL completo. Retorna ``None`` em erro fatal."""
        self._linhas = []
        self._indent = 0
        self._variaveis = {}

        if not isinstance(ast, MiniRubyParser.ProgContext):
            self._erro(0, 0, "AST não é ProgContext; geração BIRL abortada.")
            return None

        self._emit("HORA DO SHOW")
        for stmt in ast.stmt():
            self._gerar_stmt(stmt)
        self._emit("")
        self._emit("BIRL")
        return "\n".join(self._linhas)

    # ============================================================
    # Helpers de emissão
    # ============================================================

    def _emit(self, linha: str) -> None:
        self._linhas.append(self.INDENTACAO * self._indent + linha)

    def _erro(self, linha: int, coluna: int, mensagem: str) -> None:
        self.erro_handler.registrar_erro(
            self.__class__.__name__, linha, coluna, mensagem, "SEMANTICO"
        )

    def _tipo_birl_para_expr(self, expr_ctx: Any) -> str:
        """Infere o tipo BIRL (MONSTRO/FRANGO) a partir do ``type_name``."""
        tipo = getattr(expr_ctx, "type_name", "NUMERO")
        return TIPO_STR if tipo == "STRING" else TIPO_INT

    # ============================================================
    # Statements
    # ============================================================

    def _gerar_stmt(self, ctx: Any) -> None:
        if ctx.simpleStmt():
            self._gerar_simple_stmt(ctx.simpleStmt())
        elif ctx.ifStmt():
            self._gerar_if_stmt(ctx.ifStmt())
        elif ctx.whileStmt():
            self._gerar_while_stmt(ctx.whileStmt())

    def _gerar_simple_stmt(self, ctx: Any) -> None:
        if ctx.printStmt():
            self._gerar_print_stmt(ctx.printStmt())
        elif ctx.assignStmt():
            self._gerar_assign_stmt(ctx.assignStmt())

    def _gerar_print_stmt(self, ctx: Any) -> None:
        expr_list = ctx.exprList()
        if not expr_list:
            # puts sem argumentos → imprime apenas newline
            self._emit('CE QUER VER ESSA PORRA? ("\\n");')
            return

        # Cada expressão gera (trecho_de_formato, expr_str) — pode haver
        # múltiplos pares quando a expressão é uma string interpolada.
        format_pieces: list[str] = []
        args: list[str] = []
        for expr in expr_list.expr():
            for piece, arg in self._gerar_print_arg(expr):
                format_pieces.append(piece)
                if arg:
                    args.append(arg)

        format_str = "".join(format_pieces)
        if args:
            self._emit(f'CE QUER VER ESSA PORRA? ("{format_str}", {", ".join(args)});')
        else:
            self._emit(f'CE QUER VER ESSA PORRA? ("{format_str}");')

    def _gerar_print_arg(self, expr_ctx: Any) -> list[tuple[str, str]]:
        """Decompõe uma expressão em (trecho_format, expr_str) para printf."""
        if self._eh_string_literal(expr_ctx):
            return self._quebrar_string_interpolada(expr_ctx)
        tipo = self._tipo_birl_para_expr(expr_ctx)
        fmt = "%s" if tipo == TIPO_STR else "%d"
        return [(fmt, self._gerar_expr_str(expr_ctx))]

    def _gerar_assign_stmt(self, ctx: Any) -> None:
        nome: str = ctx.ID().getText()
        expr = ctx.expr()
        tipo = self._tipo_birl_para_expr(expr)

        # x = gets (int) → MONSTRO + scanf %d com &
        if self._eh_gets_literal(expr):
            self._garantir_declaracao(nome, TIPO_INT)
            self._emit(f'QUE QUE CE QUER MONSTRAO? ("%d", &{nome});')
            return

        # x = gets.chomp (string) → FRANGO[256] + scanf %s sem &
        if self._eh_gets_chomp(expr):
            self._garantir_declaracao(nome, TIPO_STR)
            self._emit(f'QUE QUE CE QUER MONSTRAO? ("%s", {nome});')
            return

        valor = self._gerar_expr_str(expr)
        if nome not in self._variaveis:
            self._variaveis[nome] = tipo
            if tipo == TIPO_STR:
                # Inicialização de array char a partir de expressão não-trivial
                # é problemática; declaramos sem inicialização.
                self._emit(f"{TIPO_STR} {nome}[{STR_SIZE}];")
                self.logger.warning(
                    f"Variável string '{nome}' declarada sem inicialização."
                )
            else:
                self._emit(f"{TIPO_INT} {nome} = {valor};")
            return

        self._emit(f"{nome} = {valor};")

    def _garantir_declaracao(self, nome: str, tipo: str) -> None:
        """Garante que a variável já foi declarada com o tipo certo."""
        if nome in self._variaveis:
            if self._variaveis[nome] != tipo:
                self._erro(
                    0,
                    0,
                    f"Variável '{nome}' redeclarada com tipo {tipo}; "
                    f"tipo anterior: {self._variaveis[nome]}.",
                )
            return
        self._variaveis[nome] = tipo
        if tipo == TIPO_STR:
            self._emit(f"{TIPO_STR} {nome}[{STR_SIZE}];")
        else:
            self._emit(f"{TIPO_INT} {nome};")

    def _gerar_if_stmt(self, ctx: Any) -> None:
        cond = self._gerar_expr_str(ctx.expr())
        self._emit(f"ELE QUE A GENTE QUER? ({cond})")
        self._indent += 1
        for stmt in ctx.stmt():
            self._gerar_stmt(stmt)
        self._indent -= 1
        if ctx.elsePart():
            self._emit("NAO VAI DAR NAO")
            self._indent += 1
            for stmt in ctx.elsePart().stmt():
                self._gerar_stmt(stmt)
            self._indent -= 1
        self._emit("BIRL")

    def _gerar_while_stmt(self, ctx: Any) -> None:
        cond = self._gerar_expr_str(ctx.expr())
        self._emit(f"NEGATIVA BAMBAM ({cond})")
        self._indent += 1
        for stmt in ctx.stmt():
            self._gerar_stmt(stmt)
        self._indent -= 1
        self._emit("BIRL")

    # ============================================================
    # Expressões
    # ============================================================

    def _gerar_expr_str(self, ctx: Any) -> str:
        nome_ctx = type(ctx).__name__

        if nome_ctx == "ExprContext":
            return self._gerar_expr_str(ctx.orExpr())
        if nome_ctx == "OrExprContext":
            return " || ".join(
                self._gerar_expr_str(ctx.andExpr(i)) for i in range(len(ctx.andExpr()))
            )
        if nome_ctx == "AndExprContext":
            return " && ".join(
                self._gerar_expr_str(ctx.eqExpr(i)) for i in range(len(ctx.eqExpr()))
            )
        if nome_ctx == "EqExprContext":
            return self._gerar_binop_cadeia(ctx, ctx.relExpr, OPS_EQ)
        if nome_ctx == "RelExprContext":
            return self._gerar_binop_cadeia(ctx, ctx.addExpr, OPS_REL)
        if nome_ctx == "AddExprContext":
            return self._gerar_binop_cadeia(ctx, ctx.mulExpr, OPS_ADD)
        if nome_ctx == "MulExprContext":
            return self._gerar_mul_expr(ctx)
        if nome_ctx == "UnaryExprContext":
            if ctx.NOT():
                return "!" + self._gerar_expr_str(ctx.unaryExpr())
            return self._gerar_expr_str(ctx.factor())
        if nome_ctx == "FactorContext":
            return self._gerar_factor(ctx)
        return ctx.getText()

    def _gerar_binop_cadeia(
        self, ctx: Any, accessor: Any, ops_validos: tuple[str, ...]
    ) -> str:
        """Serializa uma cadeia associativa à esquerda ``a OP1 b OP2 c``."""
        itens = accessor()
        if len(itens) == 1:
            return self._gerar_expr_str(itens[0])
        partes = [self._gerar_expr_str(itens[0])]
        for i in range(1, len(itens)):
            op = ctx.getChild(i * 2 - 1).getText()
            if op not in ops_validos:
                self._erro(0, 0, f"Operador inesperado '{op}' na expressão.")
                op = ops_validos[0]
            partes.append(op)
            partes.append(self._gerar_expr_str(itens[i]))
        return " ".join(partes)

    def _gerar_mul_expr(self, ctx: Any) -> str:
        """MulExpr é aninhada à direita na gramática.

        Removemos os parens em torno de MulExpr aninhado porque a AST
        MiniRuby é right-assoc mas Ruby (e BIRL/C) são left-assoc para
        ``*``/``/``. Sem os parens extras, ``a / b / c`` em BIRL vira
        ``(a / b) / c``, que é a semântica pretendida.
        """
        esquerda = self._gerar_expr_str(ctx.unaryExpr())
        filhos = ctx.mulExpr()
        if not filhos:
            return esquerda
        partes = [esquerda]
        for i, filho in enumerate(filhos):
            op = ctx.getChild(i * 2 + 1).getText()
            if op not in ("*", "/"):
                self._erro(0, 0, f"Operador inesperado '{op}' em MulExpr.")
                op = "*"
            partes.append(op)
            partes.append(self._gerar_expr_str(filho))
        return " ".join(partes)

    def _gerar_factor(self, ctx: Any) -> str:
        if ctx.NUMBER():
            return ctx.NUMBER().getText()
        if ctx.STRING():
            return ctx.STRING().getText()
        if ctx.GETS():
            return "0"  # uso isolado de gets sem atribuição é degenerado
        if ctx.ID():
            return ctx.ID().getText()
        if ctx.expr():
            return f"({self._gerar_expr_str(ctx.expr())})"
        return ctx.getText()

    # ============================================================
    # Detecção de padrões específicos na expressão
    # ============================================================

    def _unwrapping_factor(self, expr_ctx: Any) -> Any:
        """Desce na árvore até o ``FactorContext`` se a expressão for trivial."""
        # ``None`` = accessor retorna um único ctx; ``0`` = retorna lista,
        # pegamos o primeiro. Ordem reflete a hierarquia do parser.
        cadeia: tuple[tuple[str, int | None], ...] = (
            ("orExpr", None),
            ("andExpr", 0),
            ("eqExpr", 0),
            ("relExpr", 0),
            ("addExpr", 0),
            ("mulExpr", 0),
            ("unaryExpr", None),
            ("factor", None),
        )
        ctx = expr_ctx
        for accessor, idx in cadeia:
            if not hasattr(ctx, accessor):
                return None
            valor = getattr(ctx, accessor)()
            if valor is None:
                return None
            if idx is not None:
                if not valor:
                    return None
                valor = valor[0]
            ctx = valor
        return ctx

    def _eh_gets_literal(self, expr_ctx: Any) -> bool:
        factor = self._unwrapping_factor(expr_ctx)
        return (
            factor is not None
            and factor.GETS() is not None
            and factor.GETS().getText() == "gets"
        )

    def _eh_gets_chomp(self, expr_ctx: Any) -> bool:
        factor = self._unwrapping_factor(expr_ctx)
        return (
            factor is not None
            and factor.GETS() is not None
            and factor.GETS().getText() == "gets.chomp"
        )

    def _eh_string_literal(self, expr_ctx: Any) -> bool:
        factor = self._unwrapping_factor(expr_ctx)
        return factor is not None and factor.STRING() is not None

    def _quebrar_string_interpolada(self, expr_ctx: Any) -> list[tuple[str, str]]:
        """Decompõe `"texto #{var} mais"` em [(texto, ''), ('%s', var), ...]."""
        factor = self._unwrapping_factor(expr_ctx)
        if factor is None or not factor.STRING():
            return []
        raw = factor.STRING().getText()
        inner = raw[1:-1] if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"' else raw

        partes = _INTERPOLACAO_RE.split(inner)
        nomes = _INTERPOLACAO_RE.findall(inner)

        resultado: list[tuple[str, str]] = []
        for i, parte in enumerate(partes):
            if parte:
                # Escapa % literal para %% (formato printf-like) só nos literais
                resultado.append((parte.replace("%", "%%"), ""))
            if i < len(nomes):
                nome = nomes[i].strip()[2:-1]  # remove "#{ " e " }"
                if nome:
                    resultado.append(("%s", nome))
        return resultado
