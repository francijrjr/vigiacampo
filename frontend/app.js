import { api, baixar, ErroConexao, guardarSessao, usuarioAtual } from './api.js';
import { camposBoletim, camposImovelBoletim, cartoesBoletins, telaBoletim } from './boletim.js';
import { atividades, camposImovel, camposQuarteirao, camposRegistro, colecoes, escapar as e, formulario, lerFormulario, pendencias, situacoes, tipos } from './forms.js';
import { icone } from './icons.js';

const app = document.querySelector('#app');
const dialog = document.querySelector('#dialog');
let pagina = 0;
let filtros = {};
let renderAtual = 0;
let urlsFotos = [];
let temporizador;
const hoje = () => new Date().toLocaleDateString('en-CA');
const dataBr = valor => valor ? new Date(`${valor}T12:00:00`).toLocaleDateString('pt-BR') : '—';
const filaChave = () => `alberio.fila.${usuarioAtual()?.id}`;
const fila = () => JSON.parse(localStorage.getItem(filaChave()) || '[]');
const guardarFila = registros => localStorage.setItem(filaChave(), JSON.stringify(registros));
const badge = r => `<span class="badge ${e(r.status)}">${icone(r.status==='SYNCED'?'circle-check':'circle-dashed')} ${e(situacoes[r.status])}</span>`;
const empty = (titulo, texto, botao='') => `<div class="empty"><div class="empty-icon">${icone('clipboard-list')}</div><h3>${e(titulo)}</h3><p>${e(texto)}</p>${botao}</div>`;
const painel = (titulo, conteudo, acao='') => `<section class="panel"><div class="panel-heading"><h2>${e(titulo)}</h2>${acao}</div>${conteudo}</section>`;
const iconesAcao = {sair:'log-out',pdf:'download',duplicar:'copy',senha:'key-round',fila:'clipboard-list',sincronizar:'send',recarregar:'refresh-cw','enviar-registro':'send','limpar-filtros':'list-filter'};
const botao = (texto, acao, classe='secondary') => {
  const nome=acao.split(':')[0];
  const desenho=iconesAcao[nome] || (nome.startsWith('novo')||nome.startsWith('nova')?'plus':nome.startsWith('editar')?'pencil':nome.startsWith('excluir')?'trash-2':null);
  const label=texto.replace(/^\+\s*/, '').replace(/\s*[↗↓]$/, '');
  return `<button class="${classe}" data-action="${acao}">${desenho?icone(desenho):''}<span>${e(label)}</span></button>`;
};
const titulo = (nome, descricao, acao='') => `<div class="page-heading"><div><h1>${e(nome)}</h1><p>${e(descricao)}</p></div>${acao}</div>`;

function avisar(texto) {
  clearTimeout(temporizador);
  document.querySelector('#notice').textContent=texto;
  temporizador=setTimeout(()=>document.querySelector('#notice').textContent='',5000);
}
function modal(titulo, campos, dados, salvar, textoBotao='Salvar') {
  document.querySelector('#dialog-title').textContent=titulo;
  document.querySelector('#dialog-body').innerHTML=formulario(campos,dados,textoBotao);
  dialog.showModal();
  dialog.querySelector('[data-cancel]').onclick=()=>dialog.close();
  dialog.querySelector('form').onsubmit=async evento=>{
    evento.preventDefault();
    const form=evento.currentTarget, submit=form.querySelector('[type=submit]');
    submit.disabled=true;
    try { await salvar(lerFormulario(form,campos)); dialog.close(); avisar('Dados salvos com sucesso.'); await render(); }
    catch(erro) { form.querySelector('.form-error').textContent=erro.message; }
    finally { submit.disabled=false; }
  };
}
document.querySelector('#close-dialog').onclick=()=>dialog.close();
document.querySelector('#close-dialog').innerHTML=icone('x');

