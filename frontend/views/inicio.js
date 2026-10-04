import { icone } from "./icones.js";

import { painel, botao, titulo } from "./componentes.js";
import { filaPainel } from "./layout.js";
import { tabelaRegistros } from "./registros.js";

export function inicio({ resumo, recentes, usuario, pendentes }) {
  const nome = usuario.full_name.split(" ")[0];
  return (
    titulo(
      `Olá, ${nome}.`,
      "Vamos acompanhar o trabalho em campo?",
      botao("+ Novo registro", "novo-registro", "primary"),
    ) +
    filaPainel(pendentes) +
    `<section class="work-card"><div class="work-copy"><span class="eyebrow">${icone("map-pin")} Seu dia em campo</span><h2>Tudo pronto para<br>a próxima visita.</h2><p>Registre os imóveis visitados e acompanhe o que ainda precisa ser enviado.</p><div class="work-actions">${botao("Nova atividade", "novo-registro", "primary")}<a class="text-button" href="#registros">Consultar registros ${icone("arrow-right")}</a></div></div><aside class="work-summary"><span class="work-summary-icon">${icone("clipboard-check")}</span><span class="eyebrow">Para acompanhar</span><div class="work-count"><strong>${resumo.total_rascunhos}</strong><span>${resumo.total_rascunhos === 1 ? "registro em rascunho" : "registros em rascunho"}</span></div><p>${resumo.total_rascunhos ? "Continue de onde parou e envie quando terminar." : "Tudo em dia. Comece uma nova atividade quando precisar."}</p></aside></section>` +
    `<div class="metrics">${[
      [
        "Registros no total",
        resumo.total_registros,
        "Histórico da sua área de acesso",
        "clipboard-list",
      ],
      [
        "Imóveis registrados",
        resumo.total_imoveis,
        "Visitas cadastradas",
        "house",
      ],
      [
        "Registros enviados",
        resumo.total_enviados,
        "Disponíveis para acompanhamento",
        "send",
      ],
      [
        "Em rascunho",
        resumo.total_rascunhos,
        "Atividades para continuar",
        "file-pen-line",
      ],
    ]
      .map(
        ([label, valor, ajuda, nomeIcone]) =>
          `<article class="metric"><div class="metric-header">${label}<span class="metric-icon">${icone(nomeIcone)}</span></div><strong>${valor}</strong><small>${ajuda}</small></article>`,
      )
      .join("")}</div>` +
    painel(
      "Registros recentes",
      tabelaRegistros(recentes),
      `<a class="text-button" href="#registros">Ver todos ${icone("arrow-right")}</a>`,
    )
  );
}
