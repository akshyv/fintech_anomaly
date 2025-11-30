const API_BASE = 'http://localhost:5000';

// Global state
let currentTab = 'transactions';
let allTransactions = [];
let allAuditLogs = [];

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Transaction & Audit Logs page loaded');
    
    // Verify DOM elements exist
    if (!verifyDOMElements()) {
        console.error('❌ Critical DOM elements missing');
        return;
    }
    
    // Load initial data
    loadStats();
    loadTransactions();
    
    // Attach event listeners
    setupEventListeners();
});

function verifyDOMElements() {
    const requiredElements = [
        'userFilter', 'dateRangeFilter', 'searchFilter',
        'refreshBtn', 'exportBtn', 'transactionsBody', 'auditBody'
    ];
    
    for (const id of requiredElements) {
        if (!document.getElementById(id)) {
            console.error(`❌ Missing element: ${id}`);
            return false;
        }
    }
    
    console.log('✅ All required DOM elements found');
    return true;
}

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
    
    // Filters - with null checks
    const userFilter = document.getElementById('userFilter');
    const typeFilter = document.getElementById('typeFilter');
    const decisionFilter = document.getElementById('decisionFilter');
    const dateRangeFilter = document.getElementById('dateRangeFilter');
    const searchFilter = document.getElementById('searchFilter');
    
    if (userFilter) userFilter.addEventListener('change', applyFilters);
    if (typeFilter) typeFilter.addEventListener('change', applyFilters);
    if (decisionFilter) decisionFilter.addEventListener('change', applyFilters);
    if (dateRangeFilter) dateRangeFilter.addEventListener('change', applyFilters);
    if (searchFilter) searchFilter.addEventListener('input', debounce(applyFilters, 300));
    
    // Buttons
    const refreshBtn = document.getElementById('refreshBtn');
    const exportBtn = document.getElementById('exportBtn');
    
    if (refreshBtn) refreshBtn.addEventListener('click', refreshCurrentTab);
    if (exportBtn) exportBtn.addEventListener('click', exportToCSV);
}

// ========================================
// TAB SWITCHING
// ========================================

function switchTab(tabName) {
    console.log(`📑 Switching to ${tabName} tab`);
    
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
    
    // Show/hide appropriate filters
    const typeFilterGroup = document.getElementById('typeFilterGroup');
    const decisionFilterGroup = document.getElementById('decisionFilterGroup');
    
    if (tabName === 'transactions') {
        if (typeFilterGroup) typeFilterGroup.style.display = 'flex';
        if (decisionFilterGroup) decisionFilterGroup.style.display = 'none';
    } else {
        if (typeFilterGroup) typeFilterGroup.style.display = 'none';
        if (decisionFilterGroup) decisionFilterGroup.style.display = 'flex';
    }
    
    // Load data if not already loaded
    if (tabName === 'transactions' && allTransactions.length === 0) {
        loadTransactions();
    } else if (tabName === 'audit' && allAuditLogs.length === 0) {
        loadAuditLog();
    } else {
        // Apply filters to existing data
        applyFilters();
    }
}

// ========================================
// LOAD STATISTICS
// ========================================

async function loadStats() {
    console.log('📊 Loading statistics...');
    
    try {
        console.log(`🌐 Fetching from: ${API_BASE}/transactions/stats`);
        const response = await fetch(`${API_BASE}/transactions/stats`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Received stats:', data);
        
        // Animate stat updates
        animateStatUpdate('totalStat', data.total || 0);
        animateStatUpdate('normalStat', data.normal || 0);
        animateStatUpdate('anomalyStat', data.anomalous || 0);
        
        console.log('✅ Statistics loaded:', data);
        
    } catch (error) {
        console.error('❌ Error loading stats:', error);
        const totalStat = document.getElementById('totalStat');
        const normalStat = document.getElementById('normalStat');
        const anomalyStat = document.getElementById('anomalyStat');
        
        if (totalStat) totalStat.textContent = 'Error';
        if (normalStat) normalStat.textContent = 'Error';
        if (anomalyStat) anomalyStat.textContent = 'Error';
    }
}

function animateStatUpdate(elementId, newValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const oldValue = parseInt(element.textContent) || 0;
    
    if (oldValue === newValue) {
        element.textContent = newValue;
        return;
    }
    
    const duration = 500;
    const steps = 20;
    const increment = (newValue - oldValue) / steps;
    let current = oldValue;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        current += increment;
        
        if (step >= steps) {
            element.textContent = newValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current);
        }
    }, duration / steps);
}

// ========================================
// LOAD TRANSACTIONS
// ========================================

