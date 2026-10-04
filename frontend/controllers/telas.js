import { api, guardarSessao, usuarioAtual } from "../models/api.js";
import { estado } from "../models/estado.js";
import { fila } from "../models/rascunhos.js";
import {
  consultarPainel,
  consultarRegistros,
  consultarRegistro,
  consultarBoletins,
  consultarEquipe,
  consultarRelatorios,
  podeEditarRegistro,
} from "../models/consultas.js";
import * as layoutView from "../views/layout.js";
import * as registrosView from "../views/registros.js";
import { inicio as inicioView } from "../views/inicio.js";
import { visita as visitaView } from "../views/visita.js";
import { equipe as equipeView } from "../views/equipe.js";
import { relatorios as relatoriosView } from "../views/relatorios.js";
import { conta as contaView } from "../views/conta.js";

// Controllers consultam modelos, atualizam o estado e entregam dados às views.
export function criarTelas(render) {
  function login() {
    ++estado.renderAtual;
    document.querySelector("#app").innerHTML = layoutView.login();
    document.querySelector("#login").onsubmit = async (evento) => {
      evento.preventDefault();
      const formulario = evento.currentTarget;
      const botao = formulario.querySelector("button");
      botao.disabled = true;
      try {
        const sessao = await api("/auth/login", {
          method: "POST",
          body: Object.fromEntries(new FormData(formulario)),
        });
        guardarSessao(sessao);
        await render();
      } catch (erro) {
        formulario.querySelector(".form-error").textContent = erro.message;
      } finally {
        botao.disabled = false;
      }
    };
  }

  function estrutura(rota) {
    document.querySelector("#app").innerHTML = layoutView.estrutura(
      rota,
      usuarioAtual(),
      navigator.onLine,
    );
  }

  async function inicio() {
    const [resumo, recentes] = await Promise.all([
      consultarPainel(),
      consultarRegistros({}, 0, 5),
    ]);
    return inicioView({
      resumo,
      recentes,
      usuario: usuarioAtual(),
      pendentes: fila(),
    });
  }

  async function registros() {
    const { filtros, pagina } = estado;
    const dados = await consultarRegistros(filtros, pagina);
    return registrosView.registros({
      dados,
      filtros,
      pagina,
      pendentes: fila(),
    });
  }

  async function detalheRegistro(id, versao) {
    const [registro, boletins] = await Promise.all([
      consultarRegistro(id),
      consultarBoletins(id),
    ]);
    if (versao !== estado.renderAtual) return "";
    estado.registroAberto = registro;
    return registrosView.detalheRegistro({
      registro,
      boletins,
      editar: podeEditarRegistro(registro, usuarioAtual()),
      supervisor: usuarioAtual().role === "SUPERVISOR",
    });
  }

  async function visita(registroId, imovelId, versao) {
    const registro = await consultarRegistro(registroId);
    if (versao !== estado.renderAtual) return "";
    const imovel = registro.imoveis.find(
      (item) => item.id === Number(imovelId),
    );
    if (!imovel) throw new Error("Imóvel não encontrado.");
    estado.registroAberto = registro;
    estado.imovelAberto = imovel;
    return visitaView({
      registro,
      imovel,
      editar: podeEditarRegistro(registro, usuarioAtual()),
      abaVisita: estado.abaVisita,
    });
  }

  async function equipe(versao) {
    const pagina = estado.pagina;
    const dados = await consultarEquipe(pagina);
    if (versao !== estado.renderAtual) return "";
    estado.equipeAtual = dados;
    return equipeView({ dados, pagina });
  }

  async function relatorios() {
    const filtros = estado.filtros;
    return relatoriosView({
      dados: await consultarRelatorios(filtros),
      filtros,
    });
  }

  return {
    login,
    estrutura,
    inicio,
    registros,
    detalheRegistro,
    visita,
    equipe,
    relatorios,
    conta: () => contaView(usuarioAtual()),
    filaPainel: () => layoutView.filaPainel(fila()),
  };
}
