// CaféGo Comprehensive Client-Side Application Script

// --- LOCAL STORAGE CART ENGINE ---
function getCart() {
  try {
    return JSON.parse(localStorage.getItem("cafe_cart") || "[]");
  } catch (e) {
    return [];
  }
}

function saveCart(cart) {
  localStorage.setItem("cafe_cart", JSON.stringify(cart));
  updateCartBadge();
}

function updateCartBadge() {
  const badge = document.getElementById("count");
  if (badge) {
    const totalQty = getCart().reduce((sum, item) => sum + (parseInt(item.quantity) || 0), 0);
    badge.textContent = totalQty;
    badge.style.display = totalQty > 0 ? "inline-block" : "none";
  }
}

function clearCart() {
  localStorage.removeItem("cafe_cart");
  updateCartBadge();
}

function addToCart(item) {
  const cart = getCart();
  // Find matching item with same ID, spice level, and addons
  const existing = cart.find(x => 
    x.item_id === item.item_id &&
    x.spice_level === item.spice_level &&
    JSON.stringify(x.addons_selected) === JSON.stringify(item.addons_selected) &&
    (x.customization || "").trim() === (item.customization || "").trim()
  );

  if (existing) {
    existing.quantity = (parseInt(existing.quantity) || 1) + (item.quantity || 1);
  } else {
    cart.push(item);
  }

  saveCart(cart);
}

function updateItemQuantity(index, delta) {
  const cart = getCart();
  if (cart[index]) {
    cart[index].quantity += delta;
    if (cart[index].quantity <= 0) {
      cart.splice(index, 1);
    }
    saveCart(cart);
    renderCartPage();
    renderCheckoutSummary();
  }
}

function removeCartItem(index) {
  const cart = getCart();
  cart.splice(index, 1);
  saveCart(cart);
  renderCartPage();
  renderCheckoutSummary();
}

// --- CUSTOMIZATION MODAL ENGINE ---
let activeModalItem = null;
let currentSpice = "";
let currentAddons = [];

function openCustomModal(itemData) {
  activeModalItem = itemData;
  currentSpice = "";
  currentAddons = [];

  const modal = document.getElementById("customModal");
  if (!modal) return;

  document.getElementById("modalTitle").textContent = itemData.name;
  document.getElementById("modalBasePrice").textContent = `Base: ₹${itemData.price.toFixed(2)}`;
  document.getElementById("modalDesc").textContent = itemData.description || "";
  document.getElementById("modalImg").src = itemData.image_url;

  // Render Spice Levels
  const spiceContainer = document.getElementById("modalSpiceContainer");
  const spiceSection = document.getElementById("modalSpiceSection");
  spiceContainer.innerHTML = "";
  
  if (itemData.options && itemData.options.spice_levels && itemData.options.spice_levels.length > 0) {
    spiceSection.style.display = "block";
    currentSpice = itemData.options.spice_levels[0]; // default
    itemData.options.spice_levels.forEach((spice, idx) => {
      const pill = document.createElement("div");
      pill.className = `spice-pill ${idx === 0 ? "selected" : ""}`;
      pill.textContent = spice;
      pill.onclick = () => {
        document.querySelectorAll(".spice-pill").forEach(p => p.classList.remove("selected"));
        pill.classList.add("selected");
        currentSpice = spice;
      };
      spiceContainer.appendChild(pill);
    });
  } else {
    spiceSection.style.display = "none";
  }

  // Render Addons
  const addonContainer = document.getElementById("modalAddonContainer");
  const addonSection = document.getElementById("modalAddonSection");
  addonContainer.innerHTML = "";

  if (itemData.options && itemData.options.addons && itemData.options.addons.length > 0) {
    addonSection.style.display = "block";
    itemData.options.addons.forEach(addon => {
      const row = document.createElement("div");
      row.className = "addon-row";
      row.innerHTML = `
        <label>
          <input type="checkbox" data-name="${addon.name}" data-price="${addon.price}">
          <span>${addon.name}</span>
        </label>
        <b>+₹${addon.price}</b>
      `;
      const checkbox = row.querySelector("input");
      checkbox.onchange = () => {
        if (checkbox.checked) {
          row.classList.add("checked");
        } else {
          row.classList.remove("checked");
        }
        recalcModalTotal();
      };
      addonContainer.appendChild(row);
    });
  } else {
    addonSection.style.display = "none";
  }

  const noteInput = document.getElementById("modalCustomNote");
  if (noteInput) noteInput.value = "";

  recalcModalTotal();
  modal.classList.add("active");
}

