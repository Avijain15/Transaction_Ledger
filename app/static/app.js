const $ = (selector) => document.querySelector(selector);
const state = { historyAccountId: "", page: 1, limit: 10, type: "", totalPages: 0 };

function showMessage(selector, message, kind = "") {
  const element = $(selector);
  element.textContent = message;
  element.className = `message ${kind}`;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body?.error?.message || "The request failed");
  return body;
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function renderHistory(result) {
  const list = $("#history-list");
  list.replaceChildren();
  if (!result.data.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No transactions found for this account.";
    list.append(empty);
  }
  for (const item of result.data) {
    const row = document.createElement("div");
    row.className = "history-row";
    const detail = document.createElement("div");
    const title = document.createElement("p");
    title.className = "entry-title";
    title.textContent = item.description;
    const meta = document.createElement("p");
    meta.className = "entry-meta";
    meta.textContent = `${item.type} · Ref ${item.reference_id} · ${new Date(item.created_at).toLocaleString()}`;
    detail.append(title, meta);
    const amount = document.createElement("span");
    amount.className = `entry-amount ${item.type}`;
    amount.textContent = `${item.type === "credit" ? "+" : "−"}${item.amount}`;
    row.append(detail, amount);
    list.append(row);
  }
  const pageInfo = result.pagination;
  state.totalPages = pageInfo.total_pages;
  state.page = pageInfo.page;
  $("#page-label").textContent = `Page ${pageInfo.page} of ${pageInfo.total_pages} · ${pageInfo.total_records} records`;
  $("#previous").disabled = pageInfo.page <= 1;
  $("#next").disabled = pageInfo.page >= pageInfo.total_pages;
}

async function loadHistory() {
  if (!state.historyAccountId) return;
  const params = new URLSearchParams({ page: String(state.page), limit: String(state.limit) });
  if (state.type) params.set("type", state.type);
  try {
    const result = await request(`/accounts/${encodeURIComponent(state.historyAccountId)}/transactions?${params}`);
    renderHistory(result);
    showMessage("#history-message", "");
  } catch (error) {
    showMessage("#history-message", error.message, "error");
  }
}

$("#create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await request("/accounts", { method: "POST", body: JSON.stringify(formData(event.currentTarget)) });
    showMessage("#create-message", `Account created · ID ${result.id} · opening balance ${result.balance}`, "success");
  } catch (error) { showMessage("#create-message", error.message, "error"); }
});

$("#balance-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { account_id: accountId } = formData(event.currentTarget);
  try {
    const result = await request(`/accounts/${encodeURIComponent(accountId)}/balance`);
    $("#balance-result").textContent = result.balance;
    showMessage("#balance-message", `Account ${result.account_id}`, "success");
  } catch (error) { $("#balance-result").textContent = "—"; showMessage("#balance-message", error.message, "error"); }
});

$("#transaction-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = formData(event.currentTarget);
  const { account_id: accountId, ...body } = data;
  try {
    const result = await request(`/accounts/${encodeURIComponent(accountId)}/transactions`, { method: "POST", body: JSON.stringify(body) });
    showMessage("#transaction-message", `Transaction ${result.id} recorded.`, "success");
  } catch (error) { showMessage("#transaction-message", error.message, "error"); }
});

$("#history-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.historyAccountId = formData(event.currentTarget).account_id;
  state.page = 1;
  await loadHistory();
});

document.querySelectorAll(".segment").forEach((button) => button.addEventListener("click", async () => {
  document.querySelectorAll(".segment").forEach((segment) => segment.classList.toggle("active", segment === button));
  state.type = button.dataset.type;
  state.page = 1;
  await loadHistory();
}));

$("#previous").addEventListener("click", async () => { state.page = Math.max(1, state.page - 1); await loadHistory(); });
$("#next").addEventListener("click", async () => { state.page += 1; await loadHistory(); });

$("#transfer-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = formData(event.currentTarget);
  data.from_account_id = Number(data.from_account_id);
  data.to_account_id = Number(data.to_account_id);
  try {
    const result = await request("/transfers", { method: "POST", body: JSON.stringify(data) });
    showMessage("#transfer-message", `Transfer recorded · ${result.from_transaction.id} → ${result.to_transaction.id}`, "success");
  } catch (error) { showMessage("#transfer-message", error.message, "error"); }
});
