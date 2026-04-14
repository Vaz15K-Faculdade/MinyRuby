import logging
from antlr4.error.ErrorListener import ErrorListener as ANTLRErrorListener

logger = logging.getLogger(__name__)

class Erro:
    def __init__(self):
        self.tem_erros_lexicos = False
        self.tem_erros_sintaticos = False
        self.tem_erros_semanticos = False
        self.tem_erros_tac = False
        self.tem_erros_llvm = False

    def registrar_erro(self, modulo: str, linha: int, coluna: int, mensagem: str, tipo_erro: str = "GERAL"):
        # Format the exact message the user wants if it's already formatted, otherwise fallback to default
        if tipo_erro == "LEXICO" or tipo_erro == "SINTATICO":
            log_msg = mensagem
        else:
            log_msg = f"ERRO [{modulo}]: Linha {linha}, Coluna {coluna} - {mensagem}"
            
        logging.getLogger("ERRO_HANDLER").error(log_msg)

        if tipo_erro == "LEXICO":
            self.tem_erros_lexicos = True
            print(log_msg)
        elif tipo_erro == "SINTATICO":
            self.tem_erros_sintaticos = True
            print(log_msg)
        elif tipo_erro == "SEMANTICO":
            self.tem_erros_semanticos = True
        elif tipo_erro == "TAC":
            self.tem_erros_tac = True
        elif tipo_erro == "LLVM":
            self.tem_erros_llvm = True
        elif tipo_erro == "AVISO_SEMANTICO" or tipo_erro == "AVISO":
            logging.getLogger("ERRO_HANDLER").warning(log_msg.replace("ERRO", "AVISO"))
            return

    def houve_erro_fatal(self) -> bool:
        return self.tem_erros_lexicos or self.tem_erros_sintaticos or self.tem_erros_semanticos

class CustomErrorListener(ANTLRErrorListener):
    def __init__(self, erro_handler: Erro, modulo: str):
        super().__init__()
        self.erro_handler = erro_handler
        self.modulo = modulo

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        tipo = "LEXICO" if "Lexer" in str(type(recognizer).__name__) else "SINTATICO"
        if tipo == "LEXICO":
            # Format: ERRO LÉXICO [Linha 5, Coluna 12]: Símbolo 'x' inválido.
            mensagem = f"ERRO LÉXICO [Linha {line}, Coluna {column}]: Símbolo inválido. Detalhe: {msg}"
            # Extract token if possible
            if "token recognition error at: " in msg:
                bad_char = msg.split("token recognition error at: ")[1].strip("'")
                mensagem = f"ERRO LÉXICO [Linha {line}, Coluna {column}]: Símbolo '{bad_char}' inválido."
        else:
            mensagem = f"ERRO SINTÁTICO [Linha {line}, Coluna {column}]: {msg.replace('mismatched input', 'Encontrado').replace('expecting', 'Esperado')}"
            
        self.erro_handler.registrar_erro(self.modulo, line, column, mensagem, tipo_erro=tipo)
