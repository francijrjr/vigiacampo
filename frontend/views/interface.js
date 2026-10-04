import { formulario, lerFormulario } from "./formularios.js";
import { icone } from "./icones.js";


export function criarInterface(render) {
  const dialog = document.querySelector("#dialog");
  let temporizador;
  let complementoAtual;
  function limparComplemento() {
    complementoAtual?.destruir();
    complementoAtual = undefined;
  }
  function fecharModal() {
    limparComplemento();
    dialog.close();
  }
  dialog.addEventListener("close", () => {
    // O evento de fechamento anterior pode chegar depois de uma reabertura.
    if (!dialog.open) limparComplemento();
  });
  function avisar(texto) {
    clearTimeout(temporizador);
    document.querySelector("#notice").textContent = texto;
    temporizador = setTimeout(
      () => (document.querySelector("#notice").textContent = ""),
      5000,
    );
  }

  function modal(titulo, campos, dados, salvar, textoBotao = "Salvar", montar) {
    limparComplemento();
    document.querySelector("#dialog-title").textContent = titulo;
    document.querySelector("#dialog-body").innerHTML = formulario(
      campos,
      dados,
      textoBotao,
    );
    dialog.showModal();
    const complemento = montar?.(dialog.querySelector("form"), dados || {});
    complementoAtual = complemento;
    dialog.querySelector("[data-cancel]").onclick = fecharModal;
    dialog.querySelector("form").onsubmit = async (evento) => {
      evento.preventDefault();
      const form = evento.currentTarget,
        submit = form.querySelector("[type=submit]");
      submit.disabled = true;
      try {
        await salvar({ ...lerFormulario(form, campos), ...complemento?.ler() });
        fecharModal();
        avisar("Dados salvos com sucesso.");
        await render();
      } catch (erro) {
        form.querySelector(".form-error").textContent = erro.message;
      } finally {
        submit.disabled = false;
      }
    };
  }
  document.querySelector("#close-dialog").onclick = fecharModal;
  document.querySelector("#close-dialog").innerHTML = icone("x");

  return { dialog, avisar, modal };
}
