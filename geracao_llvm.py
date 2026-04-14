import logging
from erro import Erro

class GeracaoLLVM:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)

    def gerarCodigoLLVM(self, ast):
        self.logger.info("Gerando código LLVM IR fictício.")
        return "; ModuleID = 'test.rb'\n"
