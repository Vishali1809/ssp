/* ═══════════════════════════════════════════════════════════════════════════
   Salem Steel Plant HR Portal — Main JavaScript
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

    // ── Voice Search (Homepage & Employee Dashboard) ──────────────────────
    const searchInput   = document.getElementById('searchInput');
    const yearSlider    = document.getElementById('yearSlider');
    const yearDisplay   = document.getElementById('yearDisplay');
    const resetBtn      = document.getElementById('resetTimelineBtn');
    const voiceMicBtn   = document.getElementById('voiceSearchBtn');
    const langToggleBtn = document.getElementById('langToggleBtn');
    const noResultsMsg  = document.getElementById('noResultsMsg');
    const visibleCount  = document.getElementById('visibleCount');

    let currentLang = 'en-IN';

    // Language toggle (EN / TA)
    if (langToggleBtn) {
        langToggleBtn.addEventListener('click', () => {
            if (currentLang === 'en-IN') {
                currentLang = 'ta-IN';
                langToggleBtn.textContent = 'TA';
                langToggleBtn.classList.replace('bg-gray-100', 'bg-blue-100');
                langToggleBtn.classList.replace('text-gray-600', 'text-blue-800');
            } else {
                currentLang = 'en-IN';
                langToggleBtn.textContent = 'EN';
                langToggleBtn.classList.replace('bg-blue-100', 'bg-gray-100');
                langToggleBtn.classList.replace('text-blue-800', 'text-gray-600');
            }
        });
    }

    // ── AJAX Pagination & Filtering ──────────────────────────────────────
    let currentPage = 1;
    let currentDept = new URLSearchParams(window.location.search).get('dept') || '';

    async function fetchPaginatedRules(page = 1) {
        const rulesContainer = document.getElementById('rulesContainer');
        const countDisplay = document.getElementById('ruleCountDisplay');
        const paginationContainer = document.getElementById('paginationContainer');
        const noResultsMsg = document.getElementById('noResultsMsg');
        if (!rulesContainer) return; // Not on the employee dashboard

        const q = searchInput ? searchInput.value.trim() : '';
        const year = yearSlider ? yearSlider.value : '1969';
        const perPage = window.innerWidth < 768 ? 5 : 10;

        rulesContainer.innerHTML = '<div class="col-span-3 text-center py-12 text-gray-500 animate-pulse">Loading rules...</div>';

        try {
            const res = await fetch(`/api/rules/html?q=${encodeURIComponent(q)}&year=${year}&dept=${encodeURIComponent(currentDept)}&page=${page}&per_page=${perPage}`);
            if (!res.ok) throw new Error('Network error');
            const data = await res.json();
            
            rulesContainer.innerHTML = data.html;
            currentPage = data.page;

            if (visibleCount) visibleCount.textContent = data.total;

            if (noResultsMsg) {
                noResultsMsg.classList.toggle('hidden', data.total > 0);
            }

            if (countDisplay) {
                if (data.total === 0) {
                    countDisplay.textContent = 'No rules found';
                } else {
                    const start = (currentPage - 1) * perPage + 1;
                    const end = Math.min(currentPage * perPage, data.total);
                    countDisplay.textContent = `Showing ${start}–${end} of ${data.total} rules`;
                }
            }

            if (paginationContainer) {
                renderPagination(paginationContainer, data.page, data.total_pages, (newPage) => {
                    fetchPaginatedRules(newPage);
                    // Smooth scroll to top of rules
                    document.getElementById('rulesContainer').scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
            }
        } catch (err) {
            console.error('Error fetching rules:', err);
            rulesContainer.innerHTML = '<div class="col-span-3 text-center py-12 text-red-500">Error loading rules. Please try again.</div>';
        }
    }

    function renderPagination(container, current, total, onPageClick) {
        container.innerHTML = '';
        if (total <= 1) return;

        const createBtn = (text, page, disabled, active) => {
            const btn = document.createElement('button');
            btn.innerHTML = text;
            btn.className = `px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                active ? 'bg-sail-blue text-white shadow' :
                disabled ? 'text-gray-300 cursor-not-allowed' :
                'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`;
            if (disabled) btn.disabled = true;
            else btn.addEventListener('click', () => onPageClick(page));
            return btn;
        };

        // Previous
        container.appendChild(createBtn('← Previous', current - 1, current === 1, false));

        // Pages
        let startPage = Math.max(1, current - 2);
        let endPage = Math.min(total, current + 2);

        if (current <= 3) endPage = Math.min(total, 5);
        if (current >= total - 2) startPage = Math.max(1, total - 4);

        if (startPage > 1) {
            container.appendChild(createBtn('1', 1, false, false));
            if (startPage > 2) container.appendChild(createBtn('...', null, true, false));
        }

        for (let i = startPage; i <= endPage; i++) {
            container.appendChild(createBtn(i, i, false, i === current));
        }

        if (endPage < total) {
            if (endPage < total - 1) container.appendChild(createBtn('...', null, true, false));
            container.appendChild(createBtn(total, total, false, false));
        }

        // Next
        container.appendChild(createBtn('Next →', current + 1, current === total, false));
    }

    if (searchInput) searchInput.addEventListener('input', () => fetchPaginatedRules(1));

    if (yearSlider) {
        yearSlider.addEventListener('input', e => {
            const val = parseInt(e.target.value, 10);
            if (yearDisplay) yearDisplay.textContent = val === 1969 ? 'All' : val;
            fetchPaginatedRules(1);
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (yearSlider) { yearSlider.value = 1969; }
            if (yearDisplay) yearDisplay.textContent = 'All';
            fetchPaginatedRules(1);
        });
    }

    // Expose a global function to change department from UI without reload
    window.setDepartmentFilter = function(dept) {
        currentDept = dept;
        // Update URL to reflect state
        const url = new URL(window.location.href);
        if (dept) url.searchParams.set('dept', dept);
        else url.searchParams.delete('dept');
        window.history.pushState({}, '', url);

        // Update active classes on dept buttons
        document.querySelectorAll('.dept-filter-btn').forEach(btn => {
            const btnDept = btn.dataset.dept || '';
            if (btnDept === dept) {
                btn.classList.add('bg-sail-blue', 'text-white', 'border-sail-blue');
                btn.classList.remove('text-sail-blue', 'hover:bg-blue-50');
            } else {
                btn.classList.remove('bg-sail-blue', 'text-white');
                btn.classList.add('text-sail-blue', 'border-sail-blue', 'hover:bg-blue-50');
            }
        });
        
        fetchPaginatedRules(1);
    };

    // Run initial fetch
    if (document.getElementById('rulesContainer')) {
        fetchPaginatedRules(1);
        // Handle window resize for mobile vs desktop limit change
        let lastWidth = window.innerWidth;
        window.addEventListener('resize', () => {
            const newWidth = window.innerWidth;
            if ((lastWidth < 768 && newWidth >= 768) || (lastWidth >= 768 && newWidth < 768)) {
                lastWidth = newWidth;
                fetchPaginatedRules(1);
            }
        });
    }


    // ── Voice Search ───────────────────────────────────────────────────────
    if (voiceMicBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous    = false;
        recognition.interimResults = false;

        voiceMicBtn.addEventListener('click', () => {
            recognition.lang = currentLang;
            voiceMicBtn.classList.add('mic-listening');
            recognition.start();
        });

        recognition.onresult = e => {
            voiceMicBtn.classList.remove('mic-listening');
            if (searchInput) {
                searchInput.value = e.results[0][0].transcript;
                fetchPaginatedRules(1);
            }
        };

        recognition.onerror = () => voiceMicBtn.classList.remove('mic-listening');
        recognition.onend   = () => voiceMicBtn.classList.remove('mic-listening');
    } else if (voiceMicBtn) {
        // Browser doesn't support speech API
        voiceMicBtn.title = 'Voice search requires Chrome or Edge browser';
        voiceMicBtn.style.opacity = '0.4';
        voiceMicBtn.style.cursor  = 'not-allowed';
    }

    // ── Floating AI Chat Panel ─────────────────────────────────────────────
    const assistantBtn  = document.getElementById('assistantBtn');
    const chatPanel     = document.getElementById('chatPanel');
    const closeChatBtn  = document.getElementById('closeChatBtn');
    const chatInput     = document.getElementById('chatInput');
    const sendChatBtn   = document.getElementById('sendChatBtn');
    const chatMicBtn    = document.getElementById('chatMicBtn');
    const chatHistory   = document.getElementById('chatHistory');

    function openChat() {
        if (chatPanel) {
            chatPanel.classList.add('open');
            if (assistantBtn) assistantBtn.style.display = 'none';
            chatInput?.focus();
        }
    }

    function closeChat() {
        if (chatPanel) {
            chatPanel.classList.remove('open');
            if (assistantBtn) assistantBtn.style.display = '';
        }
    }

    if (assistantBtn) assistantBtn.addEventListener('click', openChat);
    if (closeChatBtn) closeChatBtn.addEventListener('click', closeChat);

    // Add message bubble to chat history
    function addMessage(text, sender) {
        if (!chatHistory) return;
        const div = document.createElement('div');
        div.className = sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai';
        div.textContent = text;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Loading indicator
    function addLoading() {
        if (!chatHistory) return null;
        const div = document.createElement('div');
        div.className = 'chat-bubble-ai text-gray-400 italic text-xs';
        div.innerHTML = '<span class="animate-pulse">● ● ●</span>';
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return div;
    }

    // Submit chat message — calls server-side /api/chat (Gemini key is secure)
    async function handleChatSubmit() {
        if (!chatInput) return;
        const question = chatInput.value.trim();
        if (!question) return;

        addMessage(question, 'user');
        chatInput.value = '';
        if (sendChatBtn) { sendChatBtn.disabled = true; sendChatBtn.textContent = '…'; }

        const loadingEl = addLoading();

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            const data = await resp.json();
            if (loadingEl) loadingEl.remove();
            addMessage(data.answer || "I'm sorry, I couldn't process that request.", 'ai');
        } catch (err) {
            if (loadingEl) loadingEl.remove();
            addMessage('Network error. Please check your connection and try again.', 'ai');
        } finally {
            if (sendChatBtn) { sendChatBtn.disabled = false; sendChatBtn.textContent = 'Send'; }
        }
    }

    if (sendChatBtn) sendChatBtn.addEventListener('click', handleChatSubmit);
    if (chatInput) {
        chatInput.addEventListener('keypress', e => {
            if (e.key === 'Enter') handleChatSubmit();
        });
    }

    // Voice input for chat panel
    if (chatMicBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SR2 = window.SpeechRecognition || window.webkitSpeechRecognition;
        const chatRec = new SR2();
        chatRec.continuous = false;
        chatRec.interimResults = false;
        chatRec.lang = 'en-IN';

        chatMicBtn.addEventListener('click', () => {
            chatMicBtn.classList.add('mic-listening');
            chatRec.start();
        });
        chatRec.onresult = e => {
            chatMicBtn.classList.remove('mic-listening');
            if (chatInput) {
                chatInput.value = e.results[0][0].transcript;
                handleChatSubmit();
            }
        };
        chatRec.onerror = () => chatMicBtn.classList.remove('mic-listening');
        chatRec.onend   = () => chatMicBtn.classList.remove('mic-listening');
    }

    // ── Search Autocomplete (Employee dashboard) ───────────────────────────
    let suggestTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(suggestTimer);
            suggestTimer = setTimeout(async () => {
                const q = searchInput.value.trim();
                const suggBox = document.getElementById('suggestionBox');
                if (!suggBox || q.length < 2) {
                    if (suggBox) suggBox.classList.add('hidden');
                    return;
                }
                try {
                    const r = await fetch('/api/search?q=' + encodeURIComponent(q));
                    const d = await r.json();
                    if (d.suggestions && d.suggestions.length > 0) {
                        suggBox.innerHTML = d.suggestions.map(s =>
                            `<div class="px-4 py-2.5 hover:bg-blue-50 cursor-pointer text-sm text-gray-700 border-b border-gray-50 last:border-0"
                                  onclick="document.getElementById('searchInput').value='${s.replace(/'/g,"\\'")}';fetchPaginatedRules(1);this.parentElement.classList.add('hidden')">${s}</div>`
                        ).join('');
                        suggBox.classList.remove('hidden');
                    } else {
                        suggBox.classList.add('hidden');
                    }
                } catch(e) {}
            }, 250);
        });

        document.addEventListener('click', e => {
            const suggBox = document.getElementById('suggestionBox');
            if (suggBox && !searchInput.contains(e.target)) suggBox.classList.add('hidden');
        });
    }

    // ── Smooth year slider track fill ──────────────────────────────────────
    function updateSliderFill(slider) {
        if (!slider) return;
        const min = parseInt(slider.min), max = parseInt(slider.max), val = parseInt(slider.value);
        const pct = ((val - min) / (max - min)) * 100;
        slider.style.background = `linear-gradient(to right, #0f3a63 ${pct}%, #cbd5e1 ${pct}%)`;
    }

    if (yearSlider) {
        updateSliderFill(yearSlider);
        yearSlider.addEventListener('input', () => updateSliderFill(yearSlider));
    }

    // ── Back to Top Button ─────────────────────────────────────────────────
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', () => {
            backToTop.classList.toggle('visible', window.scrollY > 400);
        });
        backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    }

    // ── Keyboard Shortcut: '/' to focus search ─────────────────────────────
    document.addEventListener('keydown', e => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            searchInput?.focus();
        }
        if (e.key === 'Escape') closeChat();
    });

    // ── Animate cards on load ──────────────────────────────────────────────
    const cards = document.querySelectorAll('.rule-card, .dept-card, .admin-stat-card');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(16px)';
            observer.observe(card);
        });
    }

});