async function loadTransactions() {
    console.log('📋 Loading transactions...');
    
    const tbody = document.getElementById('transactionsBody');
    
    if (!tbody) {
        console.error('❌ transactionsBody element not found');
        return;
    }
    
    tbody.innerHTML = `
        <tr>
            <td colspan="9" class="loading">
                <div class="spinner"></div>
                <p>Loading transactions...</p>
            </td>
        </tr>
    `;
    
    try {
        console.log(`🌐 Fetching from: ${API_BASE}/transactions?limit=1000`);
        const response = await fetch(`${API_BASE}/transactions?limit=1000`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Received data:', data);
        
        allTransactions = data.transactions || [];
        
        console.log(`✅ Loaded ${allTransactions.length} transactions`);
        
        // Apply filters to display
        if (allTransactions.length > 0) {
            applyFilters();
        } else {
            console.log('⚠️ No transactions found, displaying empty state');
            displayTransactions([]);
        }
        
    } catch (error) {
        console.error('❌ Error loading transactions:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <div style="color: #dc3545;">⚠️ Error loading transactions</div>
                    <p style="margin-top: 10px; font-size: 0.9em;">${error.message}</p>
                    <p style="margin-top: 5px; font-size: 0.85em; color: #718096;">
                        Check that the backend is running on ${API_BASE}
                    </p>
                </td>
            </tr>
        `;
    }
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    if (!tbody) return;
    
    if (transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>No transactions found</p>
                    <div style="margin-top: 10px;">
                        <a href="index.html">Generate some transactions</a>
                    </div>
                </td>
            </tr>
        `;
        
        const transactionsCount = document.getElementById('transactionsCount');
        if (transactionsCount) transactionsCount.textContent = '0 transactions';
        return;
    }
    
    tbody.innerHTML = transactions.map(txn => {
        const date = new Date(txn.timestamp);
        const timeStr = date.toLocaleString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit', 
            minute: '2-digit'
        });
        
        return `
            <tr>
                <td>
                    <span class="code-text" title="${txn.transaction_id}">
                        ${txn.transaction_id.substring(0, 12)}...
                    </span>
                </td>
                <td style="white-space: nowrap;">${timeStr}</td>
                <td><strong>${txn.user_name}</strong></td>
                <td class="amount-cell" style="color: #667eea;">$${txn.amount.toFixed(2)}</td>
                <td>${txn.merchant}</td>
                <td>${txn.merchant_category}</td>
                <td>${txn.location}</td>
                <td style="text-align: center;">${txn.amount_ratio.toFixed(2)}x</td>
                <td>
                    <span class="badge ${txn.is_anomaly_label ? 'badge-anomaly' : 'badge-normal'}">
                        ${txn.is_anomaly_label ? 'ANOMALY' : 'NORMAL'}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
    
    const transactionsCount = document.getElementById('transactionsCount');
    if (transactionsCount) {
        transactionsCount.textContent = 
            `${transactions.length} transaction${transactions.length !== 1 ? 's' : ''}`;
    }
}

// ========================================
// LOAD AUDIT LOG
// ========================================

async function loadAuditLog() {
    console.log('🔒 Loading audit log...');
    
    const tbody = document.getElementById('auditBody');
    
    if (!tbody) {
        console.error('❌ auditBody element not found');
        return;
    }
    
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="loading">
                <div class="spinner"></div>
                <p>Loading audit log...</p>
            </td>
        </tr>
    `;
    
    try {
        console.log(`🌐 Fetching from: ${API_BASE}/audit-log?limit=1000`);
        const response = await fetch(`${API_BASE}/audit-log?limit=1000`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Received audit data:', data);
        
        allAuditLogs = data.logs || [];
        
        console.log(`✅ Loaded ${allAuditLogs.length} audit entries`);
        
        // Apply filters to display
        if (allAuditLogs.length > 0) {
            applyFilters();
        } else {
            console.log('⚠️ No audit entries found, displaying empty state');
            displayAuditLog([]);
        }
        
    } catch (error) {
        console.error('❌ Error loading audit log:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <div style="color: #dc3545;">⚠️ Error loading audit log</div>
                    <p style="margin-top: 10px; font-size: 0.9em;">${error.message}</p>
                    <p style="margin-top: 5px; font-size: 0.85em; color: #718096;">
                        Check that the backend is running on ${API_BASE}
                    </p>
                </td>
            </tr>
        `;
    }
}

function displayAuditLog(logs) {
    const tbody = document.getElementById('auditBody');
    if (!tbody) return;
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <p>No audit entries yet</p>
                    <div style="margin-top: 10px;">
                        <a href="index.html">Generate and score transactions</a>
                    </div>
                </td>
            </tr>
        `;
        
        const auditCount = document.getElementById('auditCount');
        if (auditCount) auditCount.textContent = '0 audit entries';
        return;
    }
    
    tbody.innerHTML = logs.map(log => {
        const date = new Date(log.timestamp);
        const timeStr = date.toLocaleString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit', 
            minute: '2-digit'
        });
        
        // Determine decision badge class
        let decisionClass = 'badge-review';
        if (log.decision === 'APPROVE') decisionClass = 'badge-approve';
        else if (log.decision === 'DECLINE') decisionClass = 'badge-decline';
        
        // Color code risk score
        let riskClass = 'risk-low';
        if (log.risk_score > 0.7) riskClass = 'risk-high';
        else if (log.risk_score > 0.4) riskClass = 'risk-medium';
        
        // Format risk components
        let componentsStr = '-';
        if (log.risk_components) {
            try {
                const components = typeof log.risk_components === 'string' 
                    ? JSON.parse(log.risk_components) 
                    : log.risk_components;
                
                componentsStr = Object.entries(components)
                    .map(([key, val]) => `${key}: ${(val.contribution * 100).toFixed(0)}%`)
                    .join(', ');
            } catch (e) {
                console.error('Error parsing risk components:', e);
            }
        }
        
        // Truncate explanation
        const explanation = log.explanation 
            ? (log.explanation.length > 100 
                ? log.explanation.substring(0, 100) + '...' 
                : log.explanation)
            : '<em style="color: #aaa;">Pending</em>';
        
        return `
            <tr>
                <td style="text-align: center;"><strong>#${log.id}</strong></td>
                <td style="white-space: nowrap;">${timeStr}</td>
                <td><strong>${log.user_id}</strong></td>
                <td>
                    <span class="code-text" title="${log.transaction_id}">
                        ${log.transaction_id ? String(log.transaction_id).substring(0, 10) + '...' : '-'}
                    </span>
                </td>
                <td class="risk-score-cell ${riskClass}">
                    ${(log.risk_score * 100).toFixed(1)}%
                </td>
                <td>
                    <span class="badge ${decisionClass}">${log.decision}</span>
                </td>
                <td>
                    <span class="truncate risk-components-mini" title="${componentsStr}">
                        ${componentsStr}
                    </span>
                </td>
                <td>
                    <span class="truncate" title="${log.explanation || 'Pending'}">
                        ${explanation}
                    </span>
                </td>
            </tr>
        `;
    }).join('');
    
    const auditCount = document.getElementById('auditCount');
    if (auditCount) {
        auditCount.textContent = 
            `${logs.length} audit entr${logs.length !== 1 ? 'ies' : 'y'}`;
    }
}

// ========================================
// FILTERING
// ========================================

function applyFilters() {
    console.log('🔍 Applying filters...');
    
    // Null checks for all filter elements
    const userFilterEl = document.getElementById('userFilter');
    const typeFilterEl = document.getElementById('typeFilter');
    const decisionFilterEl = document.getElementById('decisionFilter');
    const dateRangeFilterEl = document.getElementById('dateRangeFilter');
    const searchFilterEl = document.getElementById('searchFilter');
    
    if (!userFilterEl || !dateRangeFilterEl || !searchFilterEl) {
        console.error('❌ Filter elements not found in DOM');
        return;
    }
    
    const userFilter = userFilterEl.value.toLowerCase();
    const typeFilter = typeFilterEl ? typeFilterEl.value : '';
    const decisionFilter = decisionFilterEl ? decisionFilterEl.value : '';
    const dateRange = dateRangeFilterEl.value;
    const searchText = searchFilterEl.value.toLowerCase();
    
    if (currentTab === 'transactions') {
        let filtered = [...allTransactions];
        
        // User filter
        if (userFilter) {
            filtered = filtered.filter(t => t.user_id === userFilter);
        }
        
        // Type filter
        if (typeFilter) {
            const isAnomaly = typeFilter === 'true';
            filtered = filtered.filter(t => t.is_anomaly_label === isAnomaly);
        }
        
        // Date range filter
        filtered = filterByDateRange(filtered, dateRange);
        
        // Search filter (ID) - FIXED: Convert to string first
        if (searchText) {
            filtered = filtered.filter(t => 
                String(t.transaction_id).toLowerCase().includes(searchText)
            );
        }
        
        console.log(`✅ Filtered ${filtered.length}/${allTransactions.length} transactions`);
        displayTransactions(filtered);
        
    } else if (currentTab === 'audit') {
        let filtered = [...allAuditLogs];
        
        // User filter
        if (userFilter) {
            filtered = filtered.filter(a => a.user_id === userFilter);
        }
        
        // Decision filter
        if (decisionFilter) {
            filtered = filtered.filter(a => a.decision === decisionFilter);
        }
        
        // Date range filter
        filtered = filterByDateRange(filtered, dateRange);
        
        // Search filter (Transaction ID) - FIXED: Convert to string first
        if (searchText) {
            filtered = filtered.filter(a => 
                (a.transaction_id && String(a.transaction_id).toLowerCase().includes(searchText)) ||
                a.id.toString().includes(searchText)
            );
        }
        
        console.log(`✅ Filtered ${filtered.length}/${allAuditLogs.length} audit entries`);
        displayAuditLog(filtered);
    }
}

function filterByDateRange(items, range) {
    if (range === 'all') return items;
    
    const now = new Date();
    let cutoffDate;
    
    switch (range) {
        case 'today':
            cutoffDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            break;
        case 'week':
            cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
        case 'month':
            cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            break;
        default:
            return items;
    }
    
    return items.filter(item => new Date(item.timestamp) >= cutoffDate);
}

// ========================================
// REFRESH
// ========================================

function refreshCurrentTab() {
    console.log('🔄 Refreshing current tab...');
    
    // Reload stats
    loadStats();
    
    // Reload current tab data
    if (currentTab === 'transactions') {
        loadTransactions();
    } else {
        loadAuditLog();
    }
}

// ========================================
// CSV EXPORT
// ========================================

function exportToCSV() {
    console.log('📥 Exporting to CSV...');
    
    let csvContent = '';
    let filename = '';
    
    if (currentTab === 'transactions') {
        // Get currently filtered transactions
        const userFilter = document.getElementById('userFilter').value.toLowerCase();
        const typeFilterEl = document.getElementById('typeFilter');
        const typeFilter = typeFilterEl ? typeFilterEl.value : '';
        const dateRange = document.getElementById('dateRangeFilter').value;
        const searchText = document.getElementById('searchFilter').value.toLowerCase();
        
        let filtered = [...allTransactions];
        
        if (userFilter) filtered = filtered.filter(t => t.user_id === userFilter);
        if (typeFilter) {
            const isAnomaly = typeFilter === 'true';
            filtered = filtered.filter(t => t.is_anomaly_label === isAnomaly);
        }
        filtered = filterByDateRange(filtered, dateRange);
        if (searchText) filtered = filtered.filter(t => t.transaction_id.toLowerCase().includes(searchText));
        
        // Create CSV header
        csvContent = 'Transaction ID,Timestamp,User,Amount,Merchant,Category,Location,Amount Ratio,Type\n';
        
        // Add rows
        filtered.forEach(txn => {
            csvContent += `"${txn.transaction_id}","${txn.timestamp}","${txn.user_name}",${txn.amount},"${txn.merchant}","${txn.merchant_category}","${txn.location}",${txn.amount_ratio},"${txn.is_anomaly_label ? 'ANOMALY' : 'NORMAL'}"\n`;
        });
        
        filename = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
        
    } else if (currentTab === 'audit') {
        // Get currently filtered audit logs
        const userFilter = document.getElementById('userFilter').value.toLowerCase();
        const decisionFilterEl = document.getElementById('decisionFilter');
        const decisionFilter = decisionFilterEl ? decisionFilterEl.value : '';
        const dateRange = document.getElementById('dateRangeFilter').value;
        const searchText = document.getElementById('searchFilter').value.toLowerCase();
        
        let filtered = [...allAuditLogs];
        
        if (userFilter) filtered = filtered.filter(a => a.user_id === userFilter);
        if (decisionFilter) filtered = filtered.filter(a => a.decision === decisionFilter);
        filtered = filterByDateRange(filtered, dateRange);
        if (searchText) {
            filtered = filtered.filter(a => 
                (a.transaction_id && a.transaction_id.toLowerCase().includes(searchText)) ||
                a.id.toString().includes(searchText)
            );
        }
        
        // Create CSV header
        csvContent = 'Audit ID,Timestamp,User,Transaction ID,Risk Score,Decision,Explanation\n';
        
        // Add rows
        filtered.forEach(log => {
            const explanation = log.explanation ? log.explanation.replace(/"/g, '""') : 'Pending';
            csvContent += `${log.id},"${log.timestamp}","${log.user_id}","${log.transaction_id || ''}",${log.risk_score},"${log.decision}","${explanation}"\n`;
        });
        
        filename = `audit_log_${new Date().toISOString().split('T')[0]}.csv`;
    }
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) { // IE 10+
        navigator.msSaveBlob(blob, filename);
    } else {
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    console.log(`✅ Exported to ${filename}`);
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Debounce function to limit search input calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}