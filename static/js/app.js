// Stats counters
let stats = {
    live: 0,
    dead: 0,
    invalid: 0,
    unknown: 0
};

// Store LIVE cards for export
let liveCards = [];

// File upload handler
document.getElementById('file-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        document.getElementById('file-name').textContent = file.name;
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.content) {
                document.getElementById('cards-input').value = data.content;
            } else if (data.error) {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error uploading file');
        });
    }
});

// Start checking
function startCheck() {
    const cardsInput = document.getElementById('cards-input').value.trim();
    
    if (!cardsInput) {
        alert('Please enter card list!');
        return;
    }
    
    // Reset stats and live cards
    stats = { live: 0, dead: 0, invalid: 0, unknown: 0 };
    liveCards = [];
    updateStats();
    
    // Clear results
    document.getElementById('results').innerHTML = '';
    
    // Disable buttons
    const btn = document.getElementById('check-btn');
    const exportBtn = document.getElementById('export-btn');
    btn.disabled = true;
    btn.textContent = '⏳ Checking...';
    exportBtn.disabled = true;
    
    // Send request
    fetch('/api/check', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ cards: cardsInput })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'started') {
            // Start listening to SSE stream
            listenToStream();
        } else if (data.error) {
            alert('Error: ' + data.error);
            btn.disabled = false;
            btn.textContent = '🚀 Start Checking';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error connecting to server');
        btn.disabled = false;
        btn.textContent = '🚀 Start Checking';
    });
}

// Listen to SSE stream
function listenToStream() {
    const eventSource = new EventSource('/api/stream');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'result') {
            addResult(data);
        } else if (data.type === 'log') {
            addLog(data.message);
        } else if (data.type === 'complete') {
            addLog(data.message);
            eventSource.close();
            
            // Re-enable button
            const btn = document.getElementById('check-btn');
            btn.disabled = false;
            btn.textContent = '🚀 Start Checking';
            
            // Enable export button if there are LIVE cards
            const exportBtn = document.getElementById('export-btn');
            if (liveCards.length > 0) {
                exportBtn.disabled = false;
            }
        } else if (data.type === 'error') {
            addLog('ERROR: ' + data.message);
            eventSource.close();
            
            const btn = document.getElementById('check-btn');
            btn.disabled = false;
            btn.textContent = '🚀 Start Checking';
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        
        const btn = document.getElementById('check-btn');
        btn.disabled = false;
        btn.textContent = '🚀 Start Checking';
    };
}

// Add result to UI
function addResult(data) {
    const resultsDiv = document.getElementById('results');
    
    const resultItem = document.createElement('div');
    resultItem.className = `result-item ${data.status.toLowerCase()}`;
    
    resultItem.innerHTML = `
        <div class="result-card">${data.card}</div>
        <div class="result-message">${data.status}: ${data.message}</div>
    `;
    
    resultsDiv.insertBefore(resultItem, resultsDiv.firstChild);
    
    // Update stats
    const status = data.status.toLowerCase();
    if (stats.hasOwnProperty(status)) {
        stats[status]++;
        updateStats();
    }
    
    // Store LIVE cards (lưu format gốc user nhập)
    if (status === 'live') {
        liveCards.push(data.card_original || data.card);
    }
}

// Add log message
function addLog(message) {
    const resultsDiv = document.getElementById('results');
    
    const logItem = document.createElement('div');
    logItem.className = 'log-message';
    logItem.textContent = message;
    
    resultsDiv.insertBefore(logItem, resultsDiv.firstChild);
}

// Update stats display
function updateStats() {
    document.getElementById('stat-live').textContent = stats.live;
    document.getElementById('stat-dead').textContent = stats.dead;
    document.getElementById('stat-invalid').textContent = stats.invalid;
    document.getElementById('stat-unknown').textContent = stats.unknown;
}

// Export LIVE cards to file
function exportLiveCards() {
    if (liveCards.length === 0) {
        alert('No LIVE cards to export!');
        return;
    }
    
    // Create file content
    const content = liveCards.join('\n');
    
    // Create blob and download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    a.download = `live_cards_${timestamp}.txt`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    alert(`Exported ${liveCards.length} LIVE cards successfully!`);
}
