const state = {
  apiBase: localStorage.getItem("achei_api_base") || "http://127.0.0.1:8000",
  usuario: JSON.parse(localStorage.getItem("achei_usuario") || "null"),
  postos: [],
  itens: [],
  retiradas: [],
};

const PERMISSIONS = {
  "Aluno": ["rf10", "rf11", "rf12", "rf13", "rf15"],
  "Funcionário": ["rf03", "rf06", "rf07", "rf10", "rf11", "rf12", "rf13", "rf14", "rf15"],
  "Administrador": ["rf02", "rf03", "rf04", "rf05", "rf06", "rf07", "rf08", "rf09", "rf10", "rf11", "rf12", "rf13", "rf14", "rf15"],
};

const FUNCTIONALITIES = [
  ["rf02", "RF02", "Cadastrar postos de apoio"],
  ["rf03", "RF03", "Consultar postos de apoio"],
  ["rf04", "RF04", "Atualizar postos de apoio"],
  ["rf05", "RF05", "Excluir postos de apoio"],
  ["rf06", "RF06", "Registrar termo de retirada"],
  ["rf07", "RF07", "Consultar termos de retirada"],
  ["rf08", "RF08", "Atualizar termo de retirada"],
  ["rf09", "RF09", "Excluir termo de retirada"],
  ["rf10", "RF10", "Registrar item perdido"],
  ["rf11", "RF11", "Consultar itens perdidos"],
  ["rf12", "RF12", "Consultar registros de itens por posto"],
  ["rf13", "RF13", "Consultar itens disponíveis para retirada"],
  ["rf14", "RF14", "Registrar entrega de item em posto"],
  ["rf15", "RF15", "Excluir item"],
];

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function apiUrl(path) {
  return `${state.apiBase.replace(/\/$/, "")}${path}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toast(message, type = "success") {
  const el = $("#toast");
  if (!el) {
    alert(message);
    return;
  }
  el.textContent = message;
  el.className = `toast ${type}`;
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => el.classList.add("hidden"), 4200);
}

async function request(path, options = {}) {
  const config = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };
  if (state.usuario?.token) config.headers["X-Achei-Token"] = state.usuario.token;
  if (state.usuario?.perfil) config.headers["X-Achei-Perfil"] = state.usuario.perfil;
  if (config.body && typeof config.body !== "string") config.body = JSON.stringify(config.body);

  const response = await fetch(apiUrl(path), config);
  if (response.status === 204) return null;

  const text = await response.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!response.ok) {
    const detail = typeof data?.detail === "string"
      ? data.detail
      : Array.isArray(data?.detail)
        ? data.detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
        : `Erro HTTP ${response.status}`;
    throw new Error(detail);
  }
  return data;
}

function hasPermission(code) {
  if (!state.usuario) return false;
  return (PERMISSIONS[state.usuario.perfil] || []).includes(code);
}

function setPageTitle(view) {
  const titles = {
    dashboard: "Achei!",
    postos: "Postos de Apoio",
    itens: "Itens",
    retiradas: "Termos de Retirada",
    relatorios: "Relatório por Posto",
  };
  $("#pageTitle").textContent = titles[view] || "Achei!";
}

function switchView(view) {
  const target = $(`#${view}`);
  if (!target) return;
  $$(".nav-link").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
  $$(".view").forEach((section) => section.classList.remove("active-view"));
  target.classList.add("active-view");
  setPageTitle(view);
}

function setupNavigation() {
  $$(".nav-link").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });
}

function applyPermissions() {
  if (!state.usuario) return;
  $("#userName").textContent = state.usuario.nome;
  $("#userRole").textContent = state.usuario.perfil;

  $$('[data-permission]').forEach((el) => {
    el.classList.toggle("hidden", !hasPermission(el.dataset.permission));
  });

  $$('[data-view-permission]').forEach((el) => {
    el.classList.toggle("hidden", !hasPermission(el.dataset.viewPermission));
  });

  const active = $(".nav-link.active");
  if (active?.classList.contains("hidden")) switchView("dashboard");
  renderPermissionCards();
}

