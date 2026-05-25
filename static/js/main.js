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

    // ── Real-time rule card filtering ──────────────────────────────────────
    function filterRules() {
        if (!searchInput) return;
        const query       = searchInput.value.toLowerCase().trim();
        const selectedYear = yearSlider ? parseInt(yearSlider.value, 10) : 1969;
        const cards       = document.querySelectorAll('.rule-card-item');
        let visible       = 0;

        cards.forEach(card => {
            const title = card.dataset.title || '';
            const desc  = card.dataset.desc  || '';
            const dept  = card.dataset.dept  || '';
            const cat   = card.dataset.cat   || '';
            const year  = parseInt(card.dataset.year, 10);

            const textMatch = !query || title.includes(query) || desc.includes(query)
                              || dept.includes(query) || cat.includes(query);
            const yearMatch = selectedYear === 1969 || year === selectedYear;

            if (textMatch && yearMatch) {
                card.style.display = '';
                visible++;
            } else {
                card.style.display = 'none';
            }
        });

        if (visibleCount) visibleCount.textContent = visible;

        if (noResultsMsg) {
            noResultsMsg.classList.toggle('hidden', visible > 0 || cards.length === 0);
        }
    }

    if (searchInput) searchInput.addEventListener('input', filterRules);

    if (yearSlider) {
        yearSlider.addEventListener('input', e => {
            const val = parseInt(e.target.value, 10);
            if (yearDisplay) yearDisplay.textContent = val === 1969 ? 'All' : val;
            filterRules();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            if (yearSlider) { yearSlider.value = 1969; }
            if (yearDisplay) yearDisplay.textContent = 'All';
            filterRules();
        });
    }

    // Run initial filter (e.g. if URL ?q= was pre-filled)
    if (searchInput && searchInput.value) filterRules();

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
                filterRules();
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
                                  onclick="document.getElementById('searchInput').value='${s.replace(/'/g,"\\'")}';filterRules();this.parentElement.classList.add('hidden')">${s}</div>`
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

// Make filterRules global for inline calls
function filterRules() {
    const searchInput  = document.getElementById('searchInput');
    const yearSlider   = document.getElementById('yearSlider');
    const noResultsMsg = document.getElementById('noResultsMsg');
    const visibleCount = document.getElementById('visibleCount');
    if (!searchInput) return;

    const query        = searchInput.value.toLowerCase().trim();
    const selectedYear = yearSlider ? parseInt(yearSlider.value, 10) : 1969;
    const cards        = document.querySelectorAll('.rule-card-item');
    let visible        = 0;

    cards.forEach(card => {
        const title = card.dataset.title || '';
        const desc  = card.dataset.desc  || '';
        const dept  = card.dataset.dept  || '';
        const cat   = card.dataset.cat   || '';
        const year  = parseInt(card.dataset.year, 10);

        const textMatch = !query || title.includes(query) || desc.includes(query)
                          || dept.includes(query) || cat.includes(query);
        const yearMatch = selectedYear === 1969 || year === selectedYear;

        if (textMatch && yearMatch) { card.style.display = ''; visible++; }
        else card.style.display = 'none';
    });

    if (visibleCount) visibleCount.textContent = visible;
    if (noResultsMsg) noResultsMsg.classList.toggle('hidden', visible > 0 || cards.length === 0);
}