function login() {
  ++renderAtual;
  app.innerHTML=`<div class="login"><section class="login-story"><div class="brand"><span class="brand-mark">V</span>VigiaCampo</div><div><h1>O cuidado com a cidade começa <em>em campo.</em></h1><p>Um lugar para organizar visitas, acompanhar sua equipe e registrar cada ação contra a dengue.</p></div><div class="eyebrow">Vigilância em saúde · PNCD</div></section><div class="login-form"><section><span class="eyebrow">Seu espaço de trabalho</span><h2>Bom ter você por aqui.</h2><p>Entre na sua conta para acompanhar as atividades.</p><form id="login"><label>Usuário<input name="username" autocomplete="username" required placeholder="Seu nome de usuário"></label><label>Senha<input name="password" type="password" autocomplete="current-password" required placeholder="Sua senha"></label><p class="form-error" role="alert"></p><button class="primary">Entrar na minha conta ${icone('arrow-right')}</button></form><p class="login-footer">Precisa de acesso? Fale com o supervisor da sua equipe.</p><a class="subtle-link" href="/docs" target="_blank" rel="noopener">Documentação da API ${icone('arrow-up-right')}</a></section></div></div>`;
  document.querySelector('#login').onsubmit=async evento=>{
    evento.preventDefault(); const form=evento.currentTarget, submit=form.querySelector('button'); submit.disabled=true;
    try { guardarSessao(await api('/auth/login',{method:'POST',body:Object.fromEntries(new FormData(form))})); await render(); }
    catch(erro){form.querySelector('.form-error').textContent=erro.message;}
    finally{submit.disabled=false;}
  };
}

function estrutura(rota) {
  const user=usuarioAtual();
  const menu=[['inicio','layout-dashboard','Visão geral'],['registros','clipboard-list','Registros diários'],...(user.role==='SUPERVISOR'?[['equipe','users','Minha equipe'],['relatorios','chart-no-axes-combined','Relatórios']]:[]),['conta','settings','Minha conta']];
  app.innerHTML=`<div class="layout"><aside class="sidebar"><div class="brand"><span class="brand-mark">V</span>VigiaCampo</div><div class="nav-label">ESPAÇO DE TRABALHO</div><nav>${menu.map(([id,nomeIcone,nome])=>`<a class="nav-link ${rota===id?'active':''}" href="#${id}"><span class="nav-icon">${icone(nomeIcone)}</span>${nome}</a>`).join('')}</nav><div class="sidebar-bottom"><div class="field-note"><strong>Pequenas ações.<br>Uma cidade mais protegida.</strong>Cada visita registrada ajuda a acompanhar o cuidado com a comunidade.</div><div class="profile"><span class="avatar">${e(user.full_name.split(' ').map(s=>s[0]).slice(0,2).join(''))}</span><div><p>${e(user.full_name)}</p><small>${user.role==='SUPERVISOR'?'Supervisor':'Agente de campo'}</small></div></div>${botao('Sair da conta','sair','text-button')}</div></aside><main class="main"><header class="topbar"><span>Vigilância em saúde <span class="muted"> / ${e(user.municipio || 'PNCD')}</span></span><span class="connection ${navigator.onLine?'':'offline'}">${icone(navigator.onLine?'wifi':'wifi-off')}${navigator.onLine?'Conectado':'Sem conexão'}</span></header><div id="content" class="content"><p class="loading">Carregando informações…</p></div></main></div>`;
}

function tabelaRegistros(registros) {
  if (!registros.length) return empty('Nenhum registro por aqui','Comece registrando as atividades do seu dia.',botao('+ Criar registro','novo-registro','primary'));
  return `<div class="table-wrap"><table><thead><tr><th>Data / município</th><th>Área / ciclo</th><th>Atividade</th><th>Imóveis</th><th>Situação</th><th></th></tr></thead><tbody>${registros.map(r=>`<tr><td><strong>${dataBr(r.data)}</strong><small>${e(r.municipio)}</small></td><td><strong>${e(r.codigo_area)}</strong><small>Ciclo ${e(r.ciclo)}</small></td><td>${e(atividades[r.atividade] || r.atividade)}</td><td>${r.resumo_imoveis_trabalhados}</td><td>${badge(r)}</td><td><a class="text-button" href="#registro/${r.id}">Abrir ${icone('arrow-right')}</a></td></tr>`).join('')}</tbody></table></div>`;
}

function filaPainel() {
  const pendentes=fila();
  return pendentes.length?`<div class="queue-note"><span><strong>${pendentes.length} registro(s) salvo(s) neste aparelho.</strong> Envie quando estiver conectado.</span>${botao('Revisar e enviar','fila')}</div>`:'';
}