function renderPermissionCards() {
  const container = $("#permissionCards");
  if (!container) return;
  container.innerHTML = FUNCTIONALITIES.map(([code, label, title]) => {
    const allowed = hasPermission(code);
    return `
      <article class="permission-card ${allowed ? "allowed" : "denied"}">
        <strong>${label}: ${escapeHtml(title)}</strong>
        <span>${allowed ? "Permitido" : "Bloqueado"}</span>
      </article>
    `;
  }).join("");
}

function showLogin() {
  $("#loginScreen").classList.remove("hidden");
  $("#appShell").classList.add("hidden");
}

function showApp() {
  $("#loginScreen").classList.add("hidden");
  $("#appShell").classList.remove("hidden");
  applyPermissions();
  switchView("dashboard");
  loadAll(false);
}

function statusClass(status) {
  if (status === "Perdido") return "perdido";
  if (status === "Disponível para Retirada") return "disponivel";
  return "retornado";
}

function renderSelectPostos() {
  const options = state.postos
    .map((posto) => `<option value="${posto.id_posto}">${escapeHtml(posto.nome)} — ${escapeHtml(posto.local)}</option>`)
    .join("");
  const placeholder = '<option value="">Selecione um posto</option>';
  ["#itemEntreguePosto", "#retiradaPosto", "#relatorioPosto"].forEach((selector) => {
    const el = $(selector);
    if (el) el.innerHTML = placeholder + options;
  });
  const filtro = $("#filtroPosto");
  if (filtro) filtro.innerHTML = '<option value="">Todos os postos</option>' + options;
}

function renderSelectItensDisponiveis() {
  const disponiveis = state.itens.filter((item) => item.status === "Disponível para Retirada");
  const select = $("#retiradaItem");
  if (!select) return;
  if (!disponiveis.length) {
    select.innerHTML = '<option value="">Nenhum item disponível</option>';
    return;
  }
  select.innerHTML = '<option value="">Selecione um item</option>' + disponiveis.map((item) => {
    const posto = item.posto_nome || `Posto ${item.fk_posto}`;
    return `<option value="${item.id_item}" data-posto="${item.fk_posto}">#${item.id_item} — ${escapeHtml(item.descricao)} (${escapeHtml(posto)})</option>`;
  }).join("");
}

function renderPostos() {
  const tbody = $("#postosTabela");
  if (!tbody) return;
  if (!state.postos.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Nenhum posto cadastrado.</td></tr>';
    return;
  }

  tbody.innerHTML = state.postos.map((posto) => `
    <tr>
      <td>${posto.id_posto}</td>
      <td><strong>${escapeHtml(posto.nome)}</strong></td>
      <td>${escapeHtml(posto.local)}</td>
      <td>${escapeHtml(posto.horario)}</td>
      <td>${posto.quantidade_itens_disponiveis ?? 0}</td>
      <td>
        <div class="actions">
          ${hasPermission("rf04") ? `<button class="btn small secondary" type="button" data-edit-posto="${posto.id_posto}">Editar</button>` : ""}
          ${hasPermission("rf05") ? `<button class="btn small danger" type="button" data-delete-posto="${posto.id_posto}">Excluir</button>` : ""}
          ${(!hasPermission("rf04") && !hasPermission("rf05")) ? "—" : ""}
        </div>
      </td>
    </tr>
  `).join("");
}

function filteredItens() {
  const status = $("#filtroStatus")?.value || "";
  const posto = $("#filtroPosto")?.value || "";
  return state.itens.filter((item) => {
    const statusOk = !status || item.status === status;
    const postoOk = !posto || String(item.fk_posto || "") === posto;
    return statusOk && postoOk;
  });
}

