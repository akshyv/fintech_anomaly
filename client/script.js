const API_URL = 'http://localhost:5000';

let currentTransaction = null;
let currentUserProfile = null;
let currentMLScore = null;

async function loadUsers() {
    try {
        const response = await fetch(`${API_URL}/users`);
        if (!response.ok) throw new Error('Failed to load users');
        
        const data = await response.json();
        console.log('Users data:', data); // Debug log
        console.log('Type of data:', typeof data);
        console.log('Is data an array?', Array.isArray(data));
        console.log('data.users exists?', data.users);
        console.log('Is data.users an array?', Array.isArray(data.users));
        
        const userSelect = document.getElementById('userSelect');
        
        // Handle both cases: {users: [...]} or [...]
        let users;
        if (Array.isArray(data)) {
            users = data;
        } else if (data.users && Array.isArray(data.users)) {
            users = data.users;
        } else {
            console.error('Invalid users data:', data);
            showError('Invalid user data received');
            return;
        }
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = `${user.name} (${user.location}, ${user.account_age_days} days old)`;
            userSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading users:', error);
        showError('Failed to load users');
    }
}

async function generateTransaction() {
    const userId = document.getElementById('userSelect').value;
    const isAnomaly = document.querySelector('input[name="transactionType"]:checked').value === 'anomaly';
    
    if (!userId) {
        showError('Please select a user');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    // Clear previous results
    document.getElementById('results').style.display = 'none';
    document.getElementById('mlResults').style.display = 'none';
    document.getElementById('riskResults').style.display = 'none';
    
    try {
        // Step 1: Generate transaction
        const generateResponse = await fetch(`${API_URL}/generate-transaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, is_anomaly: isAnomaly })
        });
        
        if (!generateResponse.ok) throw new Error('Failed to generate transaction');
        currentTransaction = await generateResponse.json();
        
        // Get user profile
        const usersResponse = await fetch(`${API_URL}/users`);
        const usersData = await usersResponse.json();
        currentUserProfile = usersData.users.find(u => u.user_id === userId);
        
        displayTransaction(currentTransaction);
        
        // Step 2: Score with ML model
        await scoreTransaction();
        
        // Step 3: Calculate risk score
        await calculateRisk();
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Transaction';
    }
}

async function scoreTransaction() {
    if (!currentTransaction || !currentUserProfile) return;
    
    try {
        const response = await fetch(`${API_URL}/score-transaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transaction: currentTransaction,
                user_profile: currentUserProfile
            })
        });
        
        if (!response.ok) throw new Error('Failed to score transaction');
        const mlResult = await response.json();
        currentMLScore = mlResult.anomaly_score;
        
        displayMLScore(mlResult);
    } catch (error) {
        console.error('Error scoring transaction:', error);
        showError('Failed to score transaction');
    }
}

