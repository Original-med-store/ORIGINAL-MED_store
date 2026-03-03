// Products are loaded from scripts/products.js

let cart = JSON.parse(localStorage.getItem('medicalRetailCart')) || [];

const itemsGrid = document.getElementById('product-grid');
const categoriesContainer = document.getElementById('categoriesContainer');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');

// Cart Elements
const cartBadge = document.getElementById('cartBadge');
const cartItemsContainer = document.getElementById('cartItemsContainer');
const cartTotal = document.getElementById('cartTotal');
const cartSidebar = document.getElementById('cartSidebar');
const checkoutModal = document.getElementById('checkoutModal');
const checkoutForm = document.getElementById('checkoutForm');

// Modal Elements
const lightboxModal = document.getElementById("imageModal");
const lightboxImg = document.getElementById("img01");
const captionText = document.getElementById("caption");
const productDetailsModal = document.getElementById('productDetailsModal');

// Fallback Image
const FALLBACK_IMG = 'https://via.placeholder.com/300x250?text=لا+توجد+صورة';

// State
let currentCategoryId = 'all';
let currentUser = JSON.parse(localStorage.getItem('medicalRetailUser')) || null;

function init() {
    renderCategories();
    renderProducts(products); // Render all initially
    updateCartUI();
    updateAuthUI();
    setupEventListeners();
    loadCustomerData();

    // Force category view area
    const catPanel = document.getElementById('categoriesPanel');
    if (catPanel) {
        catPanel.style.display = 'block';
        catPanel.style.maxHeight = 'none';
        catPanel.style.opacity = '1';
    }
}

// Render Categories
function renderCategories() {
    if (!categoriesContainer) return;

    if (!categories || categories.length === 0) {
        categoriesContainer.innerHTML = '<p style="padding:1rem; color:#666; font-size:0.9rem;">لا توجد أقسام</p>';
        return;
    }

    let html = `
        <button class="filter-btn active" data-id="all">
            <span>الرئيسية (الكل)</span>
        </button>
    `;

    html += categories.map(cat => `
        <button class="filter-btn" data-id="${cat.id}">
            <span>${cat.name}</span>
        </button>
    `).join('');

    categoriesContainer.innerHTML = html;
}

function filterByCategory(event, catId) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    currentCategoryId = catId;

    // Active class logic
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.getAttribute('data-id') == catId) {
            btn.classList.add('active');
            const catNameSpan = btn.querySelector('span');
            if (catNameSpan && document.getElementById('currentCategoryText')) {
                if (catId === 'all') {
                    document.getElementById('currentCategoryText').textContent = 'الرئيسية (الكل)';
                } else {
                    document.getElementById('currentCategoryText').textContent = catNameSpan.textContent;
                }
            }
        } else {
            btn.classList.remove('active');
        }
    });

    closeCategoriesModal();

    // Clear search
    if (searchInput) searchInput.value = '';

    filterAndSearch();
}

