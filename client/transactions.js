const API_BASE = 'http://localhost:5000';

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadTransactions();
});

// Refresh button
document.getElementById('refreshBtn').addEventListener('click', () => {
    loadStats();
    loadTransactions();
});

// Filter change handlers
document.getElementById('userFilter').addEventListener('change', loadTransactions);
document.getElementById('typeFilter').addEventListener('change', loadTransactions);

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/transactions/stats`);
        
        if (!response.ok) {
            throw new Error('Failed to load stats');
        }
        
        const data = await response.json();
        
        document.getElementById('totalStat').textContent = data.total || 0;
        document.getElementById('normalStat').textContent = data.normal || 0;
        document.getElementById('anomalyStat').textContent = data.anomalous || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('totalStat').textContent = 'Error';
        document.getElementById('normalStat').textContent = 'Error';
        document.getElementById('anomalyStat').textContent = 'Error';
    }
}

// Load transactions with filters
async function loadTransactions() {
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = '<tr><td colspan="9" class="loading">Loading...</td></tr>';
    
    try {
        const userFilter = document.getElementById('userFilter').value;
        const typeFilter = document.getElementById('typeFilter').value;
        
        let url = `${API_BASE}/transactions?limit=100`;
        if (userFilter) url += `&user_id=${userFilter}`;
        if (typeFilter) url += `&is_anomaly=${typeFilter}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.transactions || data.transactions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <div>No transactions found</div>
                        <div style="margin-top: 10px;">
                            <a href="index.html" style="color: #667eea;">Generate some transactions</a>
                        </div>
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = data.transactions.map(txn => `
                <tr>
                    <td><code style="font-size: 0.85em;">${txn.transaction_id.substring(0, 12)}...</code></td>
                    <td>${new Date(txn.timestamp).toLocaleString()}</td>
                    <td>${txn.user_name}</td>
                    <td class="amount-cell" style="color: #667eea; font-weight: 600;">$${txn.amount.toFixed(2)}</td>
                    <td>${txn.merchant}</td>
                    <td>${txn.merchant_category}</td>
                    <td>${txn.location}</td>
                    <td>${txn.amount_ratio.toFixed(2)}x</td>
                    <td>
                        <span class="badge ${txn.is_anomaly_label ? 'badge-anomaly' : 'badge-normal'}">
                            ${txn.is_anomaly_label ? 'ANOMALY' : 'NORMAL'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <div style="color: #dc3545;">Error loading transactions</div>
                    <div style="margin-top: 10px; font-size: 0.9em;">${error.message}</div>
                </td>
            </tr>
        `;
    }
}