async function calculateRisk() {
    if (!currentTransaction || !currentUserProfile || currentMLScore === null) return;
    
    try {
        const response = await fetch(`${API_URL}/calculate-risk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transaction: currentTransaction,
                user_profile: currentUserProfile,
                ml_score: currentMLScore
            })
        });
        
        if (!response.ok) throw new Error('Failed to calculate risk');
        const riskResult = await response.json();
        
        displayRiskScore(riskResult);
        
        // Generate LLM explanation after risk calculation
        await generateExplanation(currentTransaction, riskResult);
        
    } catch (error) {
        console.error('Error calculating risk:', error);
        showError('Failed to calculate risk score');
    }
}

function displayTransaction(transaction) {
    document.getElementById('transactionData').textContent = JSON.stringify(transaction, null, 2);
    document.getElementById('results').style.display = 'block';
}

function displayMLScore(mlResult) {
    const scorePercent = (mlResult.anomaly_score * 100).toFixed(1);
    document.getElementById('anomalyScore').textContent = `${scorePercent}%`;
    
    const shapList = document.getElementById('shapFeatures');
    shapList.innerHTML = '';
    
    for (const [feature, value] of Object.entries(mlResult.shap_features)) {
        const li = document.createElement('li');
        const direction = value > 0 ? 'increases' : 'decreases';
        const absValue = Math.abs(value).toFixed(3);
        li.textContent = `${feature}: ${value > 0 ? '+' : ''}${value.toFixed(3)} (${direction} anomaly score by ${absValue})`;
        shapList.appendChild(li);
    }
    
    document.getElementById('mlResults').style.display = 'block';
}

function displayRiskScore(riskResult) {
    const riskPercent = (riskResult.risk_score * 100).toFixed(1);
    const decision = riskResult.decision;
    
    // Display risk score with color-coded bar
    document.getElementById('riskScore').textContent = `${riskPercent}%`;
    const riskBar = document.getElementById('riskScoreBar');
    riskBar.style.width = `${riskPercent}%`;
    
    // Color code based on risk level
    if (riskResult.risk_score > 0.7) {
        riskBar.style.backgroundColor = '#dc3545'; // Red
    } else if (riskResult.risk_score >= 0.4) {
        riskBar.style.backgroundColor = '#ffc107'; // Yellow
    } else {
        riskBar.style.backgroundColor = '#28a745'; // Green
    }
    
    // Display decision
    const decisionElement = document.getElementById('decision');
    decisionElement.textContent = decision;
    decisionElement.className = 'decision';
    
    if (decision === 'DECLINE') {
        decisionElement.classList.add('decline');
    } else if (decision === 'MANUAL REVIEW') {
        decisionElement.classList.add('manual-review');
    } else {
        decisionElement.classList.add('approve');
    }
    
    // Display component breakdown
    const componentsDiv = document.getElementById('riskComponents');
    componentsDiv.innerHTML = '';
    
    const components = riskResult.components;
    for (const [name, data] of Object.entries(components)) {
        const componentDiv = document.createElement('div');
        componentDiv.className = 'risk-component';
        
        const label = document.createElement('div');
        label.className = 'component-label';
        const displayName = name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        const contributionPercent = (data.contribution * 100).toFixed(1);
        label.textContent = `${displayName}: ${contributionPercent}% (value: ${data.value.toFixed(2)}, weight: ${data.weight})`;
        
        const barContainer = document.createElement('div');
        barContainer.className = 'component-bar-container';
        
        const bar = document.createElement('div');
        bar.className = 'component-bar';
        bar.style.width = `${contributionPercent * 2}%`; // Scale for visibility
        bar.style.backgroundColor = getComponentColor(data.contribution);
        
        barContainer.appendChild(bar);
        componentDiv.appendChild(label);
        componentDiv.appendChild(barContainer);
        componentsDiv.appendChild(componentDiv);
    }
    
    document.getElementById('riskResults').style.display = 'block';
}

function getComponentColor(contribution) {
    if (contribution > 0.25) return '#dc3545'; // High contribution - red
    if (contribution > 0.15) return '#ffc107'; // Medium contribution - yellow
    return '#17a2b8'; // Low contribution - blue
}

async function generateExplanation(transaction, riskData) {
    const llmLoading = document.getElementById('llmLoading');
    const llmContent = document.getElementById('llmContent');
    
    // Show loading state
    llmLoading.style.display = 'block';
    llmContent.innerHTML = '';
    
    try {
        console.log('🤖 Requesting LLM explanation from Groq...');
        
        const response = await fetch(`${API_URL}/explain-decision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                transaction: transaction,
                risk_components: riskData.components,
                decision: riskData.decision
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Hide loading, show explanation
        llmLoading.style.display = 'none';
        llmContent.innerHTML = `
            <div style="
                background: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 4px;
                line-height: 1.6;
                color: #2d3748;
                margin-top: 10px;
            ">
                <p style="margin: 0; white-space: pre-wrap;">${data.explanation}</p>
                <div style="
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid #e2e8f0;
                    font-size: 0.85em;
                    color: #718096;
                ">
                    <strong>Model:</strong> Llama 3.3 70B (via Groq) • 
                    <strong>Generated:</strong> ${new Date(data.timestamp).toLocaleTimeString()}
                </div>
            </div>
        `;
        
        console.log('✅ LLM explanation received');
        
    } catch (error) {
        console.error('❌ Error generating explanation:', error);
        llmLoading.style.display = 'none';
        llmContent.innerHTML = `
            <div style="
                background: #fff5f5;
                border-left: 4px solid #e53e3e;
                padding: 15px;
                border-radius: 4px;
                margin-top: 10px;
            ">
                <p style="color: #e53e3e; margin: 0; font-weight: 600;">
                    ⚠️ Could not generate explanation
                </p>
                <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #718096;">
                    Error: ${error.message}
                </p>
                <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #718096;">
                    The risk analysis is still valid. This is just the AI explanation that failed.
                </p>
            </div>
        `;
    }
}

function showError(message) {
    alert(`Error: ${message}`);
}

document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    document.getElementById('generateBtn').addEventListener('click', generateTransaction);
});