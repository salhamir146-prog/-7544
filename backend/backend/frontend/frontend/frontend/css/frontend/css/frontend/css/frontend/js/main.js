let userId = null;
let userPhone = '';
let chatHistory = [];
let isTyping = false;

// ============ ورود کاربر ============
function loginUser() {
    const name = document.getElementById('userName').value.trim();
    const phone = document.getElementById('userPhone').value.trim();
    
    if (!name || !phone) {
        showToast('لطفاً نام و شماره تلفن را وارد کنید', 'error');
        return;
    }
    
    if (!/^09\d{9}$/.test(phone) && phone !== 'Amidhjsos62627@_897') {
        showToast('شماره تلفن باید ۱۱ رقم و با ۰۹ شروع شود', 'error');
        return;
    }
    
    // بررسی ورود ادمین
    if (phone === 'Amidhjsos62627@_897') {
        window.location.href = '/admin';
        return;
    }
    
    const loginBtn = document.querySelector('.btn-primary');
    loginBtn.textContent = '⏳ در حال ورود...';
    loginBtn.disabled = true;
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            userId = data.user_id;
            userPhone = phone;
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('chatInterface').style.display = 'flex';
            
            // بارگذاری تنظیمات و پیام خوش‌آمدگویی
            loadSettings();
        } else {
            showToast(data.error || 'خطا در ورود', 'error');
        }
    })
    .catch(error => {
        showToast('خطا در ارتباط با سرور: ' + error.message, 'error');
    })
    .finally(() => {
        loginBtn.textContent = '🌙 ورود به آوای یقین';
        loginBtn.disabled = false;
    });
}

// ============ بارگذاری تنظیمات ============
function loadSettings() {
    fetch('/api/admin/settings')
    .then(response => response.json())
    .then(data => {
        document.getElementById('botName').textContent = data.name || 'آوای یقین';
        // نمایش پیام خوش‌آمدگویی
        const welcomeMsg = data.welcome_message || '🌙 سلام! من آوای یقین هستم. چه سوالی دارید؟';
        const messagesDiv = document.getElementById('chatMessages');
        messagesDiv.innerHTML = `
            <div class="message ai">
                <div class="message-avatar">🤖</div>
                <div class="message-content">${welcomeMsg}</div>
            </div>
        `;
    })
    .catch(error => {
        console.error('خطا در بارگذاری تنظیمات:', error);
    });
}

// ============ ارسال پیام ============
function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    if (!userId) {
        showToast('لطفاً ابتدا وارد شوید', 'error');
        return;
    }
    if (isTyping) return;
    
    // نمایش پیام کاربر
    const messagesDiv = document.getElementById('chatMessages');
    const userMsgDiv = document.createElement('div');
    userMsgDiv.className = 'message user';
    userMsgDiv.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    messagesDiv.appendChild(userMsgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // پاک کردن ورودی
    input.value = '';
    
    // نمایش تایپ
    showTyping(true);
    isTyping = true;
    
    // ارسال به سرور
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            user_id: userId, 
            message: message,
            phone: userPhone
        })
    })
    .then(response => response.json())
    .then(data => {
        showTyping(false);
        isTyping = false;
        
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        
        // نمایش پاسخ AI
        const aiMsgDiv = document.createElement('div');
        aiMsgDiv.className = 'message ai';
        aiMsgDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">${escapeHtml(data.response)}</div>
        `;
        messagesDiv.appendChild(aiMsgDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    })
    .catch(error => {
        showTyping(false);
        isTyping = false;
        showToast('خطا در ارتباط با سرور: ' + error.message, 'error');
    });
}

// ============ نمایش/مخفی کردن تایپ ============
function showTyping(show) {
    const indicator = document.getElementById('typingIndicator');
    if (show) {
        indicator.classList.add('active');
    } else {
        indicator.classList.remove('active');
    }
}

// ============ توابع کمکی ============
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    // حذف toast قبلی
    const oldToast = document.querySelector('.custom-toast');
    if (oldToast) oldToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `custom-toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        padding: 12px 24px;
        border-radius: 14px;
        background: ${type === 'error' ? 'rgba(255,0,0,0.2)' : 'rgba(76,175,80,0.2)'};
        backdrop-filter: blur(20px);
        border: 1px solid ${type === 'error' ? 'rgba(255,0,0,0.2)' : 'rgba(76,175,80,0.2)'};
        color: ${type === 'error' ? '#ff6b6b' : '#4CAF50'};
        font-size: 14px;
        z-index: 9999;
        max-width: 90%;
        text-align: center;
        animation: slideUp 0.3s ease;
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============ رویدادهای صفحه ============
document.addEventListener('DOMContentLoaded', function() {
    // Enter برای ارسال
    document.getElementById('userInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // فوکوس خودکار روی ورودی
    setTimeout(() => {
        const input = document.getElementById('userInput');
        if (input) input.focus();
    }, 500);
});

// ============ استایل toast ============
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
`;
document.head.appendChild(style);
