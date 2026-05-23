from nucleo import persistencia
from nucleo.bots_ranqueados import InicializarEstadoBotsRanqueados
from nucleo.gerenciador_salas import GerenciadorSalas

persistencia.InicializarBanco()
InicializarEstadoBotsRanqueados()
GerenciadorVersus = GerenciadorSalas()
GerenciadorVersus.RestaurarSalasAtivas()
