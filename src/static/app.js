/**
 * Autonomous Newsroom - Frontend Application
 * Obsługuje komunikację z API i aktualizację UI
 */

const API_BASE = '';  // Relative URL

// === DOM Elements ===
const topicForm = document.getElementById('topic-form');
const topicInput = document.getElementById('topic');
const iterationsSelect = document.getElementById('iterations');
const submitBtn = document.getElementById('submit-btn');
const statusBox = document.getElementById('status-box');
const statusIcon = document.getElementById('status-icon');
const statusText = document.getElementById('status-text');
const progressBar = document.getElementById('progress');
const currentStep = document.getElementById('current-step');
const logsContainer = document.getElementById('logs-container');
const clearLogsBtn = document.getElementById('clear-logs-btn');
const resultContainer = document.getElementById('result-container');
const apiStatusEl = document.getElementById('api-status');

// === State ===
let isProcessing = false;
let eventSource = null;
let lastLogCount = 0;
let currentTopic = '';  // Aktualny temat - do filtrowania logów

// === Inicjalizacja ===
document.addEventListener('DOMContentLoaded', () => {
    checkApiHealth();
    setInterval(checkApiHealth, 30000); // Sprawdzaj co 30s
    
    topicForm.addEventListener('submit', handleSubmit);
    clearLogsBtn.addEventListener('click', clearLogs);
});

// === API Health Check ===
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            apiStatusEl.className = 'api-status online';
            apiStatusEl.innerHTML = '<span class="status-dot"></span>API: Online';
        } else {
            throw new Error('API error');
        }
    } catch (e) {
        apiStatusEl.className = 'api-status offline';
        apiStatusEl.innerHTML = '<span class="status-dot"></span>API: Offline';
    }
}

// === Form Submit ===
async function handleSubmit(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    const topic = topicInput.value.trim();
    const maxIterations = parseInt(iterationsSelect.value);
    
    if (!topic) {
        alert('Wpisz temat artykułu!');
        return;
    }
    
    startProcessing(topic, maxIterations);
}

// === Start Processing ===
async function startProcessing(topic, maxIterations) {
    isProcessing = true;
    
    // UI: Pokaż loading
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').classList.add('hidden');
    submitBtn.querySelector('.btn-loading').classList.remove('hidden');
    
    // Pokaż status box
    statusBox.classList.remove('hidden');
    updateStatus('⏳', 'Wysyłanie zlecenia...', 5);
    
    // Wyczyść poprzednie wyniki i zresetuj flagi
    clearLogs();
    completionHandled = false;  // Reset flagi zakończenia
    resultContainer.innerHTML = '<div class="result-placeholder">Oczekiwanie na wyniki...</div>';
    
    try {
        // Wyślij zlecenie do API
        const response = await fetch(`${API_BASE}/start-cycle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, max_iterations: maxIterations })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Zlecenie przyjęte:', data);
        
        updateStatus('🔄', 'Agenci pracują...', 10);
        addLog('INFO', `Zlecenie przyjęte: "${topic}"`);
        
        // Rozpocznij polling logów
        startLogPolling(topic);
        
    } catch (error) {
        console.error('Błąd:', error);
        updateStatus('❌', `Błąd: ${error.message}`, 0);
        addLog('ERROR', `Błąd wysyłania: ${error.message}`);
        stopProcessing();
    }
}

// === Log Polling ===
let pollInterval = null;

function startLogPolling(topic) {
    lastLogCount = 0;
    currentTopic = topic;  // Zapamiętaj aktualny temat
    
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/logs?lines=100`);
            const logsText = await response.text();
            
            // Parsuj logi i aktualizuj UI
            const lines = logsText.trim().split('\n').filter(l => l);
            
            // Dodaj tylko nowe logi
            if (lines.length > lastLogCount) {
                const newLines = lines.slice(lastLogCount);
                newLines.forEach(line => parseAndAddLog(line));
                lastLogCount = lines.length;
                
                // Sprawdź czy zakończono
                checkForCompletion(logsText);
            }
            
        } catch (e) {
            console.error('Błąd pobierania logów:', e);
        }
    }, 1000); // Co 1 sekundę
}

function stopLogPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// === Parse Log Line ===
function parseAndAddLog(line) {
    // Format: "2026-02-02 12:34:56 | INFO     | Message"
    const match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| (.+)$/);
    
    if (match) {
        const [, time, level, message] = match;
        addLog(level.trim(), message, time.split(' ')[1]); // Tylko godzina
        updateProgressFromLog(message);
    } else {
        // Fallback dla innych formatów
        addLog('INFO', line);
    }
}