function renderItens() {
  const tbody = $("#itensTabela");
  if (!tbody) return;
  const itens = filteredItens();
  if (!itens.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Nenhum item encontrado.</td></tr>';
    return;
  }

  tbody.innerHTML = itens.map((item) => {
    const canDeliverExisting = hasPermission("rf14") && item.status !== "Retornado" && !item.fk_posto;
    const canDelete = hasPermission("rf15") && item.status !== "Retornado";
    return `
      <tr>
        <td>${item.id_item}</td>
        <td><strong>${escapeHtml(item.descricao)}</strong><br><small>${escapeHtml(item.data_registro || "")}</small></td>
        <td>${escapeHtml(item.categoria)}</td>
        <td><span class="status ${statusClass(item.status)}">${escapeHtml(item.status)}</span></td>
        <td>${item.posto_nome ? `${escapeHtml(item.posto_nome)}<br><small>${escapeHtml(item.posto_local || "")}</small>` : "—"}</td>
        <td>
          <div class="actions">
            ${canDeliverExisting ? `<button class="btn small ghost" type="button" data-deliver-item="${item.id_item}">Entregar em posto</button>` : ""}
            ${canDelete ? `<button class="btn small danger" type="button" data-delete-item="${item.id_item}">Excluir</button>` : ""}
            ${(!canDeliverExisting && !canDelete) ? "—" : ""}
          </div>
        </td>
      </tr>
    `;
  }).join("");
}

function renderRetiradas() {
  const tbody = $("#retiradasTabela");
  if (!tbody) return;
  if (!state.retiradas.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-row">Nenhum termo de retirada emitido.</td></tr>';
    return;
  }

  tbody.innerHTML = state.retiradas.map((termo) => `
    <tr>
      <td>${termo.id_termo}</td>
      <td><strong>#${termo.fk_item}</strong><br>${escapeHtml(termo.item_descricao)}</td>
      <td>${escapeHtml(termo.posto_nome)}<br><small>${escapeHtml(termo.posto_local)}</small></td>
      <td>${escapeHtml(termo.cpf_retirante)}</td>
      <td>${escapeHtml(termo.email_retirante)}</td>
      <td>${escapeHtml(termo.data_retirada)}</td>
      <td>
        <div class="actions">
          ${hasPermission("rf08") ? `<button class="btn small secondary" type="button" data-edit-termo="${termo.id_termo}">Corrigir</button>` : ""}
          ${hasPermission("rf09") ? `<button class="btn small danger" type="button" data-delete-termo="${termo.id_termo}">Excluir</button>` : ""}
          ${(!hasPermission("rf08") && !hasPermission("rf09")) ? "—" : ""}
        </div>
      </td>
    </tr>
  `).join("");
}

function renderDashboard() {
  $("#statPostos").textContent = state.postos.length;
  $("#statItens").textContent = state.itens.length;
  $("#statDisponiveis").textContent = state.itens.filter((i) => i.status === "Disponível para Retirada").length;
  $("#statRetiradas").textContent = state.retiradas.length;
}

function renderRelatorioInicial() {
  const tbody = $("#relatorioTabela");
  if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="empty-row">Selecione um posto e clique em gerar relatório.</td></tr>';
  const resumo = $("#relatorioResumo");
  if (resumo) resumo.textContent = "";
}

function renderAll() {
  renderSelectPostos();
  renderSelectItensDisponiveis();
  renderPostos();
  renderItens();
  renderRetiradas();
  renderDashboard();
  renderPermissionCards();
  applyPermissions();
}

async function loadPostos() { state.postos = await request("/postos"); }
async function loadItens() { state.itens = await request("/itens"); }
async function loadRetiradas() { state.retiradas = await request("/retiradas"); }

async function loadAll(showMessage = false) {
  try {
    const tarefas = [loadPostos(), loadItens()];
    if (hasPermission("rf07")) tarefas.push(loadRetiradas());
    else state.retiradas = [];
    await Promise.all(tarefas);
    renderAll();
    if (showMessage) toast("Dados atualizados com sucesso.");
  } catch (error) {
    toast(`Não foi possível carregar os dados: ${error.message}`, "error");
  }
}

function resetPostoForm() {
  $("#postoId").value = "";
  $("#postoNome").value = "";
  $("#postoLocal").value = "";
  $("#postoHorario").value = "";
  $("#postoFormTitle").textContent = "Cadastrar posto";
  $("#btnCancelarPosto").classList.add("hidden");
}