function closeCustomModal() {
  const modal = document.getElementById("customModal");
  if (modal) modal.classList.remove("active");
  activeModalItem = null;
}

function recalcModalTotal() {
  if (!activeModalItem) return;
  let totalAddonPrice = 0;
  const checkboxes = document.querySelectorAll("#modalAddonContainer input[type='checkbox']:checked");
  checkboxes.forEach(cb => {
    totalAddonPrice += parseFloat(cb.dataset.price || 0);
  });

  const finalUnitPrice = activeModalItem.price + totalAddonPrice;
  const totalBtn = document.getElementById("modalAddBtn");
  if (totalBtn) {
    totalBtn.textContent = `Add to Order • ₹${finalUnitPrice.toFixed(2)}`;
  }
}

function confirmModalAddToCart() {
  if (!activeModalItem) return;

  const selectedAddons = [];
  let totalAddonPrice = 0;
  const checkboxes = document.querySelectorAll("#modalAddonContainer input[type='checkbox']:checked");
  checkboxes.forEach(cb => {
    selectedAddons.push(cb.dataset.name);
    totalAddonPrice += parseFloat(cb.dataset.price || 0);
  });

  const customNote = document.getElementById("modalCustomNote") ? document.getElementById("modalCustomNote").value.trim() : "";

  addToCart({
    item_id: activeModalItem.item_id,
    name: activeModalItem.name,
    base_price: activeModalItem.price,
    addon_price: totalAddonPrice,
    unit_price: activeModalItem.price + totalAddonPrice,
    quantity: 1,
    spice_level: currentSpice,
    addons_selected: selectedAddons,
    customization: customNote,
    image_url: activeModalItem.image_url
  });

  closeCustomModal();

  // Temporary feedback toast
  showToast(`Added "${activeModalItem.name}" to cart! 🛒`);
}

function showToast(msg) {
  let toast = document.getElementById("appToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "appToast";
    toast.style.position = "fixed";
    toast.style.bottom = "24px";
    toast.style.right = "24px";
    toast.style.background = "#0f172a";
    toast.style.color = "white";
    toast.style.padding = "12px 20px";
    toast.style.borderRadius = "12px";
    toast.style.boxShadow = "0 10px 15px -3px rgba(0,0,0,0.2)";
    toast.style.zIndex = "9999";
    toast.style.fontWeight = "600";
    toast.style.fontSize = "14px";
    toast.style.transition = "all 0.3s ease";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2500);
}