async function inicio() {
  const resumo=await api('/painel');
  const recentes=await api('/registros/?limit=5');
  const nome=usuarioAtual().full_name.split(' ')[0];
  return titulo(`Olá, ${nome}.`,'Vamos acompanhar o trabalho em campo?',botao('+ Novo registro','novo-registro','primary'))+filaPainel()+
  `<section class="work-card"><div class="work-copy"><span class="eyebrow">${icone('map-pin')} Seu dia em campo</span><h2>Tudo pronto para<br>a próxima visita.</h2><p>Registre os imóveis visitados e acompanhe o que ainda precisa ser enviado.</p><div class="work-actions">${botao('Nova atividade','novo-registro','primary')}<a class="text-button" href="#registros">Consultar registros ${icone('arrow-right')}</a></div></div><aside class="work-summary"><span class="work-summary-icon">${icone('clipboard-check')}</span><span class="eyebrow">Para acompanhar</span><div class="work-count"><strong>${resumo.total_rascunhos}</strong><span>${resumo.total_rascunhos===1?'registro em rascunho':'registros em rascunho'}</span></div><p>${resumo.total_rascunhos?'Continue de onde parou e envie quando terminar.':'Tudo em dia. Comece uma nova atividade quando precisar.'}</p></aside></section>`+
  `<div class="metrics">${[['Registros no total',resumo.total_registros,'Histórico da sua área de acesso','clipboard-list'],['Imóveis registrados',resumo.total_imoveis,'Visitas cadastradas','house'],['Registros enviados',resumo.total_enviados,'Disponíveis para acompanhamento','send'],['Em rascunho',resumo.total_rascunhos,'Atividades para continuar','file-pen-line']].map(([label,valor,ajuda,nomeIcone])=>`<article class="metric"><div class="metric-header">${label}<span class="metric-icon">${icone(nomeIcone)}</span></div><strong>${valor}</strong><small>${ajuda}</small></article>`).join('')}</div>`+
  painel('Registros recentes',tabelaRegistros(recentes),`<a class="text-button" href="#registros">Ver todos ${icone('arrow-right')}</a>`);
}

async function registros() {
  const busca=new URLSearchParams({...filtros,skip:pagina*20,limit:20});
  const dados=await api(`/registros/?${busca}`);
  return titulo('Registros diários','O histórico de cada ação em campo.',botao('+ Novo registro','novo-registro','primary'))+filaPainel()+
    `<section class="panel"><form id="filters" class="filters"><label>De<input type="date" name="data_inicio" value="${e(filtros.data_inicio)}"></label><label>Até<input type="date" name="data_fim" value="${e(filtros.data_fim)}"></label><label>Zona / bairro<input name="zona" value="${e(filtros.zona)}" placeholder="Todas as zonas"></label><label>Situação<select name="status"><option value="">Todas</option>${Object.entries(situacoes).map(([k,v])=>`<option value="${k}" ${filtros.status===k?'selected':''}>${v}</option>`).join('')}</select></label><button class="primary">Filtrar</button>${botao('Limpar','limpar-filtros')}</form>${tabelaRegistros(dados)}<div class="pager"><button class="secondary" data-action="anterior" ${!pagina?'disabled':''}>${icone('arrow-left')} Anterior</button><span>Página ${pagina+1}</span><button class="secondary" data-action="proxima" ${dados.length<20?'disabled':''}>Próxima ${icone('arrow-right')}</button></div></section>`;
}

