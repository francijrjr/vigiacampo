let sessao = JSON.parse(sessionStorage.getItem("alberio.sessao") || "null");
let renovacao;

export class ErroConexao extends Error {
  constructor() {
    super(
      "Não foi possível conectar ao servidor. Você pode salvar um rascunho neste aparelho e tentar enviar depois.",
    );
  }
}

export const usuarioAtual = () => sessao?.user;

export function guardarSessao(dados) {
  sessao = dados;
  if (dados) sessionStorage.setItem("alberio.sessao", JSON.stringify(dados));
  else sessionStorage.removeItem("alberio.sessao");
}

export async function api(
  caminho,
  { method = "GET", body, arquivo = false, repetir = true } = {},
) {
  const headers = {};
  if (sessao) headers.Authorization = `Bearer ${sessao.access_token}`;
  if (body && !(body instanceof FormData))
    headers["Content-Type"] = "application/json";
  let resposta;
  try {
    resposta = await fetch(`/api/v1${caminho}`, {
      method,
      headers,
      body:
        body instanceof FormData
          ? body
          : body
            ? JSON.stringify(body)
            : undefined,
    });
  } catch {
    throw new ErroConexao();
  }
  if (
    resposta.status === 401 &&
    sessao?.refresh_token &&
    repetir &&
    caminho !== "/auth/refresh"
  ) {
    renovacao ||= api("/auth/refresh", {
      method: "POST",
      body: { refresh_token: sessao.refresh_token },
      repetir: false,
    })
      .then(guardarSessao)
      .finally(() => {
        renovacao = null;
      });
    try {
      await renovacao;
      return await api(caminho, { method, body, arquivo, repetir: false });
    } catch (erro) {
      if (!(erro instanceof ErroConexao)) {
        guardarSessao(null);
        window.dispatchEvent(new Event("sessao-encerrada"));
      }
      throw erro;
    }
  }
  if (!resposta.ok) {
    const dados = await resposta.json().catch(() => ({}));
    const mensagem = Array.isArray(dados.detail)
      ? dados.detail
          .map((e) => `${e.loc.slice(1).join(" › ")}: ${e.msg}`)
          .join("\n")
      : dados.detail;
    throw new Error(
      mensagem || `Não foi possível concluir a operação (${resposta.status}).`,
    );
  }
  if (resposta.status === 204) return null;
  return arquivo ? resposta.blob() : resposta.json();
}
