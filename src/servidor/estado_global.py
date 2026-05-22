from nucleo import persistencia
from nucleo.gerenciador_salas import GerenciadorSalas

persistencia.InicializarBanco()
GerenciadorVersus = GerenciadorSalas()
GerenciadorVersus.RestaurarSalasAtivas()
