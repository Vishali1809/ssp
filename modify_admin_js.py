import re
with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('// Admin table search filter')
end_idx = content.find('// Edit Modal')

if start_idx != -1 and end_idx != -1:
    new_js = """// ── Admin AJAX Pagination & Filtering ──────────────────────────────────────
let adminCurrentPage = 1;

async function fetchAdminPaginatedRules(page = 1) {
    const tableBody = document.getElementById('adminRulesTable');
    const countDisplay = document.getElementById('adminRuleCountDisplay');
    const paginationContainer = document.getElementById('adminPaginationContainer');
    if (!tableBody) return;

    const q = document.getElementById('adminSearch').value.trim();
    const perPage = window.innerWidth < 768 ? 5 : 10;

    tableBody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-gray-500 animate-pulse">Loading rules...</td></tr>';

    try {
        const res = await fetch(`/api/admin/rules/html?q=${encodeURIComponent(q)}&page=${page}&per_page=${perPage}`);
        if (!res.ok) throw new Error('Network error');
        const data = await res.json();
        
        tableBody.innerHTML = data.html;
        adminCurrentPage = data.page;

        if (countDisplay) {
            if (data.total === 0) {
                countDisplay.textContent = 'No rules found';
            } else {
                const start = (adminCurrentPage - 1) * perPage + 1;
                const end = Math.min(adminCurrentPage * perPage, data.total);
                countDisplay.textContent = `Showing ${start}–${end} of ${data.total} rules`;
            }
        }

        if (paginationContainer) {
            renderAdminPagination(paginationContainer, data.page, data.total_pages, (newPage) => {
                fetchAdminPaginatedRules(newPage);
            });
        }
    } catch (err) {
        console.error('Error fetching admin rules:', err);
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center py-8 text-red-500">Error loading rules. Please try again.</td></tr>';
    }
}

function renderAdminPagination(container, current, total, onPageClick) {
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

    container.appendChild(createBtn('← Previous', current - 1, current === 1, false));
    
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
    container.appendChild(createBtn('Next →', current + 1, current === total, false));
}

function filterAdminTable(q) {
    fetchAdminPaginatedRules(1);
}

// Initial fetch
if (document.getElementById('adminRulesTable')) {
    fetchAdminPaginatedRules(1);
    
    // Handle window resize for mobile vs desktop limit change
    let lastWidth = window.innerWidth;
    window.addEventListener('resize', () => {
        const newWidth = window.innerWidth;
        if ((lastWidth < 768 && newWidth >= 768) || (lastWidth >= 768 && newWidth < 768)) {
            lastWidth = newWidth;
            fetchAdminPaginatedRules(1);
        }
    });
}

"""
    new_content = content[:start_idx] + new_js + content[end_idx:]
    with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Modified admin_dashboard.html JS successfully")
else:
    print("Could not find js tags")