// === Add Log Entry ===
function addLog(level, message, time = null) {
    // Usuń placeholder
    const placeholder = logsContainer.querySelector('.log-placeholder');
    if (placeholder) placeholder.remove();
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    // Dodaj specjalne klasy
    if (message.includes('[STEP') || message.includes('[1/') || message.includes('[2/') || message.includes('[3/') || message.includes('[4/')) {
        entry.classList.add('step');
    }
    if (message.includes('ITERATION')) {
        entry.classList.add('iteration');
    }
    if (message.includes('APPROVED') || message.includes('SUCCESS') || message.includes('ZAAKCEPTOWANY')) {
        entry.classList.add('success');
    }
    
    const timeStr = time || new Date().toLocaleTimeString('pl-PL');
    
    entry.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-level ${level}">${level}</span>
        <span class="log-message">${escapeHtml(message)}</span>
    `;
    
    logsContainer.appendChild(entry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// === Update Progress from Log ===
function updateProgressFromLog(message) {
    if (message.includes('RESEARCH AGENT') || message.includes('[1/')) {
        updateStatus('🔍', 'Research Agent zbiera fakty...', 25);
        currentStep.textContent = 'Krok 1/4: Zbieranie źródeł i faktów';
    }
    else if (message.includes('WRITER AGENT') || message.includes('[2/')) {
        updateStatus('✍️', 'Writer Agent pisze artykuł...', 50);
        currentStep.textContent = 'Krok 2/4: Generowanie artykułu';
    }
    else if (message.includes('CLICKBAIT') || message.includes('[3/')) {
        updateStatus('🤖', 'ML sprawdza clickbait...', 65);
        currentStep.textContent = 'Krok 3/4: Analiza ML';
    }
    else if (message.includes('EDITOR AGENT') || message.includes('[4/')) {
        updateStatus('📋', 'Editor Agent ocenia...', 80);
        currentStep.textContent = 'Krok 4/4: Ocena redakcyjna';
    }
    else if (message.includes('ITERATION 2')) {
        updateStatus('🔄', 'Rewizja - iteracja 2...', 60);
        currentStep.textContent = 'Iteracja 2: Poprawianie artykułu';
    }
}

// === Check for Completion ===
let completionHandled = false;  // Zapobiega wielokrotnemu wywołaniu

function checkForCompletion(logsText) {
    if (completionHandled) return;  // Już obsłużone
    
    // Znajdź początek AKTUALNEGO cyklu - szukaj startu z naszym tematem
    const cycleStartMarker = `>>> START CYKLU: '${currentTopic}'`;
    const cycleStartIndex = logsText.lastIndexOf(cycleStartMarker);
    
    // Jeśli nie znaleziono startu aktualnego cyklu, czekaj
    if (cycleStartIndex === -1) {
        return;
    }
    
    // Analizuj tylko logi PO starcie aktualnego cyklu
    const relevantLogs = logsText.substring(cycleStartIndex);
    
    // Szukamy DOKŁADNYCH fraz końcowych (z orchestratora)
    if (relevantLogs.includes('>>> ARTICLE APPROVED!') || relevantLogs.includes('>>> ARTYKUL ZAAKCEPTOWANY')) {
        completionHandled = true;
        updateStatus('✅', 'Artykuł zaakceptowany!', 100);
        fetchResultWithRetry();
        stopProcessing();
    }
    else if (relevantLogs.includes('>>> ARTICLE REJECTED') || relevantLogs.includes('>>> ARTYKUL ODRZUCONY')) {
        completionHandled = true;
        updateStatus('❌', 'Artykuł odrzucony', 100);
        fetchResultWithRetry();
        stopProcessing();
    }
    else if (relevantLogs.includes('>>> CYKL ZAKONCZONY') || (relevantLogs.includes('MAX ITERATIONS') && relevantLogs.includes('REACHED'))) {
        completionHandled = true;
        updateStatus('✅', 'Artykuł gotowy (max iteracji)', 100);
        fetchResultWithRetry();
        stopProcessing();
    }
    else if (relevantLogs.includes('ORCHESTRATOR ERROR') || relevantLogs.includes('BLAD W PIPELINE')) {
        completionHandled = true;
        updateStatus('❌', 'Błąd w pipeline', 100);
        fetchResultWithRetry();
        stopProcessing();
    }
}

// === Fetch Result with Retry ===
async function fetchResultWithRetry(retries = 5, delay = 1000) {
    for (let i = 0; i < retries; i++) {
        try {
            // Poczekaj przed próbą
            await new Promise(resolve => setTimeout(resolve, delay));
            
            const response = await fetch(`${API_BASE}/last-result`);
            const result = await response.json();
            
            if (result.status === 'no_result') {
                console.log(`Brak wyniku - próba ${i + 1}/${retries}...`);
                continue;  // Spróbuj ponownie
            }
            
            displayResult(result);
            return;  // Sukces - zakończ
            
        } catch (e) {
            console.error(`Błąd pobierania wyniku (próba ${i + 1}):`, e);
        }
    }
    
    // Po wyczerpaniu prób
    resultContainer.innerHTML = '<div class="result-placeholder">❌ Nie udało się pobrać wyników. Sprawdź logi.</div>';
}

// === Display Result ===
function displayResult(result) {
    const statusLabels = {
        success: { icon: '✅', text: 'Zaakceptowany' },
        rejected: { icon: '❌', text: 'Odrzucony' },
        max_iterations: { icon: '⚠️', text: 'Max iteracji' },
        error: { icon: '❌', text: 'Błąd' },
        unknown: { icon: '❓', text: 'Nieznany status' }
    };
    
    const statusInfo = statusLabels[result.status] || statusLabels.unknown;
    
    let html = `
        <div class="result-article">
            <div class="result-status ${result.status}">
                ${statusInfo.icon} ${statusInfo.text}
            </div>
    `;
    
    // Artykuł
    if (result.article) {
        html += `<h3 class="article-title">${escapeHtml(result.article.title)}</h3>`;
        html += `<p class="article-lead">${escapeHtml(result.article.lead)}</p>`;
        
        // Pełna treść artykułu (body) - konwertuj Markdown na HTML
        if (result.article.body) {
            html += `<div class="article-body">${formatMarkdown(result.article.body)}</div>`;
        }
        
        // Tagi
        if (result.article.tags && result.article.tags.length > 0) {
            html += `<div class="tags-list">`;
            result.article.tags.forEach(tag => {
                html += `<span class="tag">#${escapeHtml(tag)}</span>`;
            });
            html += `</div>`;
        }
    }
    
    // Metadane i ocena
    html += `<div class="article-meta">`;
    html += `<span class="meta-item"><strong>Iteracje:</strong> ${result.iterations || '?'}</span>`;
    
    if (result.review) {
        html += `<span class="meta-item"><strong>Ocena:</strong> ${result.review.score}/10</span>`;
    }
    
    if (result.article && result.article.word_count) {
        html += `<span class="meta-item"><strong>Słów:</strong> ${result.article.word_count}</span>`;
    }
    html += `</div>`;
    
    // Feedback od edytora
    if (result.review && (result.review.strengths?.length || result.review.weaknesses?.length)) {
        html += `<div class="review-section">`;
        html += `<h4>📋 Ocena redaktora</h4>`;
        
        if (result.review.strengths && result.review.strengths.length > 0) {
            html += `<div class="review-strengths"><strong>✅ Mocne strony:</strong><ul>`;
            result.review.strengths.forEach(s => html += `<li>${escapeHtml(s)}</li>`);
            html += `</ul></div>`;
        }
        
        if (result.review.weaknesses && result.review.weaknesses.length > 0) {
            html += `<div class="review-weaknesses"><strong>⚠️ Do poprawy:</strong><ul>`;
            result.review.weaknesses.forEach(w => html += `<li>${escapeHtml(w)}</li>`);
            html += `</ul></div>`;
        }
        
        html += `</div>`;
    }
    
    html += `</div>`;
    
    resultContainer.innerHTML = html;
}

// === Format Markdown to HTML ===
function formatMarkdown(text) {
    // Prosta konwersja Markdown → HTML
    let html = escapeHtml(text);
    
    // Nagłówki ## 
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    
    // Bold **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    
    // Italic *text*
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Listy - 
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Akapity (podwójne entery)
    html = html.split('\n\n').map(p => {
        if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<li')) {
            return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');
    
    return html;
}

// === Update Status ===
function updateStatus(icon, text, progress) {
    statusIcon.textContent = icon;
    statusText.textContent = text;
    progressBar.style.width = `${progress}%`;
}

// === Stop Processing ===
function stopProcessing() {
    isProcessing = false;
    stopLogPolling();
    
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').classList.remove('hidden');
    submitBtn.querySelector('.btn-loading').classList.add('hidden');
}

// === Clear Logs ===
function clearLogs() {
    logsContainer.innerHTML = '<div class="log-placeholder">Logi pojawią się tutaj po uruchomieniu agentów...</div>';
    lastLogCount = 0;
}

// === Escape HTML ===
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