// Render Products
function renderProducts(items) {
    if (!itemsGrid) return;
    const noResults = document.getElementById('noResults');

    if (!items || items.length === 0) {
        if (noResults) noResults.classList.remove('hidden');
        itemsGrid.innerHTML = '';
        return;
    }

    if (noResults) noResults.classList.add('hidden');

    itemsGrid.innerHTML = items.map((item, index) => {
        let priceHtml = '';
        if (item.old_price && item.old_price > item.price) {
            priceHtml = `
                <div class="product-price-container">
                    <span class="price">${item.price} <span>ج.م</span></span>
                    <span class="product-price old" style="font-size: 0.8rem; margin-right: 5px;">${item.old_price} ج.م</span>
                </div>
            `;
        } else {
            priceHtml = `<div class="price">${item.price} <span>ج.م</span></div>`;
        }

        let images = item.images && item.images.length > 0 ? item.images : [item.image];
        let arrowsHtml = '';

        if (images.length > 1) {
            arrowsHtml = `
                <button class="card-arrow prev" onclick="changeCardImage(event, ${item.id}, -1)">&#10094;</button>
                <button class="card-arrow next" onclick="changeCardImage(event, ${item.id}, 1)">&#10095;</button>
            `;
        }

        const animDelay = (index % 10) * 0.1;

        // Find category name
        let catName = 'متنوع';
        if (item.category_id) {
            const cat = categories.find(c => c.id == item.category_id);
            if (cat) catName = cat.name;
        }

        return `
        <div class="item-card slide-up" style="animation-delay: ${animDelay}s; cursor: pointer;" onclick="openQuickView(${item.id})">
            <div class="card-img-container">
                 <img src="${images[0] || FALLBACK_IMG}" alt="${item.name}" class="card-img" id="img-${item.id}" data-img-index="0" onerror="this.src='${FALLBACK_IMG}'">
                 ${arrowsHtml}
            </div>
            <div class="card-body">
                <a href="#" class="card-category" onclick="event.stopPropagation(); filterByCategory(event, '${item.category_id}')">${catName}</a>
                <h3 class="card-title" title="${item.name}">${item.name}</h3>
                <div class="card-stock">
                     ${item.description ? `<p class="product-desc" style="font-size: 0.75rem; color: #7f8c8d; margin-bottom: 5px; height: 32px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${item.description}</p>` : ''}
                </div>
                <div class="card-footer">
                    ${priceHtml}
                    <button class="add-btn" title="أضف للسلة" onclick="event.stopPropagation(); addToCart(${item.id}, \`${item.name}\`, ${item.price}, '${images[0] || FALLBACK_IMG}', event)">
                        <i class="fa-solid fa-cart-plus"></i>
                    </button>
                </div>
            </div>
        </div>
    `}).join('');
}

function changeCardImage(event, productId, step) {
    event.stopPropagation();
    const imgElement = document.getElementById(`img-${productId}`);
    if (!imgElement) return;

    let currentIndex = parseInt(imgElement.getAttribute('data-img-index') || 0);

    const product = products.find(p => p.id == productId);
    if (!product) return;

    const images = product.images && product.images.length > 0 ? product.images : [product.image];

    let nextIndex = currentIndex + step;
    if (nextIndex >= images.length) nextIndex = 0;
    if (nextIndex < 0) nextIndex = images.length - 1;

    // Feature Request: Preload all images to prevent slow switching
    if (!product._imagesPreloaded) {
        images.forEach(src => {
            if (src && !src.includes('placeholder')) {
                const img = new Image();
                img.src = src;
            }
        });
        product._imagesPreloaded = true;
    }

    imgElement.src = images[nextIndex];
    imgElement.setAttribute('data-img-index', nextIndex);
}

// Arabic normalization for search
function normalizeArabic(text) {
    if (!text) return "";
    return text
        .replace(/[أإآ]/g, 'ا')
        .replace(/ة/g, 'ه')
        .replace(/ى/g, 'ي')
        .replace(/[ًٌٍَُِّْ]/g, '');
}

function filterAndSearch() {
    let term = "";
    if (searchInput) {
        term = normalizeArabic(searchInput.value.trim().toLowerCase());
    }

    let filtered = products;

    if (term) {
        filtered = filtered.filter(p => {
            const name = normalizeArabic(p.name.toLowerCase());
            const desc = p.description ? normalizeArabic(p.description.toLowerCase()) : "";
            // Find category
            let catName = "";
            const cat = categories.find(c => c.id == p.category_id);
            if (cat) catName = normalizeArabic(cat.name.toLowerCase());

            return name.includes(term) || desc.includes(term) || catName.includes(term);
        });

        // Auto-scroll logic
        const catalogSec = document.getElementById('catalog');
        if (catalogSec) {
            const headerOffset = window.innerWidth <= 768 ? 100 : 80;
            const elementPosition = catalogSec.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
            window.scrollTo({ top: offsetPosition, behavior: "smooth" });
        }
    } else {
        if (currentCategoryId !== 'all') {
            filtered = filtered.filter(p => String(p.category_id) === String(currentCategoryId));
        }

        // Auto-scroll logic when clicking All or resetting search
        const catalogSec = document.getElementById('catalog');
        if (catalogSec && !term) {
            const headerOffset = window.innerWidth <= 768 ? 100 : 80;
            const elementPosition = catalogSec.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
            window.scrollTo({ top: offsetPosition, behavior: "smooth" });
        }
    }

    // Sorting
    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        const sortValue = sortSelect.value;
        if (sortValue === 'price-asc') {
            filtered.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
        } else if (sortValue === 'price-desc') {
            filtered.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
        } else if (sortValue === 'name-asc') {
            filtered.sort((a, b) => a.name.localeCompare(b.name, 'ar'));
        } else if (sortValue === 'default') {
            // Default to ID descending (Recently Added)
            filtered.sort((a, b) => b.id - a.id);
        }
    }

    renderProducts(filtered);
}

// Live Search Dropdown
function handleLiveSearch(e) {
    const query = normalizeArabic(e.target.value.toLowerCase().trim());
    const dropdown = document.getElementById('searchResultsDropdown');
    if (!dropdown) return;

    if (query.length < 2) {
        dropdown.classList.add('hidden');
        if (query.length === 0) filterAndSearch();
        return;
    }

    const results = products.filter(item => {
        let catName = "";
        const cat = categories.find(c => c.id == item.category_id);
        if (cat) catName = normalizeArabic(cat.name.toLowerCase());
        const iName = normalizeArabic(item.name.toLowerCase());

        return iName.includes(query) || catName.includes(query)
    }).slice(0, 6);

    if (results.length === 0) {
        dropdown.innerHTML = '<div class="search-dropdown-item" style="justify-content:center; color:#999;">لا توجد نتائج مطابقة</div>';
    } else {
        dropdown.innerHTML = '';
        results.forEach(item => {
            let catName = 'متنوع';
            if (item.category_id) {
                const cat = categories.find(c => c.id == item.category_id);
                if (cat) catName = cat.name;
            }

            let img = FALLBACK_IMG;
            if (item.images && item.images.length > 0) img = item.images[0];
            else if (item.image) img = item.image;

            const a = document.createElement('a');
            a.href = "javascript:void(0);";
            a.className = 'search-dropdown-item';
            a.style.display = 'flex';
            a.style.textDecoration = 'none';
            a.style.color = 'inherit';

            a.innerHTML = `
                <img src="${img}" onerror="this.onerror=null;this.src='${FALLBACK_IMG}';" alt="${item.name}">
                <div class="search-dropdown-info">
                    <div class="search-dropdown-name" style="font-weight: 800; color: #1a1a2e; margin-bottom: 2px;">${item.name}</div>
                    <div class="search-dropdown-cat" style="font-size: 0.8rem; color: #3a7bd5;">${catName}</div>
                </div>
                <div class="search-dropdown-price" style="font-weight: 800; color: #27ae60;">${parseFloat(item.price).toFixed(2)} ج.م</div>
            `;

            const openAction = (e) => {
                e.preventDefault();
                searchInput.value = '';
                dropdown.classList.add('hidden');
                openQuickView(item.id);
            };

            a.addEventListener('mousedown', openAction);
            a.addEventListener('click', openAction);
            dropdown.appendChild(a);
        });
    }

    dropdown.classList.remove('hidden');
}


function setupEventListeners() {
    if (searchInput) {
        searchInput.addEventListener('input', handleLiveSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const dropdown = document.getElementById('searchResultsDropdown');
                if (dropdown) dropdown.classList.add('hidden');
                filterAndSearch();
            }
        });
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', filterAndSearch);
    }

    const sortSelect = document.getElementById('sortSelect');
    if (sortSelect) sortSelect.addEventListener('change', filterAndSearch);

    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (cart.length === 0) {
                alert("السلة فارغة. يرجى إضافة منتجات أولاً.");
                return;
            }

            const name = document.getElementById('custName').value;
            const phone = document.getElementById('custPhone').value;
            const address = document.getElementById('custAddress').value;
            const paymentMethod = document.getElementById('paymentMethod').value;

            let total = 0;
            let orderDetails = cart.map(item => {
                total += (item.price * item.qty);
                return `▫️ ${item.qty}x ${item.name} (${(item.price * item.qty).toFixed(2)} ج.م)`;
            }).join('\n');

            const message = `
🌟 *طلب وتوصيل جديد* 🌟
-------------------------
👤 *الاسم:* ${name}
📞 *الهاتف:* ${phone}
📍 *العنوان:* ${address || 'لم يُحدد'}
💳 *طريقة الدفع:* ${paymentMethod}
-------------------------
📦 *المنتجات:*
${orderDetails}
-------------------------
💰 *الإجمالي المطلوب:* ${total.toFixed(2)} ج.م

نرجو التأكيد والتواصل في أسرع وقت. شكراً!
            `.trim();

            const whatsappNumber = '201068672360';
            const encodedMessage = encodeURIComponent(message);
            const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${encodedMessage}`;

            cart = [];
            updateCartUI();
            closeCheckout();

            window.open(whatsappUrl, '_blank');
        });
    }

    if (categoriesContainer) {
        categoriesContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('.filter-btn');
            if (btn) {
                const categoryId = btn.getAttribute('data-id');
                filterByCategory(e, categoryId);
            }
        });
    }

    // Auth Listeners
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    document.addEventListener('mousedown', (e) => {
        const d = document.getElementById('searchResultsDropdown');
        if (d && !e.target.closest('.search-container')) {
            d.classList.add('hidden');
        }
    });
}