// --- CART PAGE RENDERER ---
function renderCartPage() {
  const container = document.getElementById("cartPageContainer");
  if (!container) return;

  const cart = getCart();
  if (cart.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 50px 20px;">
        <div style="font-size: 50px; margin-bottom: 12px;">🛒</div>
        <h2>Your Cart is Empty</h2>
        <p style="color: var(--text-muted); margin: 10px 0 24px;">Discover chef specials and fresh meals from our digital menu.</p>
        <a href="/menu" class="btn btn-accent">Explore Digital Menu →</a>
      </div>
    `;
    return;
  }

  let subtotal = 0;
  const itemsHtml = cart.map((item, idx) => {
    const itemSubtotal = (parseFloat(item.unit_price) || (item.base_price + (item.addon_price || 0))) * item.quantity;
    subtotal += itemSubtotal;
    
    const addonsLabel = item.addons_selected && item.addons_selected.length > 0 
      ? `<small style="color: var(--accent); font-weight:600;">+ ${item.addons_selected.join(", ")}</small>` 
      : "";
    const spiceLabel = item.spice_level ? `<small style="color: #ef4444; font-weight:600;">🌶️ ${item.spice_level}</small>` : "";
    const noteLabel = item.customization ? `<small style="font-style: italic;">Note: "${item.customization}"</small>` : "";

    return `
      <div class="cart-item-row">
        <div class="cart-item-info">
          <h4>${item.name}</h4>
          <span style="font-weight: 700; color: var(--primary);">₹${(parseFloat(item.unit_price) || item.base_price).toFixed(2)} each</span>
          ${spiceLabel}
          ${addonsLabel}
          ${noteLabel}
        </div>
        <div style="display: flex; align-items: center; gap: 16px;">
          <div class="qty-controls">
            <button class="qty-btn" onclick="updateItemQuantity(${idx}, -1)">−</button>
            <span style="font-weight: 700; width: 24px; text-align: center;">${item.quantity}</span>
            <button class="qty-btn" onclick="updateItemQuantity(${idx}, 1)">+</button>
          </div>
          <div style="font-weight: 800; font-family: 'Outfit'; font-size: 17px; min-width: 70px; text-align: right;">
            ₹${itemSubtotal.toFixed(2)}
          </div>
          <button onclick="removeCartItem(${idx})" class="btn-outline btn-sm" style="color: var(--accent-red); border-color: #fee2e2;">✕</button>
        </div>
      </div>
    `;
  }).join("");

  const tax = subtotal * 0.05; // 5% GST representation
  const grandTotal = subtotal + tax;

  container.innerHTML = `
    <div class="cart-layout">
      <div class="card">
        <div class="card-header">
          <h3>Your Selected Food Items (${cart.length})</h3>
          <button onclick="clearCart(); renderCartPage();" class="btn-outline btn-sm" style="color: var(--accent-red);">Clear Cart</button>
        </div>
        <div>${itemsHtml}</div>
      </div>
      <div>
        <div class="order-summary-box">
          <h3 style="margin-bottom: 16px;">Order Summary</h3>
          <div class="summary-row">
            <span>Subtotal</span>
            <span>₹${subtotal.toFixed(2)}</span>
          </div>
          <div class="summary-row">
            <span>Cafeteria GST (5%)</span>
            <span>₹${tax.toFixed(2)}</span>
          </div>
          <div class="summary-row total">
            <span>Total Payable</span>
            <span>₹${grandTotal.toFixed(2)}</span>
          </div>
          <a href="/checkout" class="btn btn-accent" style="width: 100%; margin-top: 20px; padding: 14px; font-size: 16px;">Proceed to Pre-Order Slot & Payment →</a>
          <a href="/menu" class="btn btn-outline" style="width: 100%; margin-top: 10px;">← Add More Items</a>
        </div>
      </div>
    </div>
  `;
}

// --- CHECKOUT SUMMARY & FORM CONTROLLER ---
function renderCheckoutSummary() {
  const summaryEl = document.getElementById("checkoutSummary");
  if (!summaryEl) return;

  const cart = getCart();
  if (!cart.length) {
    summaryEl.innerHTML = "<p>Your cart is empty. <a href='/menu'>Browse Menu</a></p>";
    return;
  }

  let subtotal = 0;
  let itemsListHtml = cart.map(x => {
    const itemTotal = (parseFloat(x.unit_price) || (x.base_price + (x.addon_price || 0))) * x.quantity;
    subtotal += itemTotal;
    return `
      <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;">
        <span>${x.name} × ${x.quantity}</span>
        <b>₹${itemTotal.toFixed(2)}</b>
      </div>
    `;
  }).join("");

  const tax = subtotal * 0.05;
  const grandTotal = subtotal + tax;

  summaryEl.innerHTML = `
    <div style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 12px;">
      ${itemsListHtml}
    </div>
    <div class="summary-row">
      <span>Items Subtotal</span>
      <span>₹${subtotal.toFixed(2)}</span>
    </div>
    <div class="summary-row">
      <span>GST (5%)</span>
      <span>₹${tax.toFixed(2)}</span>
    </div>
    <div class="summary-row total">
      <span>Total Amount</span>
      <span>₹${grandTotal.toFixed(2)}</span>
    </div>
  `;
}

// --- PAYMENT METHOD DYNAMIC VIEWER ---
function updatePaymentDetailsView(method) {
  const box = document.getElementById("paymentDynamicDetails");
  if (!box) return;

  const cart = getCart();
  const subtotal = cart.reduce((sum, item) => sum + (parseFloat(item.unit_price) || item.base_price) * item.quantity, 0);
  const total = subtotal + (subtotal * 0.05);

  if (method === "UPI") {
    box.innerHTML = `
      <div style="text-align: center; padding: 10px;">
        <p style="font-weight: 600; margin-bottom: 8px;">Scan Dynamic UPI QR to Pay ₹${total.toFixed(2)}</p>
        <div style="background: white; border: 2px solid var(--border); padding: 12px; display: inline-block; border-radius: 12px;">
          <img src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=upi://pay?pa=cafeteria@demo%26pn=CafeGo%26am=${total.toFixed(2)}%26cu=INR" alt="UPI QR Code" style="display:block; width:130px; height:130px;">
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: var(--text-muted);">
          Supports GPay, PhonePe, Paytm, BHIM & all UPI Apps
        </div>
      </div>
    `;
  } else if (method === "Card") {
    box.innerHTML = `
      <div>
        <p style="font-weight: 600; margin-bottom: 8px;">Simulated Card Payment</p>
        <div style="display: grid; gap: 8px;">
          <input type="text" placeholder="Card Number (e.g. 4532 •••• •••• 8921)" value="4532 9821 3491 8921" readonly style="background:#f1f5f9;">
          <div style="display: flex; gap: 8px;">
            <input type="text" placeholder="MM/YY" value="08/28" readonly style="background:#f1f5f9;">
            <input type="password" placeholder="CVV" value="888" readonly style="background:#f1f5f9;">
          </div>
        </div>
        <small style="color: var(--accent); display:block; margin-top:6px;">✓ Demo Mode: Instant Secure Pre-Authorization</small>
      </div>
    `;
  } else if (method === "Wallet") {
    box.innerHTML = `
      <div style="display: flex; gap: 10px; justify-content: center; padding: 10px 0;">
        <span style="background: white; border: 1px solid var(--border); padding: 8px 14px; border-radius: 8px; font-weight:600;">Paytm Wallet</span>
        <span style="background: white; border: 1px solid var(--border); padding: 8px 14px; border-radius: 8px; font-weight:600;">PhonePe</span>
        <span style="background: white; border: 1px solid var(--border); padding: 8px 14px; border-radius: 8px; font-weight:600;">Amazon Pay</span>
      </div>
    `;
  } else if (method === "Cafeteria Credit") {
    box.innerHTML = `
      <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 12px; border-radius: 10px; color: #065f46;">
        <b>Student / Staff ID Credit Balance: ₹500.00</b>
        <p style="font-size: 13px; margin-top: 4px;">₹${total.toFixed(2)} will be debited directly from your campus ID card.</p>
      </div>
    `;
  }
}

// --- REAL-TIME LIVE TRACKING POLLER & NOTIFICATIONS ---
let trackingInterval = null;
let lastKnownStatus = "";

function requestNotificationPermission() {
  if ("Notification" in window) {
    Notification.requestPermission().then(perm => {
      const btn = document.getElementById("notifPermBtn");
      if (btn) {
        if (perm === "granted") {
          btn.textContent = "🔔 Push Notifications Enabled";
          btn.classList.remove("btn-outline");
          btn.classList.add("btn-accent");
        } else {
          btn.textContent = "🔕 Notifications Denied";
        }
      }
    });
  }
}

function playAlertChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.15); // A5
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.5);
  } catch (e) {
    // Audio context may require initial interaction
  }
}

function triggerDesktopNotification(orderId, status) {
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification(`CaféGo Order #${orderId}`, {
      body: `Status Update: Your order is now "${status}"! ☕`,
      icon: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=100"
    });
  }
  playAlertChime();
}

