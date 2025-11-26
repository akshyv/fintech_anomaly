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
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = `${user.name} (Avg: $${user.avg_transaction}, Age: ${user.account_age_days}d)`;
            select.appendChild(option);
        });
        
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
            <strong>Connection Successful!</strong>
            <p>Frontend (port 3000) → Backend (port 5000)</p>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
        resultBox.style.display = 'block';
        
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <strong>Connection Failed</strong>
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
        
        const txn = await response.json();
        
        // Display transaction
        displayTransaction(txn, resultBox);
        
        // Score the transaction
        await scoreTransaction(txn, resultBox);
        
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.innerHTML = `
            <strong>Generation Failed</strong>
            <p>${error.message}</p>
        `;
        resultBox.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Transaction';
    }
});

function displayTransaction(txn, container) {
    container.className = 'result-box success';
    container.innerHTML = `
        <strong>Transaction Generated</strong>
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
                    <span class="detail-value">${txn.amount_ratio.toFixed(2)}x avg</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Category Risk:</span>
                    <span class="detail-value">${(txn.category_risk * 100).toFixed(0)}%</span>
                </div>
            </div>
        </div>
        <div id="mlScoring" style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; text-align: center; color: #666;">
            Scoring with ML model...
        </div>
    `;
    container.style.display = 'block';
}

async function scoreTransaction(txn, container) {
    const scoringDiv = container.querySelector('#mlScoring');
    
    try {
        const response = await fetch(`${API_BASE}/score-transaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(txn)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to score transaction');
        }
        
        const result = await response.json();
        displayMLScore(result, scoringDiv);
        
    } catch (error) {
        scoringDiv.innerHTML = `<div style="color: #721c24;">ML Scoring Error: ${error.message}</div>`;
    }
}

function displayMLScore(result, container) {
    const scorePercent = (result.anomaly_score * 100).toFixed(1);
    const scoreColor = result.anomaly_score > 0.7 ? '#dc2626' : 
                       result.anomaly_score > 0.4 ? '#f59e0b' : '#059669';
    
    let shapHtml = '';
    if (result.shap_features) {
        shapHtml = Object.entries(result.shap_features).map(([feature, value]) => `
            <div style="display: flex; justify-content: space-between; padding: 8px; background: white; border-radius: 4px; margin-bottom: 5px;">
                <span style="font-weight: 500;">${formatFeatureName(feature)}</span>
                <span style="font-family: monospace; color: ${value > 0 ? '#dc2626' : '#059669'};">
                    ${value > 0 ? '+' : ''}${value.toFixed(4)}
                </span>
            </div>
        `).join('');
    }
    
    container.innerHTML = `
        <div style="text-align: left;">
            <h4 style="margin: 0 0 10px 0; color: #333;">ML Anomaly Score</h4>
            
            <div style="background: #e9ecef; height: 30px; border-radius: 6px; overflow: hidden; position: relative; margin-bottom: 15px;">
                <div style="background: ${scoreColor}; height: 100%; width: ${scorePercent}%; transition: width 0.5s;"></div>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-weight: 700; color: #1f2937;">
                    ${scorePercent}%
                </div>
            </div>
            
            <h5 style="margin: 15px 0 10px 0; color: #555;">Top Contributing Features (SHAP)</h5>
            <div style="background: #f8f9fa; padding: 10px; border-radius: 6px;">
                ${shapHtml}
            </div>
            
            <div style="margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 4px; font-size: 0.9em; color: #1565c0;">
                <strong>Note:</strong> Positive values increase anomaly score, negative values decrease it.
            </div>
        </div>
    `;
}

function formatFeatureName(feature) {
    const names = {
        'amount_ratio': 'Amount Ratio',
        'hour': 'Hour of Day',
        'day_of_week': 'Day of Week',
        'category_risk': 'Category Risk',
        'account_age_days': 'Account Age'
    };
    return names[feature] || feature;
}