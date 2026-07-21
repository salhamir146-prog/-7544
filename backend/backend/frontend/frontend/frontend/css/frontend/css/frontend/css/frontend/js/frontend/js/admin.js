let currentTab = 'settings';

// ============ راه‌اندازی ============
document.addEventListener('DOMContentLoaded', function() {
    // فعال‌سازی تب‌ها
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
    
    // بارگذاری اولیه
    loadSettings();
    loadStats();
    loadChats();
});

// ============ تغییر تب ============
function switchTab(tab) {
    currentTab = tab;
    
    // بروزرسانی دکمه‌ها
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    // بروزرسانی محتوا
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tab);
    });
    
    // بارگذاری داده‌های هر تب
    if (tab === 'chats') loadChats();
    if (tab === 'stats') loadStats();
}

// ============ بارگذاری تنظیمات ============
function loadSettings() {
    fetch('/api/admin/settings')
    .then(response => response.json())
    .then(data => {
        document.getElementById('botName').value = data.name || '';
        document.getElementById('botPersonality').value = data.personality || '';
        document.getElementById('botWelcome').value = data.welcome_message || '';
        document.getElementById('botSystemPrompt').value = data.system_prompt || '';
        document.getElementById('botTemperature').value = data.temperature || 0.7;
        document.getElementById('botMaxTokens').value = data.max_tokens || 2048;
    })
    .catch(error => {
        showMessage('خطا در بارگذاری تنظیمات', 'error');
    });
}

// ============ ذخیره تنظیمات ============
function saveSettings() {
    const data = {
        name: document.getElementById('botName').value.trim(),
        personality: document.getElementById('botPersonality').value.trim(),
        welcome_message: document.getElementById('botWelcome').value.trim(),
        system_prompt: document.getElementById('botSystemPrompt').value.trim(),
        temperature: parseFloat(document.getElementById('botTemperature').value) || 0.7,
        max_tokens: parseInt(document.getElementById('botMaxTokens').value) || 2048
    };
    
    if (!data.name) {
        showMessage('لطفاً نام ربات را وارد کنید', 'error');
        return;
    }
    
    fetch('/api/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            showMessage('✅ تنظیمات با موفقیت ذخیره شد', 'success');
            // بروزرسانی نام در صفحه اصلی (اگر باز باشد)
            if (window.opener) {
                try {
                    window.opener.document.getElementById('botName').textContent = data.name;
                } catch(e) {}
            }
        } else {
            showMessage('❌ خطا در ذخیره تنظیمات', 'error');
        }
    })
    .catch(error => {
        showMessage('❌ خطا در ارتباط با سرور', 'error');
    });
}

// ============ بارگذاری چت‌ها ============
function loadChats() {
    const search = document.getElementById('searchChat')?.value || '';
    const chatList = document.getElementById('chatList');
    chatList.innerHTML = '<div class="loading">⏳ در حال بارگذاری...</div>';
    
    let url = '/api/admin/chats?limit=200';
    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }
    
    fetch(url)
    .then(response => response.json())
    .then(chats => {
        if (chats.length === 0) {
            chatList.innerHTML = '<div class="loading">📭 هیچ چتی یافت نشد</div>';
            return;
        }
        
        chatList.innerHTML = chats.map(chat => `
            <div class="chat-item">
                <div class="chat-user">
                    👤 ${escapeHtml(chat.name)} 
                    <small>📱 ${escapeHtml(chat.phone)}</small>
                </div>
                <div class="chat-message">💬 ${escapeHtml(chat.message)}</div>
                <div class="chat-response">🤖 ${escapeHtml(chat.response || 'پاسخی ثبت نشده')}</div>
                <div class="chat-time">🕐 ${new Date(chat.timestamp).toLocaleString('fa-IR')}</div>
            </div>
        `).join('');
    })
    .catch(error => {
        chatList.innerHTML = `<div class="loading">❌ خطا: ${error.message}</div>`;
    });
}

// ============ بارگذاری آمار ============
function loadStats() {
    fetch('/api/admin/stats')
    .then(response => response.json())
    .then(data => {
        document.getElementById('totalUsers').textContent = data.total_users || 0;
        document.getElementById('totalMessages').textContent = data.total_messages || 0;
        document.getElementById('todayChats').textContent = data.today_chats || 0;
        document.getElementById('onlineUsers').textContent = data.online_users || 0;
    })
    .catch(error => {
        console.error('خطا در بارگذاری آمار:', error);
    });
}

// ============ بروزرسانی آمار ============
function refreshStats() {
    loadStats();
    showMessage('📊 آمار بروزرسانی شد', 'success');
}

// ============ خروجی داده‌ها ============
function exportChats(format) {
    showMessage('⏳ در حال آماده‌سازی خروجی...', 'success');
    
    let url = `/api/admin/export?format=${format}`;
    
    fetch(url)
    .then(response => {
        if (format === 'csv') {
            return response.text();
        }
        return response.json();
    })
    .then(data => {
        if (format === 'csv') {
            // دانلود CSV
            const blob = new Blob([data], { type: 'text/csv;chars