function initLiveOrderTracking(orderId, initialStatus) {
  lastKnownStatus = initialStatus;
  
  if (trackingInterval) clearInterval(trackingInterval);

  trackingInterval = setInterval(() => {
    fetch(`/api/orders/${orderId}`)
      .then(res => res.json())
      .then(data => {
        if (data.order_id) {
          updateTrackingUI(data);
          
          if (data.status !== lastKnownStatus) {
            triggerDesktopNotification(orderId, data.status);
            showToast(`Order #${orderId} is now ${data.status}! 🔔`);
            lastKnownStatus = data.status;
          }
          
          if (data.status === "Completed" || data.status === "Cancelled") {
            clearInterval(trackingInterval);
          }
        }
      })
      .catch(err => console.log("Tracking poll err:", err));
  }, 3500);
}

function updateTrackingUI(data) {
  // Update status pill
  const pill = document.getElementById("trackingStatusPill");
  if (pill) {
    pill.innerHTML = `<span class="pulsing-dot"></span> Status: ${data.status}`;
  }

  // Update stepper line
  const progressLine = document.getElementById("stepperLineProgress");
  if (progressLine) {
    progressLine.style.width = `${data.progress_percent}%`;
  }

  // Update step bubbles
  const stages = ["Received", "Preparing", "Ready for Pickup", "Completed"];
  const currentIdx = stages.indexOf(data.status);

  stages.forEach((st, idx) => {
    const stepEl = document.getElementById(`step-${idx}`);
    if (stepEl) {
      stepEl.classList.remove("active", "completed");
      if (idx < currentIdx) {
        stepEl.classList.add("completed");
      } else if (idx === currentIdx) {
        stepEl.classList.add("active");
      }
    }
  });

  if (data.status === "Ready for Pickup") {
    const banner = document.getElementById("readyPickupBanner");
    if (banner) banner.style.display = "block";
  }
}

