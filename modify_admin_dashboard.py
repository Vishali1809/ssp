import re
with open('templates/admin_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_tag = '<tbody id="adminRulesTable">'
start_idx = content.find(start_tag)
end_tag = '</tbody>'
end_idx = content.find(end_tag, start_idx)

if start_idx != -1 and end_idx != -1:
    replacement = """<tbody id="adminRulesTable">
                            <!-- Rows will be loaded via AJAX here -->
                        </tbody>"""
    
    # Also we need to add pagination controls after the table.
    # We can inject it after `</table>\n                </div>`
    table_end = content.find('</table>', end_idx)
    div_end = content.find('</div>', table_end)
    
    pagination_html = """
                <!-- Admin Rule Count & Pagination -->
                <div class="p-4 border-t border-gray-100 flex flex-col md:flex-row justify-between items-center gap-4 bg-gray-50">
                    <div id="adminRuleCountDisplay" class="text-sm font-medium text-gray-500">
                        <!-- Showing X-Y of Z rules -->
                    </div>
                    <div id="adminPaginationContainer" class="flex flex-wrap gap-1.5 justify-center">
                        <!-- Pagination buttons -->
                    </div>
                </div>
"""
    
    new_content = content[:start_idx] + replacement + content[end_idx + len(end_tag):div_end+6] + pagination_html + content[div_end+6:]
    with open('templates/admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Modified admin_dashboard.html successfully")
else:
    print("Could not find tags")