function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const pass = document.getElementById('loginPassword').value;

    const users = JSON.parse(localStorage.getItem('medicalRetailUsersList')) || [];
    const user = users.find(u => u.email === email && u.password === pass);

    if (user) {
        currentUser = user;
        localStorage.setItem('medicalRetailUser', JSON.stringify(user));
        showToast(`مرحبا بك مجدداً، ${user.name}`);
        closeAuthModal();
        updateAuthUI();
    } else {
        alert('بيانات الدخول غير صحيحة.');
    }
}

function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const email = document.getElementById('regEmail').value;
    const phone = document.getElementById('regPhone').value;
    const password = document.getElementById('regPassword').value;

    const users = JSON.parse(localStorage.getItem('medicalRetailUsersList')) || [];
    if (users.find(u => u.email === email)) {
        alert('هذا البريد الإلكتروني مسجل بالفعل.');
        return;
    }

    const newUser = { name, email, phone, password };
    users.push(newUser);
    localStorage.setItem('medicalRetailUsersList', JSON.stringify(users));

    currentUser = newUser;
    localStorage.setItem('medicalRetailUser', JSON.stringify(newUser));

    showToast(`تم إنشاء الحساب بنجاح، أهلاً بك ${name}`);
    closeAuthModal();
    updateAuthUI();
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('medicalRetailUser');
    showToast('تم تسجيل الخروج بنجاح');
    updateAuthUI();
}

