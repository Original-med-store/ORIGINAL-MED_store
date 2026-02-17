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
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');

// Initialize
function init() {
    renderProducts(products); // Render all initially
    updateCartUI();
    setupEventListeners();
}

function setupEventListeners() {
    searchBtn.addEventListener('click', () => {
        handleSearch(searchInput.value);
    });

    searchInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            handleSearch(searchInput.value);
        } else {
            handleSearch(searchInput.value); // Real-time search
        }
    });
}

function handleSearch(query) {
    const term = query.toLowerCase().trim();
    if (!term) {
        renderProducts(products);
        return;
    }

    const filtered = products.filter(p =>
        p.name.toLowerCase().includes(term) ||
        (p.description && p.description.toLowerCase().includes(term))
    );

    renderProducts(filtered);
}

// Render Products
function renderProducts(items) {
    if (items.length === 0) {
        productGrid.innerHTML = '<div style="text-align:center; grid-column: 1/-1; padding: 2rem; color: #666;">لا توجد منتجات تطابق بحثك</div>';
        return;
    }

    productGrid.innerHTML = items.map(product => {
        let priceHtml = '';
        if (product.old_price && product.old_price > product.price) {
            const discount = Math.round(((product.old_price - product.price) / product.old_price) * 100);
            priceHtml = `
                <div class="product-price-container">
                    <span class="product-price new">${product.price} ج.م</span>
                    <span class="product-price old">${product.old_price} ج.م</span>
                    <span class="discount-badge">${discount}% خصم</span>
                </div>
            `;
        } else {
            priceHtml = `<div class="product-price">${product.price} ج.م</div>`;
        }

        return `
        <div class="product-card">
            <div class="image-container">
                 <img src="${product.image}" alt="${product.name}" class="product-image" onclick="openProductModal(${product.id})">
            </div>
            <div class="product-info">
                <div>
                    <h3 class="product-title" onclick="openProductModal(${product.id})">${product.name}</h3>
                    <p class="product-desc">${product.description || ''}</p>
                </div>
                <div>
                    ${priceHtml}
                    <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                        <i class="fas fa-cart-plus"></i> أضف للسلة
                    </button>
                </div>
            </div>
        </div>
    `}).join('');
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

    // Feedback animation
    const btn = document.querySelector(`button[onclick="addToCart(${productId})"]`);
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> تمت الإضافة';
        btn.style.background = '#20c997'; // Secondary success color
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.background = '';
        }, 1500);
    }
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

// Product Modal & Slider
let currentProduct = null;
let currentImageIndex = 0;

function openProductModal(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;

    currentProduct = product;
    currentImageIndex = 0;

    // Determine images (handle legacy single image vs new list)
    let images = [];
    if (product.images && product.images.length > 0) {
        images = product.images;
    } else {
        images = [product.image];
    }

    const modalBody = document.getElementById('product-modal-body');
    const modal = document.getElementById('product-modal');

    // Price logic
    let priceHtml = '';
    if (product.old_price && product.old_price > product.price) {
        priceHtml = `
            <div class="product-price-container large">
                <span class="product-price new">${product.price} ج.م</span>
                <span class="product-price old">${product.old_price} ج.م</span>
            </div>
        `;
    } else {
        priceHtml = `<div class="product-price large">${product.price} ج.م</div>`;
    }

    // Slider HTML
    let sliderHtml = '';
    if (images.length > 1) {
        sliderHtml = `
            <div class="slider-container">
                <button class="slider-btn prev" onclick="changeSlide(-1)">&#10094;</button>
                <img src="${images[0]}" id="slider-img" class="slider-img">
                <button class="slider-btn next" onclick="changeSlide(1)">&#10095;</button>
                <div class="slider-dots">
                    ${images.map((_, idx) => `<span class="dot ${idx === 0 ? 'active' : ''}" onclick="setSlide(${idx})"></span>`).join('')}
                </div>
            </div>
        `;
    } else {
        sliderHtml = `<img src="${images[0]}" class="modal-single-img">`;
    }

    modalBody.innerHTML = `
        <div class="modal-product-details">
            <div class="modal-gallery">
                ${sliderHtml}
            </div>
            <div class="modal-info">
                <h2>${product.name}</h2>
                ${priceHtml}
                <div class="product-full-desc">
                    ${product.description}
                </div>
                <button class="btn btn-primary btn-block" onclick="addToCart(${product.id}); closeProductModal()">
                    إضافة للسلة
                </button>
            </div>
        </div>
    `;

    modal.classList.add('open');
}

function closeProductModal() {
    document.getElementById('product-modal').classList.remove('open');
}

function changeSlide(step) {
    const images = (currentProduct.images && currentProduct.images.length > 0) ? currentProduct.images : [currentProduct.image];
    if (images.length <= 1) return;

    currentImageIndex += step;
    if (currentImageIndex >= images.length) currentImageIndex = 0;
    if (currentImageIndex < 0) currentImageIndex = images.length - 1;

    updateSlider(images);
}

function setSlide(index) {
    currentImageIndex = index;
    const images = (currentProduct.images && currentProduct.images.length > 0) ? currentProduct.images : [currentProduct.image];
    updateSlider(images);
}

function updateSlider(images) {
    document.getElementById('slider-img').src = images[currentImageIndex];

    const dots = document.querySelectorAll('.slider-dots .dot');
    dots.forEach((dot, idx) => {
        if (idx === currentImageIndex) dot.classList.add('active');
        else dot.classList.remove('active');
    });
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
if (document.getElementById('checkout-form')) {
    document.getElementById('checkout-form').addEventListener('submit', function (e) {
        e.preventDefault();

        // 1. جمع بيانات العميل
        const name = this.querySelector('input[type="text"]').value;
        const phone = this.querySelector('input[type="tel"]').value;
        const address = this.querySelector('textarea').value;

        // 2. تجهيز تفاصيل الطلب
        let message = `*طلب جديد من متجر ORIGINAL_MED*\n`;
        message += `----------------------------\n`;
        message += `*الاسم:* ${name}\n`;
        message += `*الهاتف:* ${phone}\n`;
        message += `*العنوان:* ${address}\n`;
        message += `----------------------------\n`;
        message += `*الطلبات:* \n`;

        let total = 0;
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            total += itemTotal;
            message += `- ${item.name} (${item.quantity} × ${item.price} ج.م) = ${itemTotal} ج.م\n`;
        });

        message += `\n*الإجمالي:* ${total} ج.م`;

        // 3. التوجيه إلى واتساب
        const ownerPhone = "201068672360";
        const whatsappUrl = `https://wa.me/${ownerPhone}?text=${encodeURIComponent(message)}`;

        window.open(whatsappUrl, '_blank');

        closeCheckout();
    });
}

// Run Init
init();
