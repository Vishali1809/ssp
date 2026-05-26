import re
with open('templates/employee_dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_tag = '<div id="rulesContainer"'
start_idx = content.find(start_tag)
end_tag = '<!-- JS no-results message -->'
end_idx = content.find(end_tag)

if start_idx != -1 and end_idx != -1:
    replacement = """<div id="rulesContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Rules will be loaded via AJAX here -->
    </div>
    
    <!-- Rule Count & Pagination -->
    <div class="mt-8 flex flex-col md:flex-row justify-between items-center gap-4">
        <div id="ruleCountDisplay" class="text-sm font-medium text-gray-500">
            <!-- Showing X-Y of Z rules -->
        </div>
        <div id="paginationContainer" class="flex flex-wrap gap-1.5 justify-center">
            <!-- Pagination buttons -->
        </div>
    </div>

    <!-- JS no-results message -->"""
    
    new_content = content[:start_idx] + replacement + content[end_idx + len(end_tag):]
    with open('templates/employee_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Modified employee_dashboard.html successfully")
else:
    print("Could not find tags")