function updateAuthUI() {
    const profileArea = document.getElementById('userProfileArea');
    const bottomNavAuth = document.getElementById('bottomNavAuth');

    if (!profileArea) return;

    if (currentUser) {
        profileArea.innerHTML = `
            <div class="user-profile-menu" style="display:flex; align-items:center; gap:10px;">
                <span style="color:white; font-weight:600;"><i class="fa-solid fa-circle-user"></i> ${currentUser.name}</span>
                <button class="auth-btn logged-in" onclick="handleLogout()">خروج</button>
            </div>
        `;
        if (bottomNavAuth) {
            bottomNavAuth.innerHTML = '<i class="fa-solid fa-user-check"></i> <span>حسابي</span>';
            bottomNavAuth.onclick = () => { alert(`أهلاً بك ${currentUser.name}`); return false; };
        }
    } else {
        profileArea.innerHTML = `
            <button class="auth-btn" id="navAuthBtn" onclick="toggleAuthModal('register')">
                <i class="fa-solid fa-user-plus"></i> تسجيل
            </button>
        `;
        if (bottomNavAuth) {
            bottomNavAuth.innerHTML = '<i class="fa-solid fa-user-plus"></i> <span>تسجيل</span>';
            bottomNavAuth.onclick = () => { toggleAuthModal('register'); return false; };
        }
    }
}

function showToast(message) {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.classList.add('hidden'), 400);
        }, 3000);
    }
}