function setupLogin() {
  $("#apiBase").value = state.apiBase;

  $$(".demo-user").forEach((button) => {
    button.addEventListener("click", () => {
      $("#loginEmail").value = button.dataset.email;
      $("#loginSenha").value = button.dataset.senha;
      toast(`Credenciais de ${button.textContent} preenchidas.`, "info");
    });
  });

  $("#btnTestarApi").addEventListener("click", async () => {
    try {
      state.apiBase = $("#apiBase").value.trim();
      localStorage.setItem("achei_api_base", state.apiBase);
      await request("/health");
      $("#apiStatus").textContent = "API conectada com sucesso.";
    } catch (error) {
      $("#apiStatus").textContent = `Falha ao conectar: ${error.message}`;
    }
  });

  $("#formLogin").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      state.apiBase = $("#apiBase").value.trim();
      localStorage.setItem("achei_api_base", state.apiBase);
      const usuario = await request("/auth/login", {
        method: "POST",
        body: { email: $("#loginEmail").value, senha: $("#loginSenha").value },
      });
      state.usuario = usuario;
      localStorage.setItem("achei_usuario", JSON.stringify(usuario));
      showApp();
      toast(`Bem-vindo, ${usuario.nome}.`);
    } catch (error) {
      toast(`Login não realizado: ${error.message}`, "error");
    }
  });

  $("#btnSair").addEventListener("click", () => {
    state.usuario = null;
    localStorage.removeItem("achei_usuario");
    showLogin();
  });
}

function setupForms() {
  $("#formPosto").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!hasPermission("rf02") && !hasPermission("rf04")) return;
    const id = $("#postoId").value;
    const body = { nome: $("#postoNome").value, local: $("#postoLocal").value, horario: $("#postoHorario").value };
    try {
      if (id) await request(`/postos/${id}`, { method: "PUT", body });
      else await request("/postos", { method: "POST", body });
      resetPostoForm();
      await loadAll();
      toast(id ? "Posto atualizado." : "Posto cadastrado.");
    } catch (error) { toast(error.message, "error"); }
  });

  $("#btnCancelarPosto").addEventListener("click", resetPostoForm);

  $("#formItemPerdido").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!hasPermission("rf10")) return;
    try {
      await request("/itens/perdidos", {
        method: "POST",
        body: { descricao: $("#itemPerdidoDescricao").value, categoria: $("#itemPerdidoCategoria").value },
      });
      event.target.reset();
      await loadAll();
      toast("Item perdido registrado.");
    } catch (error) { toast(error.message, "error"); }
  });

  $("#formItemEntregue").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!hasPermission("rf14")) return;
    try {
      await request("/itens/entregues", {
        method: "POST",
        body: {
          descricao: $("#itemEntregueDescricao").value,
          categoria: $("#itemEntregueCategoria").value,
          id_posto: Number($("#itemEntreguePosto").value),
        },
      });
      event.target.reset();
      await loadAll();
      toast("Entrega em posto registrada.");
    } catch (error) { toast(error.message, "error"); }
  });

  $("#formRetirada").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!hasPermission("rf06")) return;
    try {
      await request("/retiradas", {
        method: "POST",
        body: {
          id_item: Number($("#retiradaItem").value),
          id_posto: Number($("#retiradaPosto").value),
          cpf_retirante: $("#retiradaCpf").value,
          email_retirante: $("#retiradaEmail").value,
        },
      });
      event.target.reset();
      await loadAll();
      toast("Termo de retirada registrado.");
    } catch (error) { toast(error.message, "error"); }
  });
}

