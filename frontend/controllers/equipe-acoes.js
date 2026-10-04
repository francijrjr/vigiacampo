import { api, usuarioAtual } from "../models/api.js";

import { estado } from "../models/estado.js";

export function criarAcoesEquipe({ render, modal }) {
  async function executarNovoAgente(valor, nome) {
    const campos = [
      ...(nome === "novo-agente"
        ? [
            ["username", "Nome de usuário", "text"],
            ["password", "Senha inicial", "password"],
          ]
        : []),
      ["full_name", "Nome completo", "text"],
      ["email", "E-mail", "email"],
      ["municipio", "Município", "text"],
    ];
    return modal(
      nome === "novo-agente" ? "Adicionar agente" : "Editar agente",
      campos,
      estado.equipeAtual.find((usuario) => usuario.id === Number(valor)) || {
        municipio: usuarioAtual().municipio,
      },
      (dados) =>
        api(`/users/${valor || ""}`, {
          method: valor ? "PATCH" : "POST",
          body: dados,
        }),
    );
  }

  async function executarAcessoAgente(valor) {
    const usuario = estado.equipeAtual.find(
      (usuario) => usuario.id === Number(valor),
    );
    if (
      !confirm(
        `${usuario.is_active ? "Desativar" : "Ativar"} o acesso de ${usuario.full_name}?`,
      )
    )
      return;
    await api(`/users/${usuario.id}`, {
      method: "PATCH",
      body: { is_active: !usuario.is_active },
    });

    await render();
  }

  return {
    "novo-agente": executarNovoAgente,
    "editar-agente": executarNovoAgente,
    "acesso-agente": executarAcessoAgente,
  };
}
