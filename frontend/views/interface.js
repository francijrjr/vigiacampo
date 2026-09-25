import { formulario, lerFormulario } from "./formularios.js";
import { icone } from "./icones.js";

// O callback evita dependência circular com o coordenador de navegação.
export function criarInterface(render) {
  const dialog = document.querySelector("#dialog");
  let temporizador;
  function avisar(texto) {
    clearTimeout(temporizador);
    document.querySelector("#notice").textContent = texto;
    temporizador = setTimeout(
      () => (document.querySelector("#notice").textContent = ""),
      5000,
    );
  }
  function modal(titulo, campos, dados, salvar, textoBotao = "Salvar") {
    document.querySelector("#dialog-title").textContent = titulo;
    document.querySelector("#dialog-body").innerHTML = formulario(
      campos,
      dados,
      textoBotao,
    );
    dialog.showModal();
    dialog.querySelector("[data-cancel]").onclick = () => dialog.close();
    dialog.querySelector("form").onsubmit = async (evento) => {
      evento.preventDefault();
      const form = evento.currentTarget,
        submit = form.querySelector("[type=submit]");
      submit.disabled = true;
      try {
        await salvar(lerFormulario(form, campos));
        dialog.close();
        avisar("Dados salvos com sucesso.");
        await render();
      } catch (erro) {
        form.querySelector(".form-error").textContent = erro.message;
      } finally {
        submit.disabled = false;
      }
    };
  }
  document.querySelector("#close-dialog").onclick = () => dialog.close();
  document.querySelector("#close-dialog").innerHTML = icone("x");

  return { dialog, avisar, modal };
}
