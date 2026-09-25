import { api, guardarSessao } from "../models/api.js";

export function criarAcoesSessao({ login, modal }) {
  async function executarSair() {
    await api("/auth/logout", { method: "POST" });
    guardarSessao(null);
    return login();
  }

  async function executarSenha() {
    return modal(
      "Alterar senha",
      [
        ["current_password", "Senha atual", "password"],
        ["new_password", "Nova senha", "password"],
      ],
      {},
      async (dados) => {
        await api("/auth/change-password", { method: "POST", body: dados });
        guardarSessao(null);
      },
      "Alterar e entrar novamente",
    );
  }

  return {
    sair: executarSair,
    senha: executarSenha,
  };
}