let registroAberto;
let imovelAberto;
let boletimAberto;
let abaVisita='inspecoes';
const podeEditar = r => r.status!=='SYNCED' || usuarioAtual().role==='SUPERVISOR';
async function detalheRegistro(id,versao) {
  const [r,boletins]=await Promise.all([api(`/registros/${id}`),api(`/registros/${id}/boletins`)]);
  if(versao!==renderAtual)return '';
  registroAberto=r;
  const editar=podeEditar(r);
  return `<a class="subtle-link" href="#registros">${icone('arrow-left')} Voltar aos registros</a><br><br>`+
    titulo(`Registro de ${dataBr(r.data)}`,`${r.municipio} · Área ${r.codigo_area} · Ciclo ${r.ciclo}`,badge(r))+
    cartoesBoletins(boletins,r.id,editar)+
    `<div class="actions" style="margin-bottom:24px">${editar?botao('Editar informações','editar-registro'):''}${r.status!=='SYNCED'?botao('Enviar registro','enviar-registro','primary'):''}${botao('Duplicar','duplicar')}${usuarioAtual().role==='SUPERVISOR'?botao('Baixar PDF ↓','pdf'):''}${editar?botao('Excluir registro','excluir-registro','danger'):''}</div>`+
    `<div class="detail-grid">${painel('Informações do dia',`<div class="detail-body"><dl class="data-list"><div><dt>Atividade</dt><dd>${e(atividades[r.atividade])}</dd></div><div><dt>Zona / bairro</dt><dd>${e(r.zona || 'Não informado')}</dd></div><div><dt>Imóveis</dt><dd>${r.resumo_imoveis_trabalhados}</dd></div><div><dt>Pendências</dt><dd>${r.resumo_pendencias}</dd></div><div><dt>Depósitos inspecionados</dt><dd>${r.resumo_depositos_inspecionados}</dd></div><div><dt>Exemplares encontrados</dt><dd>${r.resumo_exemplares}</dd></div></dl><p class="muted">Observações</p><p style="white-space:pre-wrap">${e(r.observacoes || 'Nenhuma observação.')}</p></div>`)}
    ${painel('Quarteirões',r.quarteiroes.length?r.quarteiroes.map(q=>`<div class="item-card"><div><strong>Quarteirão ${e(q.numero)}</strong><p>${e(q.logradouro || 'Rua não informada')}</p></div>${editar?`<div class="actions">${botao('Editar',`editar-quarteirao:${q.id}`)}${botao('Excluir',`excluir-quarteirao:${q.id}`,'danger')}</div>`:''}</div>`).join(''):empty('Cadastre o primeiro quarteirão','Organize os imóveis por rua ou quarteirão.'),editar?botao('+ Adicionar','novo-quarteirao'):'' )}</div>`+
    painel('Imóveis e visitas',r.imoveis.length?`<div class="table-wrap"><table><thead><tr><th>Imóvel</th><th>Quarteirão</th><th>Tipo</th><th>Pendência</th><th></th></tr></thead><tbody>${r.imoveis.map(im=>`<tr><td><strong>Nº ${e(im.numero)}</strong><small>${e(im.complemento)}</small></td><td>${e(r.quarteiroes.find(q=>q.id===im.quarteirao_id)?.numero || '—')}</td><td>${e(tipos[im.tipo])}</td><td>${e(pendencias[im.pendencia])}</td><td><a class="text-button" href="#visita/${r.id}/${im.id}">Abrir visita ${icone('arrow-right')}</a></td></tr>`).join('')}</tbody></table></div>`:empty('Ainda não há imóveis','Adicione um imóvel para registrar inspeções, coletas e tratamentos.'),editar?botao('+ Adicionar imóvel','novo-imovel','primary'):'');
}

async function visita(registroId,imovelId,versao) {
  const r=await api(`/registros/${registroId}`);
  if(versao!==renderAtual)return '';
  registroAberto=r;
  const im=imovelAberto=r.imoveis.find(i=>i.id===Number(imovelId));
  if(!im) throw new Error('Imóvel não encontrado.');
  const editar=podeEditar(r);
  const abas={...Object.fromEntries(Object.entries(colecoes).map(([k,v])=>[k,v.titulo])),fotos:'Fotos'};
  let conteudo;
  if(abaVisita==='fotos') {
    conteudo=im.fotos.length?`<div class="photos">${im.fotos.map(f=>`<article><img data-foto="${f.id}" alt="${e(f.descricao || 'Foto da visita')}" loading="lazy"><p>${e(f.descricao || 'Evidência da visita')}</p>${editar?botao('Excluir',`excluir-foto:${f.id}`,'danger'):''}</article>`).join('')}</div>`:empty('Nenhuma foto adicionada','As fotos ficam vinculadas à visita e não entram no PDF.');
  } else {
    const definicao=colecoes[abaVisita], itens=im[abaVisita.replaceAll('-','_')];
    conteudo=itens.length?itens.map(item=>`<div class="item-card"><div>${definicao.campos.map(([k,label,tipo,opcoes])=>`<p><strong>${e(label)}:</strong> ${e(tipo==='select'?opcoes[item[k]]:item[k]??'—')}</p>`).join('')}</div>${editar?`<div class="actions">${botao('Editar',`editar-item:${item.id}`)}${botao('Excluir',`excluir-item:${item.id}`,'danger')}</div>`:''}</div>`).join(''):empty(`Sem ${definicao.titulo.toLowerCase()} nesta visita`,'Adicione os dados encontrados em campo.');
  }
  return `<a class="subtle-link" href="#registro/${r.id}">${icone('arrow-left')} Voltar ao registro</a><br><br>`+titulo(`Visita ao imóvel nº ${im.numero}`,`${tipos[im.tipo]} · ${pendencias[im.pendencia]}`,editar?botao('Editar imóvel','editar-imovel'):'')+
    `<section class="panel"><div class="visit-tabs">${Object.entries(abas).map(([k,v])=>`<button class="secondary ${abaVisita===k?'active':''}" data-action="aba:${k}">${v}</button>`).join('')}</div><div class="panel-heading"><h2>${e(abas[abaVisita])}</h2>${editar?botao('+ Adicionar',abaVisita==='fotos'?'nova-foto':'novo-item','primary'):''}</div>${conteudo}</section>${editar?botao('Excluir imóvel','excluir-imovel','danger'):''}`;
}

