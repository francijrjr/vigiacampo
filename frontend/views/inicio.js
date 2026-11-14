import { icone } from "./icones.js";

import { painel, botao, titulo } from "./componentes.js";
import { filaPainel } from "./layout.js";
import { CATALOGO_MODULOS, barraRetornoModulos } from "./modulos.js";
import { tabelaRegistros } from "./registros.js";

export function inicio({ resumo, recentes, usuario, pendentes }) {
  const nome = usuario.full_name.split(" ")[0];
  const moduloInfo = CATALOGO_MODULOS.find((m) => m.id === "vetorial");
  return (
    barraRetornoModulos(moduloInfo, usuario) +
    titulo(
      `Olá, ${nome}.`,
      "Módulo de Controle Vetorial · escolha a modalidade de campo ou acompanhe os registros.",
      botao("+ Novo registro", "novo-registro", "primary"),
    ) +
    filaPainel(pendentes) +
    `<section class="work-card"><div class="work-copy"><span class="eyebrow">${icone("map-pin")} Seu dia em campo</span><h2>Tudo pronto para<br>a próxima visita.</h2><p>Escolha abaixo uma das duas opções de atuação para registrar visitas, boletins de reconhecimento ou fichas do serviço antivetorial.</p><div class="work-actions">${botao("Nova atividade", "novo-registro", "primary")}<a class="text-button" href="#registros">Consultar registros ${icone("arrow-right")}</a></div></div><aside class="work-summary"><span class="work-summary-icon">${icone("clipboard-check")}</span><span class="eyebrow">Para acompanhar</span><div class="work-count"><strong>${resumo.total_rascunhos}</strong><span>${resumo.total_rascunhos === 1 ? "registro em rascunho" : "registros em rascunho"}</span></div><p>${resumo.total_rascunhos ? "Continue de onde parou e envie quando terminar." : "Tudo em dia. Comece uma nova atividade quando precisar."}</p></aside></section>` +
    `<section class="choice-section" aria-label="Opções de atuação em campo"><div class="choice-header"><div><span class="eyebrow">Duas opções de escolha</span><h2>Como você deseja registrar hoje?</h2></div><p>Selecione a modalidade ideal para a atividade de campo que será executada.</p></div><div class="choice-grid">` +
    `<article class="choice-card choice-primary"><div class="choice-top"><span class="choice-tag">${icone("map-pin")} Opção 1 · Rotina e Reconhecimento</span><span class="choice-icon">${icone("house")}</span></div><h3>Visitas e Boletim de Reconhecimento</h3><p>Cadastre quarteirões com mapa interativo, registre visitas por imóvel (inspeções, coletas, espécimes e tratamentos) e emita o Boletim de Reconhecimento.</p><ul class="choice-features"><li>${icone("circle-check")}<span>Quarteirões com contorno no mapa e imóveis por rua</span></li><li>${icone("circle-check")}<span>Inspeções, amostras, fotos e fechamento automático</span></li><li>${icone("circle-check")}<span>Boletim de Reconhecimento PCFAD em PDF</span></li></ul><div class="choice-actions">${botao("+ Iniciar visita e boletim", "novo-registro", "primary")}<a class="text-button" href="#registros">Ver registros ${icone("arrow-right")}</a></div></article>` +
    `<article class="choice-card choice-accent"><div class="choice-top"><span class="choice-tag">${icone("clipboard-list")} Opção 2 · Serviço Especializado</span><span class="choice-icon">${icone("file-pen-line")}</span></div><h3>Serviço Antivetorial (PVE)</h3><p>Preencha diretamente a planilha oficial do serviço antivetorial com até 20 linhas de campo, contagem de depósitos A1 a E, foco e tratamento aplicado.</p><ul class="choice-features"><li>${icone("circle-check")}<span>Ficha direta com 20 linhas numeradas de campo</span></li><li>${icone("circle-check")}<span>Contagem de depósitos A1, A2, B, C, D1, D2 e E</span></li><li>${icone("circle-check")}<span>PDF oficial do Serviço Antivetorial pronto para impressão</span></li></ul><div class="choice-actions">${botao("+ Iniciar serviço antivetorial", "novo-antivetorial", "secondary")}<a class="text-button" href="#registros">Ver fichas ${icone("arrow-right")}</a></div></article>` +
    `</div></section>` +
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

