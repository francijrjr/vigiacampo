import { escapar as e } from "./formularios.js";
import { icone } from "./icones.js";

import { painel, botao, titulo } from "./componentes.js";

export function conta(usuario) {
  return (
    titulo("Minha conta", "Suas informações de acesso.") +
    painel(
      "Perfil",
      `<div class="detail-body"><h2>${e(usuario.full_name)}</h2><p>Usuário: ${e(usuario.username)}<br>E-mail: ${e(usuario.email || "Não informado")}<br>Município: ${e(usuario.municipio || "Não informado")}</p><div class="actions">${botao("Alterar senha", "senha", "primary")}${botao("Sair da conta", "sair")}</div></div>`,
    ) +
    painel(
      "Documentação da API",
      `<div class="detail-body"><p>Consulte as rotas, os campos e os exemplos de uso.</p><a class="primary" href="/docs" target="_blank" rel="noopener">Abrir Swagger ${icone("arrow-up-right")}</a></div>`,
    )
  );
}