let equipeAtual=[];
async function equipe(versao) {
  const dados=await api(`/users/?skip=${pagina*100}&limit=100`);
  if(versao!==renderAtual)return '';
  equipeAtual=dados;
  return titulo('Minha equipe','Pessoas que levam o cuidado para as ruas.',botao('+ Adicionar agente','novo-agente','primary'))+
    painel('Agentes de campo',equipeAtual.length?`<div class="table-wrap"><table><thead><tr><th>Agente</th><th>Usuário</th><th>Município</th><th>Acesso</th><th></th></tr></thead><tbody>${equipeAtual.map(u=>`<tr><td><strong>${e(u.full_name)}</strong><small>${e(u.email)}</small></td><td>${e(u.username)}</td><td>${e(u.municipio)}</td><td><span class="badge ${u.is_active?'SYNCED':''}">${u.is_active?'Ativo':'Desativado'}</span></td><td><div class="actions">${botao('Editar',`editar-agente:${u.id}`)}${botao(u.is_active?'Desativar':'Ativar',`acesso-agente:${u.id}`,u.is_active?'danger':'secondary')}</div></td></tr>`).join('')}</tbody></table></div>`:empty('Sua equipe começa aqui','Cadastre um agente para liberar o acesso ao sistema.'))+`<div class="pager"><button class="secondary" data-action="anterior" ${pagina===0?'disabled':''}>${icone('arrow-left')} Anterior</button><span>Página ${pagina+1}</span><button class="secondary" data-action="proxima" ${equipeAtual.length<100?'disabled':''}>Próxima ${icone('arrow-right')}</button></div>`;
}

async function relatorios() {
  const dados=await api(`/relatorios/estatisticas?${new URLSearchParams(Object.fromEntries(Object.entries(filtros).filter(([k])=>k!=='status')))}`);
  return titulo('Relatórios','Acompanhe os resultados dos registros enviados.')+
    `<section class="panel"><form id="filters" class="filters"><label>De<input type="date" name="data_inicio" value="${e(filtros.data_inicio)}"></label><label>Até<input type="date" name="data_fim" value="${e(filtros.data_fim)}"></label><label>Zona<input name="zona" value="${e(filtros.zona)}"></label><button class="primary">Filtrar</button>${botao('Limpar','limpar-filtros')}</form>${dados.length?`<div class="table-wrap"><table><thead><tr><th>Agente</th><th>Registros</th><th>Imóveis</th><th>Depósitos inspecionados</th><th>Período</th></tr></thead><tbody>${dados.map(d=>`<tr><td><strong>${e(d.agente_nome)}</strong></td><td>${d.total_registros}</td><td>${d.total_imoveis}</td><td>${d.total_inspecoes}</td><td>${dataBr(d.periodo_inicio)} a ${dataBr(d.periodo_fim)}</td></tr>`).join('')}</tbody></table></div>`:empty('Sem resultados no período','Os resultados aparecem depois que os registros são enviados.')}</section><p class="muted">Para baixar o PDF de uma atividade, abra o registro e clique em “Baixar PDF”.</p>`;
}

function conta() {
  const u=usuarioAtual();
  return titulo('Minha conta','Suas informações de acesso.')+painel('Perfil',`<div class="detail-body"><h2>${e(u.full_name)}</h2><p>Usuário: ${e(u.username)}<br>E-mail: ${e(u.email || 'Não informado')}<br>Município: ${e(u.municipio || 'Não informado')}</p><div class="actions">${botao('Alterar senha','senha','primary')}${botao('Sair da conta','sair')}</div></div>`)+painel('Documentação da API',`<div class="detail-body"><p>Consulte as rotas, os campos e os exemplos de uso.</p><a class="primary" href="/docs" target="_blank" rel="noopener">Abrir Swagger ${icone('arrow-up-right')}</a></div>`);
}

