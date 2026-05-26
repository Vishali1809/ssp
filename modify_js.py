import re
with open('static/js/main.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to replace `function filterRules() { ... }` with `async function fetchPaginatedRules(page=1) { ... }`
# And modify the event listeners to call it.

# Let's replace the whole section from `// ── Real-time rule card filtering` to `if (searchInput && searchInput.value) filterRules();`

start_idx = content.find('// ── Real-time rule card filtering')
end_idx = content.find('if (searchInput && searchInput.value) filterRules();')

if start_idx != -1 and end_idx != -1:
    end_idx += len('if (searchInput && searchInput.value) filterRules();')
    
    new_js = """// ── AJAX Pagination & Filtering ──────────────────────────────────────
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
"""
    # Wait, the voice search also updates `searchInput.value` and called `filterRules()`.
    # I should replace `filterRules()` with `fetchPaginatedRules(1)` in voice search.
    new_content = content[:start_idx] + new_js + content[end_idx:]
    new_content = new_content.replace('filterRules()', 'fetchPaginatedRules(1)')
    
    with open('static/js/main.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Modified main.js successfully")
else:
    print("Could not find filterRules tags")
