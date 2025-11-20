const API_BASE_URL = "https://jgn7wje6q2.execute-api.ap-south-1.amazonaws.com/prod";

const $ = (id) => document.getElementById(id);
const outStatus = $("status");
const table = $("resultTable");
const cellCustomer = $("cellCustomer");
const cellCount = $("cellCount");
const cellSum = $("cellSum");
const btn = $("callBtn");

function formatAmount(num) {
  if (typeof num !== "number") return String(num);
  return Number(num).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

btn.addEventListener("click", async () => {
  const customerId = $("customerId").value.trim();
  const authToken  = $("authToken").value.trim();

  table.style.display = "none";
  outStatus.className = "status";
  outStatus.textContent = "";

  if (!customerId || !authToken) {
    outStatus.classList.add("err");
    outStatus.textContent = "Please enter both Customer ID and Access Token.";
    return;
  }

  btn.disabled = true;
  btn.textContent = "Checking…";

  try {
    const res = await fetch(`${API_BASE_URL}/Details`, {
      method: "GET",
      headers: {
        "auth_token": authToken,
        "customer_id": customerId  
      },
      mode: "cors",
    });

    const text = await res.text();
    let body;
    try { body = JSON.parse(text); } catch { body = text; }

    if (!res.ok) {
      outStatus.classList.add("err");
      outStatus.textContent = body?.message || `Request failed (${res.status}).`;
      return;
    }

    outStatus.classList.add("ok");
    outStatus.textContent = "Fetched successfully.";

    cellCustomer.textContent = body.customer_id ?? customerId;
    cellCount.textContent = body.transaction_count ?? "0";
    cellSum.textContent = formatAmount(body.total_amount ?? 0);

    table.style.display = "table";

  } catch (e) {
    outStatus.classList.add("err");
    outStatus.textContent = "Network error. Please try again.";
  } finally {
    btn.disabled = false;
    btn.textContent = "Check Transactions";
  }
});
