// Products are loaded from scripts/products.js

let cart = [];

// DOM Elements
const productGrid = document.getElementById('product-grid');
const cartSidebar = document.getElementById('cart-sidebar');
const cartOverlay = document.querySelector('.cart-overlay');
const cartItemsContainer = document.getElementById('cart-items');
const cartCountSpan = document.getElementById('cart-count');
const cartTotalPriceSpan = document.getElementById('cart-total-price');
const checkoutModal = document.getElementById('checkout-modal');

// Initialize
function init() {
    renderProducts();
    updateCartUI();
}

// Render Products
function renderProducts() {
    productGrid.innerHTML = products.map(product => `
        <div class="product-card">
            <img src="${product.image}" alt="${product.name}" class="product-image">
            <div class="product-info">
                <div>
                    <h3 class="product-title">${product.name}</h3>
                </div>
                <div>
                    <div class="product-price">${product.price} ج.م</div>
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        <i class="fas fa-cart-plus"></i> أضف للسلة
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Cart Functions
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const existingItem = cart.find(item => item.id === productId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ ...product, quantity: 1 });
    }

    updateCartUI();
    toggleCart(true); // Open cart when adding
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartUI();
}

function updateCartUI() {
    // Update Count
    const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartCountSpan.textContent = totalCount;

    // Update Items
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<div class="empty-cart-msg">السلة فارغة</div>';
    } else {
        cartItemsContainer.innerHTML = cart.map(item => `
            <div class="cart-item">
                <img src="${item.image}" alt="${item.name}">
                <div class="cart-item-details">
                    <div class="cart-item-title">${item.name}</div>
                    <div class="cart-item-price">${item.price} ج.م × ${item.quantity}</div>
                </div>
                <button class="remove-item" onclick="removeFromCart(${item.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
    }

    // Update Total
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    cartTotalPriceSpan.textContent = total.toFixed(2) + ' ج.م';
}

function toggleCart(forceOpen = null) {
    const isOpen = cartSidebar.classList.contains('open');
    if (forceOpen === true || (forceOpen === null && !isOpen)) {
        cartSidebar.classList.add('open');
        cartOverlay.classList.add('open');
    } else {
        cartSidebar.classList.remove('open');
        cartOverlay.classList.remove('open');
    }
}

// Checkout Functions
function checkout() {
    if (cart.length === 0) {
        alert('السلة فارغة!');
        return;
    }
    toggleCart(false);
    checkoutModal.classList.add('open');
}

function closeCheckout() {
    checkoutModal.classList.remove('open');
}

// ==========================================
//  إرسال الطلب عبر واتساب
// ==========================================
document.getElementById('checkout-form').addEventListener('submit', function (e) {
    e.preventDefault();

    // 1. جمع بيانات العميل
    const name = this.querySelector('input[type="text"]').value;
    const phone = this.querySelector('input[type="tel"]').value;
    const address = this.querySelector('textarea').value;

    // 2. تجهيز تفاصيل الطلب
    let message = `*طلب جديد من متجر ORIGINAL_MED*\n\n`;
    message += `*الاسم:* ${name}\n`;
    message += `*الهاتف:* ${phone}\n`;
    message += `*العنوان:* ${address}\n\n`;
    message += `*الطلبات:* \n`;

    let total = 0;
    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        message += `- ${item.name} (${item.quantity} × ${item.price} ج.م) = ${itemTotal} ج.م\n`;
    });

    message += `\n*الإجمالي:* ${total} ج.م`;

    // 3. التوجيه إلى واتساب (استبدل الرقم برقمك الحقيقي)
    // مثال: 201000000000 (كود الدولة + الرقم)
    const ownerPhone = "201068672360";
    const whatsappUrl = `https://wa.me/${ownerPhone}?text=${encodeURIComponent(message)}`;

    window.open(whatsappUrl, '_blank');

    // 4. إغلاق السلة وتنظيفها (اختياري)
    // cart = [];
    // updateCartUI();
    closeCheckout();
});

// Run Init
init();