async function render() {
  const numero=++renderAtual;
  urlsFotos.forEach(URL.revokeObjectURL); urlsFotos=[];
  if(!usuarioAtual()) return login();
  const [rota='inicio',id,imovelId]=(location.hash.slice(1)||'inicio').split('/');
  estrutura(['registro','visita','boletim'].includes(rota)?'registros':rota);
  try {
    let html;
    if(rota==='inicio') html=await inicio();
    else if(rota==='registros') html=await registros();
    else if(rota==='registro') html=await detalheRegistro(id,numero);
    else if(rota==='visita') html=await visita(id,imovelId,numero);
    else if(rota==='boletim'){
      const dados=await api(`/registros/${id}/boletins/${imovelId}`);
      if(numero!==renderAtual)return;
      boletimAberto=dados;html=telaBoletim(dados);
    }
    else if(rota==='equipe' && usuarioAtual().role==='SUPERVISOR') html=await equipe(numero);
    else if(rota==='relatorios' && usuarioAtual().role==='SUPERVISOR') html=await relatorios();
    else if(rota==='conta') html=conta();
    else html=empty('Página não encontrada','Use o menu para continuar.');
    if(numero!==renderAtual) return;
    document.querySelector('#content').innerHTML=html;
    const form=document.querySelector('#filters');
    if(form) form.onsubmit=ev=>{ev.preventDefault();filtros=Object.fromEntries([...new FormData(form)].filter(([,v])=>v));pagina=0;render();};
    for (const img of document.querySelectorAll('[data-foto]')) {
      api(`/fotos/${img.dataset.foto}/arquivo`,{arquivo:true}).then(blob=>{
        if(numero!==renderAtual) return;
        const url=URL.createObjectURL(blob);urlsFotos.push(url);img.src=url;
      }).catch(()=>{img.alt='Não foi possível carregar esta foto';});
    }
  } catch(erro) {
    if(numero!==renderAtual) return;
    if(erro instanceof ErroConexao){
      const indicador=document.querySelector('.connection');
      indicador.classList.add('offline');indicador.innerHTML=icone('wifi-off')+'Servidor indisponível';
    }
    document.querySelector('#content').innerHTML=filaPainel()+empty('Não foi possível carregar',erro.message,botao('Tentar novamente','recarregar','primary'))+(erro instanceof ErroConexao?botao('+ Criar registro neste aparelho','novo-registro'):'');
  }
}

function novoRegistro() {
  modal('Novo registro diário',camposRegistro,{municipio:usuarioAtual().municipio,data:hoje(),atividade:'LI'},async dados=>{
    dados.client_id=crypto.randomUUID();
    if(!navigator.onLine){guardarFila([...fila(),dados]);return;}
    try { const r=await api('/registros/',{method:'POST',body:dados});location.hash=`registro/${r.id}`; }
    catch(erro){if(erro instanceof ErroConexao){guardarFila([...fila(),dados]);}else throw erro;}
  },'Criar registro');
}
function camposDoImovel() {
  return [...camposImovel,['quarteirao_id','Quarteirão','select',{'':'Sem quarteirão',...Object.fromEntries(registroAberto.quarteiroes.map(q=>[q.id,`${q.numero} · ${q.logradouro || ''}`]))}]];
}
const caminhoVisita = () => `/registros/${registroAberto.id}/imoveis/${imovelAberto.id}`;

