import { formularioFoto } from "../views/fotos.js";

import { api } from "../models/api.js";

import { camposImovel, colecoes } from "../views/formularios.js";
import { estado } from "../models/estado.js";

export function criarAcoesVisitas({ render, dialog, modal }) {
  function camposDoImovel() {
    return [
      ...camposImovel,
      [
        "quarteirao_id",
        "Quarteirão",
        "select",
        {
          "": "Sem quarteirão",
          ...Object.fromEntries(
            estado.registroAberto.quarteiroes.map((quarteirao) => [
              quarteirao.id,
              `${quarteirao.numero} · ${quarteirao.logradouro || ""}`,
            ]),
          ),
        },
      ],
    ];
  }
  const caminhoVisita = () =>
    `/registros/${estado.registroAberto.id}/imoveis/${estado.imovelAberto.id}`;
  async function executarNovoImovel(valor, nome) {
    const registro = estado.registroAberto;
    return modal(
      nome === "novo-imovel" ? "Adicionar imóvel" : "Editar imóvel",
      camposDoImovel(),
      nome === "editar-imovel" ? estado.imovelAberto : {},
      (dados) => {
        dados.quarteirao_id = dados.quarteirao_id
          ? Number(dados.quarteirao_id)
          : null;
        return api(
          `/registros/${registro.id}/imoveis${nome === "editar-imovel" ? `/${estado.imovelAberto.id}` : ""}`,
          {
            method: nome === "editar-imovel" ? "PATCH" : "POST",
            body: dados,
          },
        );
      },
    );
  }

  async function executarExcluirImovel() {
    const registro = estado.registroAberto;

    if (!confirm("Excluir o imóvel, os dados da visita e as fotos vinculadas?"))
      return;
    await api(caminhoVisita(), { method: "DELETE" });
    location.hash = `registro/${registro.id}`;
    return;
  }

  async function executarAba(valor) {
    estado.abaVisita = valor;
    return render();
  }

  async function executarNovoItem(valor) {
    const definicao = colecoes[estado.abaVisita];
    return modal(
      definicao.titulo,
      definicao.campos,
      estado.imovelAberto[estado.abaVisita.replaceAll("-", "_")].find(
        (i) => i.id === Number(valor),
      ),
      (dados) =>
        api(
          `${caminhoVisita()}/${estado.abaVisita}${valor ? `/${valor}` : ""}`,
          { method: valor ? "PUT" : "POST", body: dados },
        ),
    );
  }

  async function executarExcluirItem(valor) {
    if (!confirm("Excluir este item da visita?")) return;
    await api(`${caminhoVisita()}/${estado.abaVisita}/${valor}`, {
      method: "DELETE",
    });

    await render();
  }

  async function executarNovaFoto() {
    document.querySelector("#dialog-title").textContent = "Adicionar foto";
    document.querySelector("#dialog-body").innerHTML = formularioFoto();
    dialog.showModal();
    dialog.querySelector("form").onsubmit = async (ev) => {
      ev.preventDefault();
      const form = ev.currentTarget,
        submit = form.querySelector("button");
      submit.disabled = true;
      try {
        await api(`/fotos/imovel/${estado.imovelAberto.id}`, {
          method: "POST",
          body: new FormData(form),
        });
        dialog.close();
        await render();
      } catch (erro) {
        form.querySelector(".form-error").textContent = erro.message;
      } finally {
        submit.disabled = false;
      }
    };
    return;
  }

  async function executarExcluirFoto(valor) {
    if (!confirm("Excluir esta foto?")) return;
    await api(`/fotos/${valor}`, { method: "DELETE" });

    await render();
  }

  return {
    "novo-imovel": executarNovoImovel,
    "editar-imovel": executarNovoImovel,
    "excluir-imovel": executarExcluirImovel,
    aba: executarAba,
    "novo-item": executarNovoItem,
    "editar-item": executarNovoItem,
    "excluir-item": executarExcluirItem,
    "nova-foto": executarNovaFoto,
    "excluir-foto": executarExcluirFoto,
  };
}
