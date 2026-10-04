import { escapar as e } from "./formularios.js";
import { icone } from "./icones.js";

import { empty, painel, botao, titulo } from "./componentes.js";

export function equipe({ dados: equipeAtual, pagina }) {
  return (
    titulo(
      "Minha equipe",
      "Pessoas que levam o cuidado para as ruas.",
      botao("+ Adicionar agente", "novo-agente", "primary"),
    ) +
    painel(
      "Agentes de campo",
      equipeAtual.length
        ? `<div class="table-wrap"><table><thead><tr><th>Agente</th><th>Usuário</th><th>Município</th><th>Acesso</th><th></th></tr></thead><tbody>${equipeAtual.map((usuario) => `<tr><td><strong>${e(usuario.full_name)}</strong><small>${e(usuario.email)}</small></td><td>${e(usuario.username)}</td><td>${e(usuario.municipio)}</td><td><span class="badge ${usuario.is_active ? "SYNCED" : ""}">${usuario.is_active ? "Ativo" : "Desativado"}</span></td><td><div class="actions">${botao("Editar", `editar-agente:${usuario.id}`)}${botao(usuario.is_active ? "Desativar" : "Ativar", `acesso-agente:${usuario.id}`, usuario.is_active ? "danger" : "secondary")}</div></td></tr>`).join("")}</tbody></table></div>`
        : empty(
            "Sua equipe começa aqui",
            "Cadastre um agente para liberar o acesso ao sistema.",
          ),
    ) +
    `<div class="pager"><button class="secondary" data-action="anterior" ${pagina === 0 ? "disabled" : ""}>${icone("arrow-left")} Anterior</button><span>Página ${pagina + 1}</span><button class="secondary" data-action="proxima" ${equipeAtual.length < 100 ? "disabled" : ""}>Próxima ${icone("arrow-right")}</button></div>`
  );
}
