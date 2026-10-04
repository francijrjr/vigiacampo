import { criarAcoesBoletins } from "./boletins-acoes.js";
import { criarAcoesRegistros } from "./registros-acoes.js";
import { criarAcoesNavegacao } from "./navegacao-acoes.js";
import { criarAcoesSessao } from "./sessao-acoes.js";
import { criarAcoesVisitas } from "./visitas-acoes.js";
import { criarAcoesEquipe } from "./equipe-acoes.js";
import { criarAcoesRascunhos } from "./rascunhos-acoes.js";

export function criarAcoes(contexto) {
  const acoes = {
    ...criarAcoesBoletins(contexto),
    ...criarAcoesRegistros(contexto),
    ...criarAcoesNavegacao(contexto),
    ...criarAcoesSessao(contexto),
    ...criarAcoesVisitas(contexto),
    ...criarAcoesEquipe(contexto),
    ...criarAcoesRascunhos(contexto),
  };
  return async (nome, valor) => {
    const executar = acoes[nome];
    if (executar) await executar(valor, nome);
  };
}
