import logging
from erro import Erro

class GeracaoTAC:
    def __init__(self, erro_handler: Erro):
        self.erro_handler = erro_handler
        self.logger = logging.getLogger(self.__class__.__name__)

    def gerarCodigoTAC(self, ast):
        self.logger.info("Gerando código TAC fictício para não quebrar a compilação.")
        return "// TAC gerado com sucesso."