async function acao(nome,valor) {
  const r=registroAberto;
  if(nome==='novo-boletim')return modal('Novo Boletim de Reconhecimento',camposBoletim,{
    municipio:r.municipio,localidade:r.zona||'',responsavel:usuarioAtual().full_name,
    funcao_responsavel:'AGENTE',data:r.data,categoria:'Urbana'},async dados=>{
      const novo=await api(`/registros/${r.id}/boletins`,{method:'POST',body:dados});
      location.hash=`boletim/${r.id}/${novo.id}`;
    },'Criar boletim');
  if(nome==='editar-boletim')return modal('Editar cabeçalho',camposBoletim,boletimAberto,dados=>
    api(`/registros/${boletimAberto.registro_id}/boletins/${boletimAberto.id}`,{method:'PUT',body:dados}));
  if(nome==='pdf-boletim')return baixar(`/registros/${boletimAberto.registro_id}/boletins/${boletimAberto.id}/pdf`,`boletim-quarteirao-${boletimAberto.quarteirao_numero}.pdf`);
  if(nome==='novo-imovel-boletim'||nome==='editar-imovel-boletim'){
    const b=boletimAberto;
    const anterior=b.imoveis.at(-1);
    const dados=valor?b.imoveis.find(im=>im.id===Number(valor)):{logradouro:anterior?.logradouro||'',lado:anterior?.lado||'',tipo:'RESIDENCIAL'};
    return modal(valor?'Editar imóvel do boletim':'Adicionar imóvel ao boletim',camposImovelBoletim,dados,payload=>
      api(`/registros/${b.registro_id}/imoveis${valor?'/'+valor:''}`,{method:valor?'PATCH':'POST',body:{...payload,quarteirao_id:b.quarteirao_id}}));
  }
  if(nome==='excluir-imovel-boletim'){
    if(!confirm('Excluir este imóvel e os dados da visita? O fechamento do boletim será atualizado.'))return;
    await api(`/registros/${boletimAberto.registro_id}/imoveis/${valor}`,{method:'DELETE'});
    return render();
  }
  if(nome==='novo-registro') return novoRegistro();
  if(nome==='recarregar') return render();
  if(nome==='anterior'){pagina--;return render();}
  if(nome==='proxima'){pagina++;return render();}
  if(nome==='limpar-filtros'){filtros={};pagina=0;return render();}
  if(nome==='sair'){await api('/auth/logout',{method:'POST'});guardarSessao(null);return login();}
  if(nome==='editar-registro') return modal('Editar registro',camposRegistro,r,dados=>api(`/registros/${r.id}`,{method:'PATCH',body:dados}));
  if(nome==='enviar-registro'){
    if(!confirm('Enviar este registro? Depois do envio, somente o supervisor poderá alterá-lo.'))return;
    await api(`/registros/${r.id}`,{method:'PATCH',body:{status:'SYNCED',concluido:true}});
  }
  if(nome==='duplicar'){const novo=await api(`/registros/${r.id}/duplicar`,{method:'POST'});location.hash=`registro/${novo.id}`;return;}
  if(nome==='pdf') return baixar(`/relatorios/registro/${r.id}/pdf`,`registro-${r.id}.pdf`);
  if(nome==='excluir-registro'){
    if(!confirm('Excluir este registro e todas as visitas? Esta ação não pode ser desfeita.'))return;
    await api(`/registros/${r.id}`,{method:'DELETE'});location.hash='registros';return;
  }
  if(nome==='novo-quarteirao' || nome==='editar-quarteirao') return modal(nome==='novo-quarteirao'?'Adicionar quarteirão':'Editar quarteirão',camposQuarteirao,r.quarteiroes.find(q=>q.id===Number(valor)),dados=>api(`/registros/${r.id}/quarteiroes${valor?`/${valor}`:''}`,{method:valor?'PUT':'POST',body:dados}));
  if(nome==='excluir-quarteirao'){
    if(!confirm('Excluir este quarteirão?'))return;
    await api(`/registros/${r.id}/quarteiroes/${valor}`,{method:'DELETE'});
  }
  if(nome==='novo-imovel' || nome==='editar-imovel') return modal(nome==='novo-imovel'?'Adicionar imóvel':'Editar imóvel',camposDoImovel(),nome==='editar-imovel'?imovelAberto:{},dados=>{
    dados.quarteirao_id=dados.quarteirao_id?Number(dados.quarteirao_id):null;
    return api(`/registros/${r.id}/imoveis${nome==='editar-imovel'?`/${imovelAberto.id}`:''}`,{method:nome==='editar-imovel'?'PATCH':'POST',body:dados});
  });
  if(nome==='excluir-imovel'){
    if(!confirm('Excluir o imóvel, os dados da visita e as fotos vinculadas?'))return;
    await api(caminhoVisita(),{method:'DELETE'});location.hash=`registro/${r.id}`;return;
  }
  if(nome==='aba'){abaVisita=valor;return render();}
  if(nome==='novo-item' || nome==='editar-item'){
    const definicao=colecoes[abaVisita];
    return modal(definicao.titulo,definicao.campos,imovelAberto[abaVisita.replaceAll('-','_')].find(i=>i.id===Number(valor)),dados=>api(`${caminhoVisita()}/${abaVisita}${valor?`/${valor}`:''}`,{method:valor?'PUT':'POST',body:dados}));
  }
  if(nome==='excluir-item'){
    if(!confirm('Excluir este item da visita?'))return;
    await api(`${caminhoVisita()}/${abaVisita}/${valor}`,{method:'DELETE'});
  }
  if(nome==='nova-foto'){
    document.querySelector('#dialog-title').textContent='Adicionar foto';
    document.querySelector('#dialog-body').innerHTML=`<form id="photo-form"><label>Foto (JPEG, PNG ou WebP, até 10 MB)<input name="file" type="file" accept="image/jpeg,image/png,image/webp" required></label><label>Descrição<input name="descricao" maxlength="500"></label><p class="form-error" role="alert"></p><footer><button class="primary">Enviar foto</button></footer></form>`;
    dialog.showModal();dialog.querySelector('form').onsubmit=async ev=>{
      ev.preventDefault();const form=ev.currentTarget,submit=form.querySelector('button');submit.disabled=true;
      try{await api(`/fotos/imovel/${imovelAberto.id}`,{method:'POST',body:new FormData(form)});dialog.close();await render();}
      catch(erro){form.querySelector('.form-error').textContent=erro.message;}finally{submit.disabled=false;}
    };return;
  }
  if(nome==='excluir-foto'){
    if(!confirm('Excluir esta foto?'))return;
    await api(`/fotos/${valor}`,{method:'DELETE'});
  }
  if(nome==='novo-agente' || nome==='editar-agente'){
    const campos=[...(nome==='novo-agente'?[['username','Nome de usuário','text'],['password','Senha inicial','password']]:[]),['full_name','Nome completo','text'],['email','E-mail','email'],['municipio','Município','text']];
    return modal(nome==='novo-agente'?'Adicionar agente':'Editar agente',campos,equipeAtual.find(u=>u.id===Number(valor)) || {municipio:usuarioAtual().municipio},dados=>api(`/users/${valor || ''}`,{method:valor?'PATCH':'POST',body:dados}));
  }
  if(nome==='acesso-agente'){
    const u=equipeAtual.find(u=>u.id===Number(valor));
    if(!confirm(`${u.is_active?'Desativar':'Ativar'} o acesso de ${u.full_name}?`))return;
    await api(`/users/${u.id}`,{method:'PATCH',body:{is_active:!u.is_active}});
  }
  if(nome==='senha') return modal('Alterar senha',[['current_password','Senha atual','password'],['new_password','Nova senha','password']],{},async dados=>{
    await api('/auth/change-password',{method:'POST',body:dados});guardarSessao(null);
  },'Alterar e entrar novamente');
  if(nome==='fila'){
    document.querySelector('#dialog-title').textContent='Registros neste aparelho';
    document.querySelector('#dialog-body').innerHTML=`<p class="muted">Estes rascunhos ainda não foram enviados. Eles ficam neste navegador, vinculados à sua conta.</p>${fila().map((item,i)=>`<div class="item-card"><div><strong>${dataBr(item.data)} · ${e(item.municipio)}</strong><p>Área ${e(item.codigo_area)}</p></div><div class="actions">${botao('Editar',`editar-fila:${i}`)}${botao('Excluir',`excluir-fila:${i}`,'danger')}</div></div>`).join('')}<br>${botao('Enviar registros','sincronizar','primary')}`;
    dialog.showModal();return;
  }
  if(nome==='editar-fila'){
    dialog.close();return modal('Editar registro neste aparelho',camposRegistro,fila()[Number(valor)],dados=>{const itens=fila();itens[Number(valor)]={...itens[Number(valor)],...dados};guardarFila(itens);});
  }
  if(nome==='excluir-fila'){
    if(!confirm('Excluir este rascunho do aparelho?'))return;
    guardarFila(fila().filter((_,i)=>i!==Number(valor)));dialog.close();
  }
  if(nome==='sincronizar'){
    const itens=fila();
    if(!itens.length)return;
    await api('/registros/sync',{method:'POST',body:{registros:itens}});
    guardarFila([]);dialog.close();avisar('Registros enviados com sucesso.');
  }
  await render();
}

document.addEventListener('click',async evento=>{
  const button=evento.target.closest('[data-action]');if(!button)return;
  evento.preventDefault();if(button.disabled)return;
  button.disabled=true;
  try{const [nome,valor]=button.dataset.action.split(':');await acao(nome,valor);}
  catch(erro){avisar(erro.message);}
  finally{button.disabled=false;}
});
window.addEventListener('hashchange',()=>{pagina=0;render();});
window.addEventListener('online',()=>{avisar('Conexão restabelecida. Você pode enviar seus rascunhos.');render();});
window.addEventListener('offline',()=>render());
window.addEventListener('sessao-encerrada',()=>{dialog.close();login();});
if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});
render();
