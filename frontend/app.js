const state = {
  mode: "login",
  token: localStorage.getItem("token") || "",
  user: JSON.parse(localStorage.getItem("user") || "null"),
  products: [],
};

const statusEl = document.querySelector("#status");
const authForm = document.querySelector("#auth-form");
const loginTab = document.querySelector("#login-tab");
const registerTab = document.querySelector("#register-tab");
const emailField = document.querySelector("#email-field");
const nameField = document.querySelector("#name-field");
const authSubmit = document.querySelector("#auth-submit");
const productsEl = document.querySelector("#products");
const productSelect = document.querySelector("#product-select");
const orderForm = document.querySelector("#order-form");
const orderResult = document.querySelector("#order-result");

function setMode(mode) {
  state.mode = mode;
  loginTab.classList.toggle("active", mode === "login");
  registerTab.classList.toggle("active", mode === "register");
  emailField.classList.toggle("hidden", mode !== "register");
  nameField.classList.toggle("hidden", mode !== "register");
  authSubmit.textContent = mode === "login" ? "Login" : "Register";
}

function updateStatus() {
  statusEl.textContent = state.user ? `Logged in as ${state.user.username}` : "Not logged in";
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(path, { ...options, headers });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || "Request failed");
  }
  return data;
}

async function loadProducts() {
  state.products = await api("/api/products");
  productsEl.innerHTML = "";
  productSelect.innerHTML = "";

  for (const product of state.products) {
    const card = document.createElement("article");
    card.className = "product";
    card.innerHTML = `
      <h3>${product.name}</h3>
      <p>${product.description || ""}</p>
      <div class="price">$${product.price}</div>
      <div>Stock: ${product.stock}</div>
    `;
    productsEl.appendChild(card);

    const option = document.createElement("option");
    option.value = product.id;
    option.textContent = `${product.name} ($${product.price})`;
    productSelect.appendChild(option);
  }
}

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.querySelector("#username").value;
  const password = document.querySelector("#password").value;
  const path = state.mode === "login" ? "/api/auth/login" : "/api/auth/register";
  const payload = { username, password };

  if (state.mode === "register") {
    payload.email = document.querySelector("#email").value;
    payload.full_name = document.querySelector("#full-name").value;
  }

  try {
    const result = await api(path, { method: "POST", body: JSON.stringify(payload) });
    state.token = result.access_token;
    state.user = result.user;
    localStorage.setItem("token", state.token);
    localStorage.setItem("user", JSON.stringify(state.user));
    updateStatus();
  } catch (error) {
    statusEl.textContent = error.message;
  }
});

orderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/api/orders", {
      method: "POST",
      body: JSON.stringify({
        items: [
          {
            product_id: Number(productSelect.value),
            quantity: Number(document.querySelector("#quantity").value),
          },
        ],
      }),
    });
    orderResult.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    orderResult.textContent = error.message;
  }
});

loginTab.addEventListener("click", () => setMode("login"));
registerTab.addEventListener("click", () => setMode("register"));
document.querySelector("#refresh-products").addEventListener("click", loadProducts);

setMode("login");
updateStatus();
loadProducts().catch((error) => {
  productsEl.textContent = error.message;
});