// --- DOM READY INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
  updateCartBadge();
  renderCartPage();
  renderCheckoutSummary();

  // Bind Checkout Form Submit
  const checkoutForm = document.getElementById("checkoutOrderForm");
  if (checkoutForm) {
    // Initial payment view
    const initialMethod = document.querySelector("input[name='payment_method']:checked")?.value || "UPI";
    updatePaymentDetailsView(initialMethod);

    document.querySelectorAll("input[name='payment_method']").forEach(radio => {
      radio.addEventListener("change", (e) => {
        updatePaymentDetailsView(e.target.value);
      });
    });

    checkoutForm.addEventListener("submit", (e) => {
      const cart = getCart();
      if (!cart.length) {
        e.preventDefault();
        alert("Your cart is empty! Please select items first.");
        window.location.href = "/menu";
        return;
      }

      // Populate hidden cart_data input
      let cartInput = document.getElementById("hiddenCartData");
      if (!cartInput) {
        cartInput = document.createElement("input");
        cartInput.type = "hidden";
        cartInput.id = "hiddenCartData";
        cartInput.name = "cart_data";
        checkoutForm.appendChild(cartInput);
      }
      cartInput.value = JSON.stringify(cart);

      // Save user email to localStorage for quick order history access
      const emailVal = checkoutForm.querySelector("input[name='email']")?.value;
      if (emailVal) {
        localStorage.setItem("cafe_user_email", emailVal.trim().toLowerCase());
      }

      // Clear local storage cart once submitted
      setTimeout(() => clearCart(), 300);
    });
  }

  // Bind live search on menu
  const menuSearchInput = document.getElementById("menuSearchInput");
  if (menuSearchInput) {
    menuSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      const cards = document.querySelectorAll(".food-card");
      cards.forEach(card => {
        const title = card.querySelector(".food-title")?.textContent.toLowerCase() || "";
        const desc = card.querySelector(".food-desc")?.textContent.toLowerCase() || "";
        const ing = card.querySelector(".food-ingredients")?.textContent.toLowerCase() || "";
        if (title.includes(query) || desc.includes(query) || ing.includes(query)) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  }
});