// Global Modal Manager
function closeTopMostModal() {
    let closedAny = false;

    const contactSheet = document.getElementById('contactSheet');
    const authModal = document.getElementById('authModal');
    const confirmModal = document.getElementById('confirmModal');

    // Order of priority for closing
    if (lightboxModal && lightboxModal.classList.contains("show")) {
        lightboxModal.classList.remove("show");
        setTimeout(() => lightboxModal.classList.add('hidden'), 300);
        closedAny = true;
    } else if (contactSheet && contactSheet.classList.contains("show")) {
        contactSheet.classList.remove("show");
        setTimeout(() => contactSheet.classList.add('hidden'), 300);
        closedAny = true;
    } else if (authModal && authModal.classList.contains("show")) {
        authModal.classList.remove("show");
        setTimeout(() => authModal.classList.add('hidden'), 300);
        closedAny = true;
    } else if (confirmModal && confirmModal.classList.contains('show')) {
        confirmModal.classList.remove('show');
        setTimeout(() => confirmModal.classList.add('hidden'), 300);
        closedAny = true;
    } else if (checkoutModal && checkoutModal.classList.contains('show')) {
        closeCheckout(); // Use the dedicated function
        closedAny = true;
    } else if (productDetailsModal && productDetailsModal.classList.contains('show')) {
        productDetailsModal.classList.remove('show');
        setTimeout(() => productDetailsModal.classList.add('hidden'), 300);
        closedAny = true;
    } else if (cartSidebar && cartSidebar.classList.contains('show-sidebar')) {
        cartSidebar.classList.remove('show-sidebar');
        setTimeout(() => {
            cartSidebar.classList.remove('show');
            cartSidebar.classList.add('hidden');
        }, 400);
        closedAny = true;
    }
    return closedAny;
}

window.addEventListener('popstate', function () {
    closeTopMostModal();
});

window.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const contactSheet = document.getElementById('contactSheet');
        const authModal = document.getElementById('authModal');

        const isOpen = (lightboxModal && lightboxModal.classList.contains('show')) ||
            (productDetailsModal && productDetailsModal.classList.contains('show')) ||
            (cartSidebar && cartSidebar.classList.contains('show-sidebar')) ||
            (checkoutModal && checkoutModal.classList.contains('show')) ||
            (contactSheet && contactSheet.classList.contains('show')) ||
            (authModal && authModal.classList.contains('show')) ||
            (document.getElementById('confirmModal') && document.getElementById('confirmModal').classList.contains('show'));
        if (isOpen) history.back();
    }
});

window.addEventListener('click', function (event) {
    const contactSheet = document.getElementById('contactSheet');
    const authModal = document.getElementById('authModal');

    if (event.target == lightboxModal && lightboxModal.classList.contains('show')) {
        history.back();
    } else if (event.target == productDetailsModal && productDetailsModal.classList.contains('show')) {
        history.back();
    } else if (event.target == checkoutModal && checkoutModal.classList.contains('show')) {
        history.back();
    } else if (contactSheet && event.target == contactSheet && contactSheet.classList.contains('show')) {
        history.back();
    } else if (authModal && event.target == authModal && authModal.classList.contains('show')) {
        history.back();
    } else if (event.target.closest('#cartSidebar') === null && event.target.closest('#floatingCartBtn') === null && cartSidebar && cartSidebar.classList.contains('show-sidebar')) {
        cartSidebar.classList.remove('show-sidebar');
        setTimeout(() => {
            cartSidebar.classList.remove('show');
            cartSidebar.classList.add('hidden');
        }, 400);
    }
});

// Categories Panel
function toggleCategoriesPanel() {
    const categoriesPanel = document.getElementById('categoriesPanel');
    const btn = document.getElementById('openCategoriesBtn');
    if (!categoriesPanel) return;

    if (categoriesPanel.classList.contains('show')) {
        categoriesPanel.classList.remove('show');
        if (btn) btn.classList.remove('active-btn');
    } else {
        categoriesPanel.classList.add('show');
        if (btn) btn.classList.add('active-btn');
    }
}

function closeCategoriesModal() {
    const categoriesPanel = document.getElementById('categoriesPanel');
    const btn = document.getElementById('openCategoriesBtn');

    // On desktop, we don't auto-close the panel after selection
    if (window.innerWidth > 768) return;

    if (categoriesPanel && categoriesPanel.classList.contains('show')) {
        categoriesPanel.classList.remove('show');
        if (btn) btn.classList.remove('active-btn');
    }
}

function openLightbox(imgSrc, caption) {
    if (imgSrc.includes('placeholder')) return;
    lightboxModal.classList.remove('hidden');
    lightboxModal.classList.add("show");
    lightboxImg.src = imgSrc;
    captionText.innerHTML = caption;
    history.pushState({ modal: true }, "");
}

function closeLightbox() {
    if (lightboxModal.classList.contains('show')) history.back();
}

