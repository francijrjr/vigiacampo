import { escapar as e } from "./formularios.js";
import { icone } from "./icones.js";
import { botao, painel, titulo } from "./componentes.js";
import { filaPainel } from "./layout.js";
import { tabelaRegistros } from "./registros.js";

/**
 * Catálogo extensível de módulos da plataforma VigiaCampo.
 * Para adicionar um novo módulo no futuro, basta incluir um novo objeto nesta lista,
 * definindo suas rotas, perfis permitidos, permissões e metadados visuais.
 */
export const CATALOGO_MODULOS = [
  {
    id: "reconhecimento",
    rota: "reconhecimento",
    rotasAssociadas: ["reconhecimento"],
    titulo: "Reconhecimento Geográfico",
    subtitulo: "Cadastro territorial permanente",
    selo: "Módulo Territorial · Base Permanente",
    icone: "map-pin",
    tema: "territorial",
    descricao:
      "Estruture e mantenha o cadastro territorial permanente do município: localidades, zonas, quarteirões georreferenciados no mapa e quantitativo de imóveis por categoria.",
    perfis: ["SUPERVISOR", "AGENTE"],
    permissoes: {
      SUPERVISOR: [
        "Cadastrar, editar e excluir localidades e quarteirões permanentes",
        "Delimitar polígonos de quadras no mapa e validar estrutura de imóveis",
        "Supervisionar a base territorial compartilhada com toda a equipe",
      ],
      AGENTE: [
        "Consultar localidades e quarteirões permanentes da sua área de atuação",
        "Cadastrar novos quarteirões reconhecidos e atualizar contagem de imóveis",
        "Desenhar e conferir contornos de quarteirão no mapa interativo",
      ],
    },
    metricas: (resumoTerritorio = {}) => [
      [resumoTerritorio.total_localidades ?? 0, "localidades"],
      [resumoTerritorio.total_quarteiroes ?? 0, "quarteirões permanentes"],
      [resumoTerritorio.total_imoveis ?? 0, "imóveis catalogados"],
    ],
    textoBotao: "Abrir Reconhecimento Geográfico",
  },
  {
    id: "vetorial",
    rota: "vetorial",
    rotasAssociadas: [
      "vetorial",
      "registros",
      "registro",
      "visita",
      "boletim",
      "antivetorial",
      "equipe",
      "relatorios",
    ],
    titulo: "Controle Vetorial",
    subtitulo: "Registros diários, visitas, boletins e antivetorial",
    selo: "Módulo Operacional · PNCD",
    icone: "clipboard-check",
    tema: "vetorial",
    descricao:
      "Execute e acompanhe as ações de combate a endemias: registros diários de campo, visitas domiciliares, Boletim de Reconhecimento PCFAD, Serviço Antivetorial (PVE), equipe e relatórios.",
    perfis: ["SUPERVISOR", "AGENTE"],
    permissoes: {
      SUPERVISOR: [
        "Acesso completo a registros diários, visitas, boletins e fichas antivetoriais",
        "Administração da equipe de agentes (cadastro, edição e ativação)",
        "Relatórios estatísticos por período e exportação de PDFs oficiais",
      ],
      AGENTE: [
        "Criação e envio de registros diários e rascunhos offline no aparelho",
        "Registro de visitas, inspeções, fotos, boletins e fichas antivetoriais",
        "Emissão de PDF do Boletim de Reconhecimento e do Serviço Antivetorial",
      ],
    },
    metricas: (resumoVetorial = {}) => [
      [resumoVetorial.total_registros ?? 0, "registros"],
      [resumoVetorial.total_imoveis ?? 0, "imóveis visitados"],
      [resumoVetorial.total_rascunhos ?? 0, "em rascunho"],
    ],
    textoBotao: "Abrir Controle Vetorial",
  },
];

export function modulosDoUsuario(usuario) {
  if (!usuario) return [];
  return CATALOGO_MODULOS.filter((modulo) =>
    modulo.perfis.includes(usuario.role),
  );
}

export function identificarModulo(rota) {
  return (
    CATALOGO_MODULOS.find((modulo) => modulo.rotasAssociadas.includes(rota)) ||
    null
  );
}

