import { api, ErroConexao, usuarioAtual } from "../models/api.js";
import { telaBoletim } from "../views/boletim.js";
import { icone } from "../views/icones.js";
import { estado } from "../models/estado.js";
import { empty, botao } from "../views/componentes.js";
import { criarInterface } from "../views/interface.js";
import { criarTelas } from "./telas.js";
import { criarAcoes } from "./acoes.js";

const { dialog, modal, avisar } = criarInterface(render);
const {
  login,
  estrutura,
  inicio,
  registros,
  detalheRegistro,
  visita,
  equipe,
  relatorios,
  conta,
  filaPainel,
} = criarTelas(render);
const acao = criarAcoes({ render, login, dialog, modal, avisar });

async function render() {
  const numero = ++estado.renderAtual;
  estado.urlsFotos.forEach(URL.revokeObjectURL);
  estado.urlsFotos = [];
  if (!usuarioAtual()) return login();
  const [rota = "inicio", id, imovelId] = (
    location.hash.slice(1) || "inicio"
  ).split("/");
  estrutura(
    ["registro", "visita", "boletim"].includes(rota) ? "registros" : rota,
  );
  try {
    let html;
    if (rota === "inicio") html = await inicio();
    else if (rota === "registros") html = await registros();
    else if (rota === "registro") html = await detalheRegistro(id, numero);
    else if (rota === "visita") html = await visita(id, imovelId, numero);
    else if (rota === "boletim") {
      const dados = await api(`/registros/${id}/boletins/${imovelId}`);
      if (numero !== estado.renderAtual) return;
      estado.boletimAberto = dados;
      html = telaBoletim(dados);
    } else if (rota === "equipe" && usuarioAtual().role === "SUPERVISOR")
      html = await equipe(numero);
    else if (rota === "relatorios" && usuarioAtual().role === "SUPERVISOR")
      html = await relatorios();
    else if (rota === "conta") html = conta();
    else html = empty("Página não encontrada", "Use o menu para continuar.");
    if (numero !== estado.renderAtual) return;
    document.querySelector("#content").innerHTML = html;
    const form = document.querySelector("#filters");
    if (form)
      form.onsubmit = (ev) => {
        ev.preventDefault();
        estado.filtros = Object.fromEntries(
          [...new FormData(form)].filter(([, v]) => v),
        );
        estado.pagina = 0;
        render();
      };
    for (const img of document.querySelectorAll("[data-foto]")) {
      api(`/fotos/${img.dataset.foto}/arquivo`, { arquivo: true })
        .then((blob) => {
          if (numero !== estado.renderAtual) return;
          const url = URL.createObjectURL(blob);
          estado.urlsFotos.push(url);
          img.src = url;
        })
        .catch(() => {
          img.alt = "Não foi possível carregar esta foto";
        });
    }
  } catch (erro) {
    if (numero !== estado.renderAtual) return;
    if (erro instanceof ErroConexao) {
      const indicador = document.querySelector(".connection");
      indicador.classList.add("offline");
      indicador.innerHTML = icone("wifi-off") + "Servidor indisponível";
    }
    document.querySelector("#content").innerHTML =
      filaPainel() +
      empty(
        "Não foi possível carregar",
        erro.message,
        botao("Tentar novamente", "recarregar", "primary"),
      ) +
      (erro instanceof ErroConexao
        ? botao("+ Criar registro neste aparelho", "novo-registro")
        : "");
  }
}

document.addEventListener("click", async (evento) => {
  const linhaRegistro = evento.target.closest("[data-registro-linha]");
  if (linhaRegistro && !evento.defaultPrevented && evento.button === 0
    && !evento.ctrlKey && !evento.metaKey && !evento.shiftKey && !evento.altKey
    && !evento.target.closest("a, button, input, select, textarea, label, [contenteditable], [data-action]")
    && !window.getSelection()?.toString()) {
    linhaRegistro.querySelector("[data-abrir-registro]")?.click();
    return;
  }
  const button = evento.target.closest("[data-action]");
  if (!button) return;
  evento.preventDefault();
  if (button.disabled) return;
  button.disabled = true;
  try {
    const [nome, valor] = button.dataset.action.split(":");
    await acao(nome, valor);
  } catch (erro) {
    avisar(erro.message);
  } finally {
    button.disabled = false;
  }
});
window.addEventListener("hashchange", () => {
  estado.pagina = 0;
  render();
});
window.addEventListener("online", () => {
  avisar("Conexão restabelecida. Você pode enviar seus rascunhos.");
  render();
});
window.addEventListener("offline", () => render());
window.addEventListener("sessao-encerrada", () => {
  dialog.close();
  login();
});
if ("serviceWorker" in navigator)
  navigator.serviceWorker.register("/sw.js").catch(() => {});
render();
