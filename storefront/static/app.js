const money = cents => new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(cents / 100);
const cart = new Map();
let products = [];
let currentQuote = null;
let requestVersion = 0;
const byId = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Unable to load Storefront');
  return data;
}
function sock(color) {
  const fill = {cream: '#f9f6ec', orange: '#dc7644', ink: '#283e49'}[color];
  return `<svg viewBox="0 0 160 220" aria-hidden="true"><g transform="rotate(12 80 110)"><path d="M45 20h60v104l35 32c24 22 4 50-22 39l-51-23c-14-6-22-20-22-37Z" fill="${fill}" stroke="#172c39" stroke-width="1.5"/><path d="M46 32h58v7H46zm0 14h58v6H46" fill="${color === 'ink' ? '#e9ddc2' : '#172c39'}"/><path d="M46 119h58v10l-28 43-9 0c-14-6-22-20-22-37Z" fill="#172c39" opacity=".12"/><path d="m128 145 12 11c24 22 4 50-22 39l-12-5Z" fill="#172c39" opacity=".18"/></g></svg>`;
}
function renderProducts() {
  byId('products').innerHTML = products.map(product => `<article class="product"><div class="product-art ${escapeHTML(product.accent)}"><span class="tag">${escapeHTML(product.tag)}</span>${sock(product.accent)}</div><div class="product-title"><h3>${escapeHTML(product.name)}</h3><span>${money(product.price_cents)}</span></div><span class="color">${escapeHTML(product.color)}</span><p>${escapeHTML(product.description)}</p><button class="add" data-add="${escapeHTML(product.sku)}">Add a pair <span>+</span></button></article>`).join('');
}
function renderCart() {
  byId('cart-lines').innerHTML = [...cart].map(([sku, quantity]) => {
    const product = products.find(p => p.sku === sku);
    return `<div class="cart-line"><div><strong>${escapeHTML(product.name)}</strong><small>${escapeHTML(product.color)}</small><div class="quantity"><button data-quantity="${escapeHTML(sku)}" data-change="-1" aria-label="Remove one ${escapeHTML(product.name)}">−</button><span>${quantity}</span><button data-quantity="${escapeHTML(sku)}" data-change="1" aria-label="Add one ${escapeHTML(product.name)}" ${quantity >= 20 ? 'disabled' : ''}>+</button></div></div><span>${money(product.price_cents * quantity)}</span></div>`;
  }).join('') || '<p class="empty">Your bag is empty. Find your next favorite pair.</p>';
  const count = [...cart.values()].reduce((sum, quantity) => sum + quantity, 0);
  byId('bag-count').textContent = `${count} ${count === 1 ? 'pair' : 'pairs'}`;
}
function totals(quote) {
  return `<div class="total-line"><span>Subtotal</span><span>${money(quote.subtotal_cents)}</span></div><div class="total-line"><span>Shipping</span><strong>${quote.shipping_cents === 0 ? 'Free' : money(quote.shipping_cents)}</strong></div><div class="total-line final"><span>Total <small>USD</small></span><span>${money(quote.total_cents)}</span></div>`;
}
async function updateQuote() {
  const version = ++requestVersion;
  currentQuote = null;
  byId('review').disabled = true;
  byId('error').textContent = '';
  renderCart();
  if (!cart.size) { byId('totals').innerHTML = ''; return; }
  byId('totals').textContent = 'Updating checkout…';
  try {
    const quote = await api('/api/quote', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({items: [...cart].map(([sku, quantity]) => ({sku, quantity})), is_vip: byId('vip').checked})});
    if (version !== requestVersion) return;
    currentQuote = quote;
    byId('totals').innerHTML = totals(quote);
    byId('review').disabled = false;
  } catch (error) {
    if (version !== requestVersion) return;
    byId('error').textContent = error.message;
    byId('totals').textContent = '';
  }
}
document.addEventListener('click', event => {
  const add = event.target.closest('[data-add]');
  const quantity = event.target.closest('[data-quantity]');
  if (add || quantity) {
    const sku = add ? add.dataset.add : quantity.dataset.quantity;
    const count = Math.min(20, Math.max(0, (cart.get(sku) || 0) + (add ? 1 : Number(quantity.dataset.change))));
    if (count) cart.set(sku, count); else cart.delete(sku);
    updateQuote();
  }
});
byId('vip').addEventListener('change', updateQuote);
for (const name of ['shop', 'orders']) byId(`${name}-tab`).addEventListener('click', () => {
  for (const other of ['shop', 'orders']) {
    byId(`${other}-panel`).hidden = other !== name;
    byId(`${other}-tab`).classList.toggle('active', other === name);
    byId(`${other}-tab`).setAttribute('aria-pressed', String(other === name));
  }
});
byId('review').addEventListener('click', () => {
  if (!currentQuote) return;
  byId('preview-details').innerHTML = currentQuote.items.map(item => `<p>${item.quantity} × ${escapeHTML(item.name)} <strong>${money(item.line_total_cents)}</strong></p>`).join('') + totals(currentQuote);
  byId('order-preview').showModal();
});
byId('close-preview').addEventListener('click', () => byId('order-preview').close());
(async () => {
  try {
    const [catalog, orders] = await Promise.all([api('/api/catalog'), api('/api/orders')]);
    products = catalog;
    renderProducts();
    renderCart();
    byId('order-count').textContent = orders.length;
    byId('orders').innerHTML = orders.map(order => `<tr><td><strong>${escapeHTML(order.id)}</strong><small>${escapeHTML(order.customer)}</small></td><td>${order.items.map(item => `${item.quantity} × ${escapeHTML(item.name)}`).join('<br>')}</td><td><span class="badge ${order.is_vip ? 'vip-badge' : ''}">${order.is_vip ? 'VIP' : 'Standard'}</span></td><td>${order.shipping_cents === 0 ? 'Free' : money(order.shipping_cents)}</td><td><strong>${money(order.total_cents)}</strong></td><td><span class="badge">${escapeHTML(order.status)}</span></td></tr>`).join('');
  } catch (error) { byId('error').textContent = error.message; }
})();