export function barraRetornoModulos(moduloAtual, usuario) {
  const papel = usuario
    ? usuario.role === "SUPERVISOR"
      ? "Supervisor"
      : "Agente de campo"
    : null;
  return `<div class="module-context-bar"><a class="module-back-btn" href="#modulos" aria-label="Voltar para a tela de módulos">${icone("arrow-left")}<span>Tela de módulos</span></a><div class="module-context-badges"><span class="module-active-pill">${icone(moduloAtual.icone)}<span>Módulo: ${e(moduloAtual.titulo)}</span></span>${papel ? `<span class="module-role-pill">${e(papel)}</span>` : ""}</div></div>`;
}

function cartaoModulo(modulo, usuario, dadosResumo) {
  const papelNome =
    usuario.role === "SUPERVISOR" ? "Supervisor" : "Agente de campo";
  const permissoes = modulo.permissoes[usuario.role] || [];
  const indicadores = modulo.metricas(dadosResumo);
  return `<article class="module-card module-${e(modulo.tema)}" data-module-card="${e(modulo.id)}">
    <div class="module-card-top">
      <span class="module-badge">${icone(modulo.icone)}<span>${e(modulo.selo)}</span></span>
      <span class="module-icon-box" aria-hidden="true">${icone(modulo.icone)}</span>
    </div>
    <div class="module-card-header">
      <h3>${e(modulo.titulo)}</h3>
      <p class="module-subtitle">${e(modulo.subtitulo)}</p>
    </div>
    <p class="module-description">${e(modulo.descricao)}</p>
    <div class="module-stats" aria-label="Indicadores do módulo ${e(modulo.titulo)}">
      ${indicadores
        .map(
          ([valor, rotulo]) =>
            `<div class="module-stat"><strong>${e(valor)}</strong><span>${e(rotulo)}</span></div>`,
        )
        .join("")}
    </div>
    <div class="module-permissions">
      <div class="module-permissions-title">
        <span>Permissões do seu perfil</span>
        <strong>${e(papelNome)}</strong>
      </div>
      <ul>
        ${permissoes
          .map((item) => `<li>${icone("circle-check")}<span>${e(item)}</span></li>`)
          .join("")}
      </ul>
    </div>
    <div class="module-card-footer">
      <a class="primary module-open-btn" href="#${e(modulo.rota)}">
        <span>${e(modulo.textoBotao)}</span>
        ${icone("arrow-right")}
      </a>
    </div>
  </article>`;
}

export function telaModulos({
  usuario,
  resumoVetorial,
  resumoTerritorio,
  recentes,
  pendentes,
}) {
  const nome = usuario.full_name.split(" ")[0];
  const papel =
    usuario.role === "SUPERVISOR" ? "Supervisor" : "Agente de campo";
  const modulos = modulosDoUsuario(usuario);
  const resumosPorId = {
    reconhecimento: resumoTerritorio,
    vetorial: resumoVetorial,
  };

  return (
    titulo(
      `Olá, ${nome}.`,
      "Selecione o módulo de trabalho disponível para o seu perfil de acesso.",
      botao("+ Novo registro", "novo-registro", "primary"),
    ) +
    filaPainel(pendentes) +
    `<section class="modules-Access-banner" aria-label="Identificação de acesso">
      <div class="modules-access-info">
        <span class="eyebrow">${icone("users")} Ambiente modular · VigiaCampo</span>
        <h2>Módulos habilitados para a sua conta</h2>
        <p>Você está conectado como <strong>${e(papel)}</strong> (${e(usuario.municipio || "PNCD")}). Novos módulos adicionados ao sistema aparecerão automaticamente nesta grade conforme suas permissões.</p>
      </div>
      <div class="modules-access-summary">
        <span class="modules-count-badge"><strong>${modulos.length}</strong><span>${modulos.length === 1 ? "módulo liberado" : "módulos liberados"}</span></span>
      </div>
    </section>` +
    `<section class="modules-section" aria-label="Módulos disponíveis">
      <div class="modules-grid">
        ${modulos
          .map((modulo) =>
            cartaoModulo(modulo, usuario, resumosPorId[modulo.id]),
          )
          .join("")}
      </div>
    </section>` +
    painel(
      "Registros recentes do Controle Vetorial",
      tabelaRegistros(recentes),
      `<a class="text-button" href="#vetorial">Ir ao Controle Vetorial ${icone("arrow-right")}</a>`,
    )
  );
}
