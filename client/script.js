// Backend runs on port 5000, frontend on port 3000
const API_BASE = 'http://localhost:5000';

// Load user profiles on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserProfiles();
});

// Load user profiles into dropdown
async function loadUserProfiles() {
    const select = document.getElementById('userSelect');
    const generateBtn = document.getElementById('generateBtn');
    
    try {
        const response = await fetch(`${API_BASE}/users`);
        
        if (!response.ok) {
            throw new Error('Failed to load user profiles');
        }
        
        const data = await response.json();
        const users = data.users;
        
        // Clear loading option
        select.innerHTML = '<option value="">-- Select a customer --</option>';
        
        // Add user options
        for (const [userId, profile] of Object.entries(users)) {
            const option = document.createElement('option');
            option.value = userId;
            option.textContent = `${profile.name} (Avg: $${profile.avg_transaction}, Trust: ${(profile.trust_score * 100).toFixed(0)}%)`;
            select.appendChild(option);
        }
        
        // Enable generate button when user is selected
        select.addEventListener('change', () => {
            generateBtn.disabled = !select.value;
        });
        
    } catch (error) {
        select.innerHTML = '<option value="">Error loading users</option>';
        console.error('Error loading profiles:', error);
    }
}

// Health check button handler
document.getElementById('healthBtn').addEventListener('click', async () => {
    const resultBox = document.getElementById('healthResult');
    const btn = document.getElementById('healthBtn');
    
    btn.disabled = true;
    btn.textContent = 'Testing...';
    resultBox.className = 'result-box';
    resultBox.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/health`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        resultBox.className = 'result-box success';
        resultBox.innerHTML = `
            <strong>✅ Connection Successful!</strong>
            <p>Frontend (port 3000) → Backend (port 5000)</p>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
        resultBox.style.display = 'block';
        
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <strong>❌ Connection Failed</strong>
            <p>${error.message}</p>
        `;
        resultBox.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Test Backend Connection';
    }
});

// Generate transaction button handler
document.getElementById('generateBtn').addEventListener('click', async () => {
    const resultBox = document.getElementById('transactionResult');
    const btn = document.getElementById('generateBtn');
    const userSelect = document.getElementById('userSelect');
    const txnTypeRadios = document.getElementsByName('txnType');
    
    const userId = userSelect.value;
    const isAnomaly = Array.from(txnTypeRadios).find(r => r.checked).value === 'anomaly';
    
    if (!userId) {
        alert('Please select a customer');
        return;
    }
    
    // Show loading state
    btn.disabled = true;
    btn.textContent = 'Generating...';
    resultBox.className = 'result-box';
    resultBox.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/generate-transaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                is_anomaly: isAnomaly
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate transaction');
        }
        
        const data = await response.json();
        const txn = data.transaction;
        
        // Display transaction in a nice format
        resultBox.className = 'result-box success';
        resultBox.innerHTML = `
            <strong>✅ Transaction Generated</strong>
            <div class="transaction-card">
                <div class="transaction-header">
                    <div>
                        <div class="transaction-amount">$${txn.amount.toFixed(2)}</div>
                        <div class="transaction-id">${txn.transaction_id}</div>
                    </div>
                    <span class="badge ${txn.is_anomaly_label ? 'badge-anomaly' : 'badge-normal'}">
                        ${txn.is_anomaly_label ? 'ANOMALOUS' : 'NORMAL'}
                    </span>
                </div>
                <div class="transaction-details">
                    <div class="detail-item">
                        <span class="detail-label">Customer:</span>
                        <span class="detail-value">${txn.user_name}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Merchant:</span>
                        <span class="detail-value">${txn.merchant}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Category:</span>
                        <span class="detail-value">${txn.merchant_category}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Location:</span>
                        <span class="detail-value">${txn.location}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Amount Ratio:</span>
                        <span class="detail-value">${txn.amount_ratio}x avg</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Category Risk:</span>
                        <span class="detail-value">${(txn.category_risk * 100).toFixed(0)}%</span>
                    </div>
                </div>
            </div>
            <details style="margin-top: 15px;">
                <summary style="cursor: pointer; font-weight: 600; color: #667eea;">View Full JSON</summary>
                <pre>${JSON.stringify(txn, null, 2)}</pre>
            </details>
        `;
        resultBox.style.display = 'block';
        
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <strong>❌ Generation Failed</strong>
            <p>${error.message}</p>
        `;
        resultBox.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Transaction';
    }
});