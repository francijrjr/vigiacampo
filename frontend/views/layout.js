import { escapar as e } from "./formularios.js";
import { icone } from "./icones.js";

import { botao } from "./componentes.js";

export function login() {
  return `<div class="login"><section class="login-story"><div class="brand"><span class="brand-mark">V</span>VigiaCampo</div><div><h1>O cuidado com a cidade começa <em>em campo.</em></h1><p>Um lugar para organizar visitas, acompanhar sua equipe e registrar cada ação contra a dengue.</p></div><div class="eyebrow">Vigilância em saúde · PNCD</div></section><div class="login-form"><section><span class="eyebrow">Seu espaço de trabalho</span><h2>Bom ter você por aqui.</h2><p>Entre na sua conta para acompanhar as atividades.</p><form id="login"><label>Usuário<input name="username" autocomplete="username" required placeholder="Seu nome de usuário"></label><label>Senha<input name="password" type="password" autocomplete="current-password" required placeholder="Sua senha"></label><p class="form-error" role="alert"></p><button class="primary">Entrar na minha conta ${icone("arrow-right")}</button></form><p class="login-footer">Precisa de acesso? Fale com o supervisor da sua equipe.</p><a class="subtle-link" href="/docs" target="_blank" rel="noopener">Documentação da API ${icone("arrow-up-right")}</a></section></div></div>`;
}

export function estrutura(rota, user, online) {
  const nomesMobile = { inicio: "Início", registros: "Registros", equipe: "Equipe", relatorios: "Relatórios", conta: "Conta" };
  const menu = [
    ["inicio", "layout-dashboard", "Visão geral"],
    ["registros", "clipboard-list", "Registros diários"],
    ...(user.role === "SUPERVISOR"
      ? [
          ["equipe", "users", "Minha equipe"],
          ["relatorios", "chart-no-axes-combined", "Relatórios"],
        ]
      : []),
    ["conta", "settings", "Minha conta"],
  ];
  return `<div class="layout"><aside class="sidebar"><div class="brand"><span class="brand-mark">V</span>VigiaCampo</div><div class="nav-label">ESPAÇO DE TRABALHO</div><nav aria-label="Navegação principal">${menu.map(([id, nomeIcone, nome]) => `<a class="nav-link ${rota === id ? "active" : ""}" href="#${id}" aria-label="${nome}" ${rota === id ? 'aria-current="page"' : ""}><span class="nav-icon" aria-hidden="true">${icone(nomeIcone)}</span><span class="nav-name">${nome}</span><span class="nav-name-mobile" aria-hidden="true">${nomesMobile[id]}</span></a>`).join("")}</nav><div class="sidebar-bottom"><div class="field-note"><strong>Pequenas ações.<br>Uma cidade mais protegida.</strong>Cada visita registrada ajuda a acompanhar o cuidado com a comunidade.</div><div class="profile"><span class="avatar">${e(
    user.full_name
      .split(" ")
      .map((s) => s[0])
      .slice(0, 2)
      .join(""),
  )}</span><div><p>${e(user.full_name)}</p><small>${user.role === "SUPERVISOR" ? "Supervisor" : "Agente de campo"}</small></div></div>${botao("Sair da conta", "sair", "text-button")}</div></aside><main class="main"><header class="topbar"><a class="mobile-brand" href="#inicio" aria-label="VigiaCampo — Início"><span class="brand-mark">V</span><span>VigiaCampo<small>${e(user.municipio || "Vigilância em saúde")}</small></span></a><span class="desktop-context">Vigilância em saúde <span class="muted"> / ${e(user.municipio || "PNCD")}</span></span><span class="connection ${online ? "" : "offline"}">${icone(online ? "wifi" : "wifi-off")}${online ? "Conectado" : "Sem conexão"}</span></header><div id="content" class="content"><p class="loading">Carregando informações…</p></div></main></div>`;
}

export function filaPainel(pendentes) {
  return pendentes.length
    ? `<div class="queue-note"><span><strong>${pendentes.length} registro(s) salvo(s) neste aparelho.</strong> Envie quando estiver conectado.</span>${botao("Revisar e enviar", "fila")}</div>`
    : "";
}
