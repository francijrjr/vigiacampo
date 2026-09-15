export const escapar = valor => String(valor ?? '').replace(/[&<>"']/g, letra => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[letra]));
export const atividades = {LI:'Levantamento de índice', 'LI+T':'Levantamento e tratamento', PE:'Ponto estratégico', 'PE+T':'Ponto estratégico e tratamento', DF:'Delimitação de foco', PVE:'Pesquisa vetorial especial', Outros:'Outros'};
export const tipos = {RESIDENCIAL:'Residencial',COMERCIAL:'Comercial',TERRENO:'Terreno Baldio',PONTO_ESTRATEGICO:'Ponto Estratégico',OUTRO:'Outros'};
export const pendencias = {NENHUMA:'Sem pendência',FECHADO:'Fechado',RECUSA:'Recusa',OUTRA:'Outra'};
export const visitas = {NORMAL:'Normal',RECUSA:'Recusa',FECHADO:'Fechado',RECUPERADO:'Recuperado'};
export const situacoes = {DRAFT:'Rascunho',PENDING_SYNC:'Aguardando envio',SYNCED:'Enviado'};

export const camposRegistro = [
  ['municipio','Município','text'],['codigo_area','Área','text'],['ciclo','Ciclo','text'],
  ['data','Data','date'],['zona','Zona / bairro','optional'],['atividade','Atividade','select',atividades],
  ['observacoes','Observações','textarea']
];

export const camposQuarteirao = [['numero','Número do quarteirão','text'],['logradouro','Rua / logradouro','optional'],['sequencia','Sequência','number'],['lado','Lado','optional']];

export const camposImovel = [['logradouro','Rua ou logradouro','optional'],['numero','Número do imóvel','text'],['lado','Lado','optional'],['complemento','Complemento','optional'],['tipo','Tipo de imóvel','select',tipos],['hora_entrada','Hora da visita','time'],['tipo_visita','Situação da visita','select',visitas],['pendencia','Pendência','select',pendencias]];

export const colecoes = {
  inspecoes: {titulo:'Inspeções', campos:['a1','a2','b','c','d1','d2','e'].map(k => [k,`Depósitos ${k.toUpperCase()}`,'number'])},
  coletas: {titulo:'Coletas', campos:[['numero_amostra','Número da amostra','text'],['tubito_inicial','Primeiro tubito','number'],['tubito_final','Último tubito','number']]},
  especimes: {titulo:'Espécimes',campos:[['especie','Espécie','text'],['larvas','Larvas','number'],['pupas','Pupas','number'],['pupa_aedes','Pupas Aedes','number'],['adultos','Adultos','number']]},
  tratamentos: {titulo:'Tratamentos',campos:[['categoria','Categoria','select',{LARVICIDA_1:'Larvicida 1',LARVICIDA_2:'Larvicida 2',ADULTICIDA:'Adulticida'}],['produto','Produto','optional'],['quantidade','Quantidade de produto','decimal'],['depositos_tratados','Depósitos tratados','number'],['cargas','Cargas','number']]},
  'depositos-eliminados': {titulo:'Depósitos eliminados',campos:[['tipo','Tipo de depósito','text'],['quantidade','Quantidade','number']]}
};

export function formulario(campos, dados={}, textoBotao='Salvar') {
  return `<form id="edit-form"><div class="form-grid">${campos.map(([nome,label,tipo,opcoes]) => {
    const valor = dados[nome] ?? (['number','decimal'].includes(tipo) ? 0 : '');
    let controle;
    if (tipo === 'select') controle=`<select name="${nome}">${Object.entries(opcoes).map(([k,v])=>`<option value="${escapar(k)}" ${String(valor)===k?'selected':''}>${escapar(v)}</option>`).join('')}</select>`;
    else if (tipo === 'textarea') controle=`<textarea name="${nome}" rows="3" maxlength="10000">${escapar(valor)}</textarea>`;
    else controle=`<input name="${nome}" type="${['number','decimal'].includes(tipo)?'number':tipo==='optional'?'text':tipo}" value="${escapar(valor)}" ${['text','password','date','number','decimal'].includes(tipo)?'required':''} ${['number','decimal'].includes(tipo)?`min="0" step="${tipo==='decimal'?'any':'1'}"`:''} ${tipo==='password'?'minlength="6" maxlength="72" autocomplete="new-password"':''}>`;
    return `<div class="${tipo==='textarea'?'wide':''}"><label for="campo-${nome}">${escapar(label)}</label>${controle.replace(`name="${nome}"`, `id="campo-${nome}" name="${nome}"`)}</div>`;
  }).join('')}</div><p class="form-error" role="alert"></p><footer><button type="button" class="secondary" data-cancel>Cancelar</button><button class="primary" type="submit">${escapar(textoBotao)}</button></footer></form>`;
}

export function lerFormulario(form, campos) {
  const dados = Object.fromEntries(new FormData(form));
  for (const [nome,,tipo] of campos) {
    if (['number','decimal'].includes(tipo)) dados[nome]=Number(dados[nome]);
    else if (!dados[nome] && ['optional','textarea','time'].includes(tipo)) dados[nome]=null;
  }
  return dados;
}