// Contact Sheet Modal
function toggleContactSheet() {
    const sheet = document.getElementById('contactSheet');
    if (!sheet) return;
    if (sheet.classList.contains('show')) {
        sheet.classList.remove('show');
        setTimeout(() => sheet.classList.add('hidden'), 300);
    } else {
        sheet.classList.remove('hidden');
        setTimeout(() => sheet.classList.add('show'), 10);
        history.pushState({ modal: true }, "");
    }
}

// Auth Modal
function toggleAuthModal(tab) {
    const authModal = document.getElementById('authModal');
    if (!authModal) return;
    if (authModal.classList.contains('show')) {
        closeAuthModal();
    } else {
        authModal.classList.remove('hidden');
        setTimeout(() => authModal.classList.add('show'), 10);
        if (tab) switchAuthTab(tab);
        history.pushState({ modal: true }, "");
    }
}

function closeAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal && authModal.classList.contains('show')) {
        authModal.classList.remove('show');
        setTimeout(() => authModal.classList.add('hidden'), 300);
    }
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
    } else {
        registerForm.classList.remove('hidden');
        loginForm.classList.add('hidden');
        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');
    }
}


// Quick View Modal
function openQuickView(itemId) {
    const item = products.find(i => i.id == itemId);
    if (!item) return;

    if (!productDetailsModal) return;

    let images = item.images && item.images.length > 0 ? item.images : [item.image];
    const imgUrl = images[0] || FALLBACK_IMG;

    document.getElementById('modalProductImg').src = imgUrl;

    let catName = '';
    if (item.category_id) {
        const c = categories.find(ct => ct.id == item.category_id);
        if (c) catName = c.name;
    }

    document.getElementById('modalProductCategory').textContent = catName || 'بدون قسم';
    document.getElementById('modalProductName').textContent = item.name;

    // Price with discount logic
    const modalPriceElem = document.getElementById('modalProductPrice');
    const modalOldPriceElem = document.getElementById('modalProductOldPrice');

    if (modalPriceElem) {
        modalPriceElem.textContent = parseFloat(item.price).toFixed(2);
    }

    if (modalOldPriceElem) {
        if (item.old_price && item.old_price > item.price) {
            modalOldPriceElem.textContent = parseFloat(item.old_price).toFixed(2) + ' ج.م';
            modalOldPriceElem.style.display = 'inline-block';
        } else {
            modalOldPriceElem.style.display = 'none';
        }
    }

    const stockBadge = document.getElementById('modalProductStock');
    stockBadge.textContent = 'متوفر';
    stockBadge.style.background = '#2ecc71';

    const descEl = document.getElementById('modalProductDesc');
    if (item.description && item.description.trim() !== '') {
        descEl.textContent = item.description;
    } else {
        descEl.textContent = '(لا يوجد وصف متاح)';
    }

    // Replace add to cart
    const addToCartBtn = document.getElementById('modalAddToCartBtn');
    if (addToCartBtn) {
        const newAddToCartBtn = addToCartBtn.cloneNode(true);
        addToCartBtn.parentNode.replaceChild(newAddToCartBtn, addToCartBtn);
        newAddToCartBtn.onclick = function (e) {
            addToCart(item.id, item.name, item.price, imgUrl, e);
        };
    }

    // Suggestion 5: Image Zoom Functionality
    const imgContainer = document.querySelector('.product-modal-image');
    const zoomImg = document.getElementById('modalProductImg');
    if (imgContainer && zoomImg) {
        // Reset state
        imgContainer.classList.remove('zoomed');
        zoomImg.style.transform = '';

        imgContainer.onclick = function () {
            imgContainer.classList.toggle('zoomed');
            if (!imgContainer.classList.contains('zoomed')) {
                zoomImg.style.transform = '';
            }
        };

        imgContainer.onmousemove = function (e) {
            if (imgContainer.classList.contains('zoomed')) {
                const rect = imgContainer.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                zoomImg.style.transformOrigin = `${x}% ${y}%`;
            }
        };

        // Touch support for mobile
        let touchTimer;
        imgContainer.ontouchstart = function () {
            touchTimer = setTimeout(() => {
                imgContainer.classList.toggle('zoomed');
            }, 200);
        };
        imgContainer.ontouchend = function () {
            clearTimeout(touchTimer);
        };
    }

    // Fix WhatsApp Inquiry Button
    const modalWhatsappBtn = document.getElementById('modalWhatsappBtn');
    if (modalWhatsappBtn) {
        const vendorPhone = "201068672360";
        const message = `السلام عليكم، أريد الاستفسار عن منتج: ${item.name}`;
        const waLink = `https://wa.me/${vendorPhone}?text=${encodeURIComponent(message)}`;
        modalWhatsappBtn.onclick = function () {
            window.open(waLink, '_blank');
        };
    }

    // Related Products
    renderRelatedProducts(item);

    productDetailsModal.classList.remove('hidden');
    productDetailsModal.classList.add("show");
    history.pushState({ modal: true, type: 'product' }, "");
}