function setupTablesAndFilters() {
  $("#filtroStatus").addEventListener("change", renderItens);
  $("#filtroPosto").addEventListener("change", renderItens);

  $$('[data-status-quick]').forEach((button) => {
    button.addEventListener("click", () => {
      $("#filtroStatus").value = button.dataset.statusQuick;
      renderItens();
    });
  });

  $("#retiradaItem").addEventListener("change", () => {
    const selected = $("#retiradaItem").selectedOptions[0];
    const posto = selected?.dataset?.posto;
    if (posto) $("#retiradaPosto").value = posto;
  });

  document.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    if (target.matches("[data-refresh]")) {
      await loadAll(true);
    }

    const editPosto = target.dataset.editPosto;
    if (editPosto) {
      const posto = state.postos.find((p) => String(p.id_posto) === editPosto);
      if (!posto) return;
      $("#postoId").value = posto.id_posto;
      $("#postoNome").value = posto.nome;
      $("#postoLocal").value = posto.local;
      $("#postoHorario").value = posto.horario;
      $("#postoFormTitle").textContent = `Atualizar posto #${posto.id_posto}`;
      $("#btnCancelarPosto").classList.remove("hidden");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    const deletePosto = target.dataset.deletePosto;
    if (deletePosto && confirm("Excluir este posto de apoio?")) {
      try {
        await request(`/postos/${deletePosto}`, { method: "DELETE" });
        await loadAll();
        toast("Posto excluído.");
      } catch (error) { toast(error.message, "error"); }
    }

    const deliverItem = target.dataset.deliverItem;
    if (deliverItem) {
      const posto = prompt("Informe o ID do posto de apoio para vincular este item:");
      if (!posto) return;
      try {
        await request(`/itens/${deliverItem}/entrega`, { method: "PATCH", body: { id_posto: Number(posto) } });
        await loadAll();
        toast("Item vinculado ao posto.");
      } catch (error) { toast(error.message, "error"); }
    }

    const deleteItem = target.dataset.deleteItem;
    if (deleteItem && confirm("Excluir este item?")) {
      try {
        await request(`/itens/${deleteItem}`, { method: "DELETE" });
        await loadAll();
        toast("Item excluído.");
      } catch (error) { toast(error.message, "error"); }
    }

    const editTermo = target.dataset.editTermo;
    if (editTermo) {
      const termo = state.retiradas.find((t) => String(t.id_termo) === editTermo);
      if (!termo) return;
      const cpf = prompt("CPF corrigido:", termo.cpf_retirante);
      if (cpf === null) return;
      const email = prompt("E-mail corrigido:", termo.email_retirante);
      if (email === null) return;
      try {
        await request(`/retiradas/${editTermo}`, { method: "PUT", body: { cpf_retirante: cpf, email_retirante: email } });
        await loadAll();
        toast("Termo atualizado.");
      } catch (error) { toast(error.message, "error"); }
    }

    const deleteTermo = target.dataset.deleteTermo;
    if (deleteTermo && confirm("Excluir termo e reverter item para disponível?")) {
      try {
        await request(`/retiradas/${deleteTermo}`, { method: "DELETE" });
        await loadAll();
        toast("Termo excluído e item revertido.");
      } catch (error) { toast(error.message, "error"); }
    }
  });
}

function setupRelatorio() {
  $("#btnGerarRelatorio").addEventListener("click", async () => {
    const idPosto = $("#relatorioPosto").value;
    const tbody = $("#relatorioTabela");
    const resumo = $("#relatorioResumo");
    if (!idPosto) {
      toast("Selecione um posto para gerar o relatório.", "error");
      return;
    }
    try {
      const itens = await request(`/postos/${idPosto}/itens`);
      const posto = state.postos.find((p) => String(p.id_posto) === String(idPosto));
      resumo.textContent = `${itens.length} registro(s) encontrado(s) para ${posto?.nome || "o posto selecionado"}.`;
      if (!itens.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-row">Nenhum item vinculado a este posto.</td></tr>';
        return;
      }
      tbody.innerHTML = itens.map((item) => `
        <tr>
          <td>${item.id_item}</td>
          <td><strong>${escapeHtml(item.descricao)}</strong></td>
          <td>${escapeHtml(item.categoria)}</td>
          <td><span class="status ${statusClass(item.status)}">${escapeHtml(item.status)}</span></td>
          <td>${escapeHtml(item.data_registro || "")}</td>
        </tr>
      `).join("");
    } catch (error) { toast(error.message, "error"); }
  });
}

function setupTopbar() {
  $("#btnAtualizarTudo").addEventListener("click", () => loadAll(true));
}

function init() {
  setupLogin();
  setupNavigation();
  setupForms();
  setupTablesAndFilters();
  setupRelatorio();
  setupTopbar();
  renderRelatorioInicial();
  if (state.usuario) showApp();
  else showLogin();
}

document.addEventListener("DOMContentLoaded", init);