function closeProductModal() {
    if (productDetailsModal && productDetailsModal.classList.contains('show')) {
        history.back();
    }
}

function renderRelatedProducts(currentItem) {
    const container = document.getElementById('relatedProductsContainer');
    const scrollArea = document.getElementById('relatedProductsScroll');
    if (!container || !scrollArea) return;

    if (!currentItem || !currentItem.category_id) {
        container.classList.add('hidden');
        return;
    }

    const related = products.filter(i =>
        i.category_id === currentItem.category_id && i.id !== currentItem.id
    ).slice(0, 6);

    if (related.length === 0) {
        container.classList.add('hidden');
        return;
    }

    container.classList.remove('hidden');

    scrollArea.innerHTML = related.map(item => {
        let images = item.images && item.images.length > 0 ? item.images : [item.image];
        return `
        <div class="related-product-card" onclick="openQuickView('${item.id}')">
            <img class="related-product-img" src="${images[0] || FALLBACK_IMG}" onerror="this.onerror=null;this.src='${FALLBACK_IMG}';" alt="${item.name}">
            <div class="related-product-name" title="${item.name}">${item.name}</div>
            <div class="related-product-price">${parseFloat(item.price).toFixed(2)} ج.م</div>
        </div>
    `}).join('');
}

// ==== Cart Functionality ====
function toggleCart(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    if (!cartSidebar) return;
    if (cartSidebar.classList.contains("show-sidebar")) {
        cartSidebar.classList.remove('show-sidebar');
        setTimeout(() => {
            cartSidebar.classList.remove('show');
            cartSidebar.classList.add('hidden');
        }, 400);
    } else {
        cartSidebar.classList.remove('hidden');
        cartSidebar.classList.add('show');
        // Small delay to allow CSS display:block to apply before animating transform
        setTimeout(() => {
            cartSidebar.classList.add("show-sidebar");
        }, 10);
    }
}

function addToCart(id, name, price, imgUrl, event) {
    const existingItem = cart.find(i => i.id == id);
    if (existingItem) {
        existingItem.qty += 1;
    } else {
        cart.push({ id, name, price, imgUrl, qty: 1 });
    }

    // Suggestion 4: Fly Animation
    if (event) {
        flyToCart(event, imgUrl);
    }

    updateCartUI();
    showToast(`تم إضافة "${name}" للسلة بنجاح`);
}

function flyToCart(event, imgSrc) {
    const cartBtn = document.getElementById('floatingCartBtn') || document.querySelector('.nav-item i.fa-cart-shopping');
    if (!cartBtn) return;

    const startRect = event.target.getBoundingClientRect();
    const endRect = cartBtn.getBoundingClientRect();

    const flyer = document.createElement('img');
    flyer.src = imgSrc;
    flyer.className = 'fly-item';
    flyer.style.left = `${startRect.left}px`;
    flyer.style.top = `${startRect.top}px`;
    document.body.appendChild(flyer);

    // Minor delay to ensure appended to DOM
    requestAnimationFrame(() => {
        flyer.style.transform = `translate(${endRect.left - startRect.left}px, ${endRect.top - startRect.top}px) scale(0.1)`;
        flyer.style.opacity = '0';
    });

    setTimeout(() => {
        flyer.remove();
        cartBtn.classList.add('bounce-in');
        setTimeout(() => cartBtn.classList.remove('bounce-in'), 500);
    }, 800);
}

function updateQuantity(id, delta, event) {
    if (event) {
        event.stopPropagation();
    }
    const itemIndex = cart.findIndex(i => i.id == id);
    if (itemIndex > -1) {
        cart[itemIndex].qty += delta;
        if (cart[itemIndex].qty <= 0) {
            cart.splice(itemIndex, 1);
        }
        updateCartUI();
    }
}

function removeCartItem(id, event) {
    if (event) {
        event.stopPropagation();
    }
    cart = cart.filter(i => String(i.id) !== String(id));
    updateCartUI();
}

function updateCartUI() {
    if (!cartBadge || !cartItemsContainer || !cartTotal) return;

    const totalItems = cart.reduce((sum, item) => sum + item.qty, 0);
    cartBadge.textContent = totalItems;

    const navBadge = document.getElementById('navCartBadge');
    if (navBadge) {
        navBadge.textContent = totalItems;
        if (totalItems > 0) {
            navBadge.style.display = 'flex';
        } else {
            navBadge.style.display = 'none';
        }
    }

    if (cart.length === 0) {
        cartItemsContainer.innerHTML = `
            <div class="empty-cart-container">
                <i class="fa-solid fa-cart-arrow-down empty-cart-icon"></i>
                <div class="empty-cart-title">سلة المشتريات فارغة</div>
                <p style="color:#7f8c8d; font-size:0.9rem;">أضف بعض المنتجات الرائعة لتبدأ التسوق!</p>
                <button class="start-shopping-btn" onclick="toggleCart()">ابدأ التسوق الآن</button>
            </div>
        `;
        cartTotal.textContent = '0.00 ج.م';
        localStorage.setItem('medicalRetailCart', JSON.stringify(cart));
        return;
    }

    let html = '';
    let total = 0;

    cart.forEach(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        html += `
            <div class="cart-item">
                <img src="${item.imgUrl}" class="cart-item-img">
                <div class="cart-item-info">
                    <div class="cart-item-title">${item.name}</div>
                    <div class="cart-item-price">${parseFloat(item.price).toFixed(2)} ج.م</div>
                </div>
                <div class="cart-item-qty">
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', 1, event)">+</button>
                    <span>${item.qty}</span>
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', -1, event)">-</button>
                </div>
                <button class="remove-btn" onclick="removeCartItem('${item.id}', event)" title="حذف الصنف"><i class="fa-solid fa-trash-can"></i></button>
            </div>
        `;
    });

    html += `
        <div style="text-align:center; margin-top:15px;">
            <button class="clear-cart-btn" onclick="emptyCart()">
                <i class="fa-solid fa-broom"></i> تفريغ السلة
            </button>
        </div>
    `;

    cartItemsContainer.innerHTML = html;
    cartTotal.textContent = `${total.toFixed(2)} ج.م`;

    localStorage.setItem('medicalRetailCart', JSON.stringify(cart));
}

function emptyCart() {
    if (confirm('هل أنت متأكد من تفريغ السلة؟')) {
        cart = [];
        updateCartUI();
    }
}

// ==== Checkout Logic ====
function proceedToCheckout() {
    if (cart.length === 0) {
        alert("السلة فارغة. يرجى إضافة منتجات أولاً.");
        return;
    }
    if (cartSidebar && cartSidebar.classList.contains('show-sidebar')) {
        cartSidebar.classList.remove('show-sidebar');
        setTimeout(() => cartSidebar.classList.add('hidden'), 400);
    }
    setTimeout(() => {
        if (checkoutModal) {
            checkoutModal.classList.remove('hidden');
            checkoutModal.classList.add('show');
            history.pushState({ modal: true }, "");
        }
    }, 150);
}

function closeCheckout() {
    if (checkoutModal) {
        checkoutModal.classList.remove('show', 'open');
        setTimeout(() => {
            checkoutModal.classList.add('hidden');
            document.body.style.overflow = '';
        }, 300);
    }
}

// Persist Form Data
['custName', 'custPhone', 'custAddress'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('input', function (e) {
            localStorage.setItem(`kimi_retail_${id}`, e.target.value);
        });
    }
});

function loadCustomerData() {
    ['custName', 'custPhone', 'custAddress'].forEach(id => {
        const savedValue = localStorage.getItem(`kimi_retail_${id}`);
        const el = document.getElementById(id);
        if (savedValue && el) {
            el.value = savedValue;
        }
    });
}

document.addEventListener('DOMContentLoaded', init);
