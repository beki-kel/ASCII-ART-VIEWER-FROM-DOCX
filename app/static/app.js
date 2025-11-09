/**
 * ASCII Art Viewer - Competition Edition JavaScript
 * Handles WebSocket communication, form processing, and UI updates
 */

class ASCIIArtViewer {
    constructor() {
        this.websocket = null;
        this.currentSessionId = null;
        this.isProcessing = false;
        this.pollingInterval = null;
        this.backupPollingInterval = null;
        this.wsTimeout = null;
        this.lastReportedStep = null;
        
        this.initializeElements();
        this.attachEventListeners();
        this.logToTerminal('ASCII Art Viewer v3.0 initialized', 'success');
    }
    
    initializeElements() {
        // Form elements
        this.processForm = document.getElementById('processForm');
        this.urlInput = document.getElementById('urlInput');
        this.colorMode = document.getElementById('colorMode');
        this.outputFormat = document.getElementById('outputFormat');
        this.themeMode = document.getElementById('themeMode');
        this.processBtn = document.getElementById('processBtn');
        
        // Terminal elements
        this.terminal = document.getElementById('terminal');
        this.clearTerminalBtn = document.getElementById('clearTerminal');
        
        // Progress elements
        this.progressSection = document.getElementById('progressSection');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.metadataPanel = document.getElementById('metadataPanel');
        this.asciiDisplay = document.getElementById('asciiDisplay');
        this.asciiContent = document.getElementById('asciiContent');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.copyBtn = document.getElementById('copyBtn');
        
        // Metadata elements
        this.methodValue = document.getElementById('methodValue');
        this.dimensionsValue = document.getElementById('dimensionsValue');
        this.charactersValue = document.getElementById('charactersValue');
        this.timeValue = document.getElementById('timeValue');
    }
    
    attachEventListeners() {
        this.processForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.clearTerminalBtn.addEventListener('click', () => this.clearTerminal());
        this.downloadBtn.addEventListener('click', () => this.downloadResult());
        this.copyBtn.addEventListener('click', () => this.copyResult());
        
        // Theme change handler
        this.themeMode.addEventListener('change', (e) => this.changeTheme(e.target.value));
        
        // Test URL button handler
        const testUrlBtn = document.getElementById('testUrlBtn');
        if (testUrlBtn) {
            testUrlBtn.addEventListener('click', () => {
                this.urlInput.value = 'https://docs.google.com/document/d/e/2PACX-1vSmVmKxyqWZ-piMuUS251weVuIABoqm7tSyFP-GqpM9atKcV2ShZMmt5mA2-uDg_9kVFS7Q1jeB84m0/pub';
                this.logToTerminal('Test URL loaded', 'info');
            });
        }
        
        // Initialize theme
        this.changeTheme(this.themeMode.value);
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (this.isProcessing) {
            this.logToTerminal('Processing already in progress...', 'warning');
            return;
        }
        
        const url = this.urlInput.value.trim();
        if (!url) {
            this.logToTerminal('Please enter a valid URL', 'error');
            return;
        }
        
        this.startProcessing();
        this.logToTerminal(`Starting processing for: ${url}`, 'info');
        
        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    color_mode: this.colorMode.value,
                    output_format: this.outputFormat.value
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.currentSessionId = data.session_id;
            
            this.logToTerminal(`Session created: ${this.currentSessionId}`, 'success');
            this.connectWebSocket();
            
            // Also start gentle polling as backup
            setTimeout(() => {
                if (this.isProcessing) {
                    this.startBackupPolling();
                }
            }, 5000); // Start backup polling after 5 seconds
            
        } catch (error) {
            this.logToTerminal(`Error starting processing: ${error.message}`, 'error');
            this.stopProcessing();
        }
    }
    
    connectWebSocket() {
        if (!this.currentSessionId) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentSessionId}`;
        
        this.logToTerminal(`Connecting to WebSocket: ${wsUrl}`, 'info');
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.logToTerminal('WebSocket connected - receiving live updates', 'success');
            // Send a heartbeat to confirm connection
            this.websocket.send(JSON.stringify({type: 'client_ready', session_id: this.currentSessionId}));
            
            // Set a timeout to fallback to polling if no messages received
            this.wsTimeout = setTimeout(() => {
                if (this.isProcessing) {
                    this.logToTerminal('No WebSocket updates received, switching to polling', 'warning');
                    this.websocket.close();
                    this.startPolling();
                }
            }, 10000); // 10 seconds timeout
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            // Clear the timeout since we received a message
            if (this.wsTimeout) {
                clearTimeout(this.wsTimeout);
                this.wsTimeout = null;
            }
            
            // Ignore ping messages
            if (message.type !== 'ping') {
                this.handleWebSocketMessage(message);
            }
        };
        
        this.websocket.onclose = () => {
            this.logToTerminal('WebSocket connection closed - switching to polling', 'warning');
            this.startPolling();
        };
        
        this.websocket.onerror = (error) => {
            this.logToTerminal('WebSocket error - switching to polling', 'error');
            this.startPolling();
        };
    }
    
    startPolling() {
        if (!this.currentSessionId || !this.isProcessing) return;
        
        this.logToTerminal('Starting active polling for status updates', 'info');
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/session/${this.currentSessionId}`);
                const sessionData = await response.json();
                
                // Check if processing is complete
                if (sessionData.status === 'completed') {
                    this.displayResults(sessionData.ascii_art, sessionData.metadata);
                    this.logToTerminal('Processing completed successfully!', 'success');
                    this.stopProcessing();
                } else if (sessionData.status === 'failed') {
                    this.logToTerminal(`Processing failed: ${sessionData.error_message}`, 'error');
                    this.stopProcessing();
                } else {
                    // Update progress based on steps
                    const latestStep = sessionData.steps[sessionData.steps.length - 1];
                    if (latestStep && latestStep.message) {
                        this.logToTerminal(latestStep.message, 'info');
                        this.updateProgressFromStatus(latestStep.status, latestStep.message);
                    }
                }
            } catch (error) {
                this.logToTerminal(`Polling error: ${error.message}`, 'error');
            }
        }, 2000); // Poll every 2 seconds
    }
    
    startBackupPolling() {
        if (!this.currentSessionId || !this.isProcessing || this.pollingInterval) return;
        
        this.backupPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/session/${this.currentSessionId}`);
                const sessionData = await response.json();
                
                // Only update if we haven't received WebSocket updates
                if (sessionData.steps && sessionData.steps.length > 0) {
                    const latestStep = sessionData.steps[sessionData.steps.length - 1];
                    if (latestStep && !this.lastReportedStep || latestStep.timestamp !== this.lastReportedStep) {
                        this.logToTerminal(`[BACKUP] ${latestStep.message}`, 'info');
                        this.updateProgressFromStatus(latestStep.status, latestStep.message);
                        this.lastReportedStep = latestStep.timestamp;
                    }
                }
                
                // Check completion
                if (sessionData.status === 'completed' && sessionData.ascii_art) {
                    this.displayResults(sessionData.ascii_art, sessionData.metadata);
                    this.logToTerminal('Processing completed successfully!', 'success');
                    this.stopProcessing();
                } else if (sessionData.status === 'failed') {
                    this.logToTerminal(`Processing failed: ${sessionData.error_message}`, 'error');
                    this.stopProcessing();
                }
            } catch (error) {
                // Silent backup polling errors
            }
        }, 3000); // Less frequent backup polling
    }
    
    updateProgressFromStatus(status, message) {
        const progressSteps = {
            'fetching': 20,
            'parsing': 40,
            'extracting': 60,
            'enhancing': 80,
            'completed': 100
        };
        
        const progress = progressSteps[status] || 0;
        this.updateProgress(progress, message);
    }
    
    handleWebSocketMessage(message) {
        const { type, data } = message;
        
        switch (type) {
            case 'step_update':
                this.handleStepUpdate(data);
                break;
            case 'progress':
                this.updateProgress(data.progress, data.message);
                break;
            case 'completed':
                this.handleCompletion(data);
                break;
            case 'error':
                this.handleError(data);
                break;
        }
    }
    
    handleStepUpdate(data) {
        const { status, message, step } = data;
        
        // Log to terminal with appropriate styling
        let logType = 'info';
        if (status === 'completed') logType = 'success';
        else if (status === 'failed') logType = 'error';
        
        this.logToTerminal(message, logType);
        
        // Update progress based on status
        const progressSteps = {
            'fetching': 20,
            'parsing': 40,
            'extracting': 60,
            'enhancing': 80,
            'completed': 100
        };
        
        const progress = progressSteps[status] || 0;
        this.updateProgress(progress, message);
        
        // Check if processing is complete
        if (status === 'completed') {
            setTimeout(() => this.fetchFinalResult(), 1000);
        } else if (status === 'failed') {
            this.stopProcessing();
        }
    }
    
    async fetchFinalResult() {
        try {
            const response = await fetch(`/api/session/${this.currentSessionId}`);
            const sessionData = await response.json();
            
            if (sessionData.ascii_art && sessionData.metadata) {
                this.displayResults(sessionData.ascii_art, sessionData.metadata);
                this.logToTerminal('Processing completed successfully!', 'success');
            }
            
        } catch (error) {
            this.logToTerminal(`Error fetching results: ${error.message}`, 'error');
        }
        
        this.stopProcessing();
    }
    
    displayResults(asciiArt, metadata) {
        // Show results section
        this.resultsSection.style.display = 'block';
        this.resultsSection.classList.add('slide-in');
        
        // Update metadata
        this.methodValue.textContent = metadata.extraction_method;
        this.dimensionsValue.textContent = `${metadata.width}×${metadata.height}`;
        this.charactersValue.textContent = `${metadata.character_count.toLocaleString()} (${metadata.unique_characters} unique)`;
        this.timeValue.textContent = `${metadata.extraction_time_ms}ms`;
        
        // Display ASCII art with color coding based on mode
        this.displayAsciiArt(asciiArt);
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayAsciiArt(art) {
        const colorMode = this.colorMode.value;
        let displayArt = art;
        
        // Apply color modes
        switch (colorMode) {
            case 'rainbow':
                displayArt = this.applyRainbowColors(art);
                break;
            case 'highlight':
                displayArt = this.applyHighlightColors(art);
                break;
            case 'gradient':
                displayArt = this.applyGradientColors(art);
                break;
            case 'matrix':
                displayArt = this.applyMatrixColors(art);
                break;
            case 'cyberpunk':
                displayArt = this.applyCyberpunkColors(art);
                break;
            case 'classic':
                displayArt = `<span style="color: #27ae60; font-family: 'Courier New', monospace;">${this.escapeHtml(art)}</span>`;
                break;
            default:
                displayArt = this.escapeHtml(art);
        }
        
        this.asciiContent.innerHTML = displayArt;
    }
    
    applyRainbowColors(art) {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b', '#eb4d4b', '#6c5ce7'];
        const lines = art.split('\n');
        
        return lines.map((line, index) => {
            const color = colors[index % colors.length];
            return `<span style="color: ${color}">${this.escapeHtml(line)}</span>`;
        }).join('\n');
    }
    
    applyHighlightColors(art) {
        const asciiChars = ['█', '▀', '▄', '▌', '▐', '░', '▒', '▓'];
        let highlightedArt = this.escapeHtml(art);
        
        asciiChars.forEach(char => {
            const regex = new RegExp(this.escapeRegex(char), 'g');
            highlightedArt = highlightedArt.replace(regex, 
                `<span style="background-color: #00d9ff; color: #000;">${char}</span>`
            );
        });
        
        return highlightedArt;
    }
    
    startProcessing() {
        this.isProcessing = true;
        this.processBtn.disabled = true;
        this.processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        this.progressSection.style.display = 'block';
        this.resultsSection.style.display = 'none';
        this.updateProgress(0, 'Initializing...');
    }
    
    stopProcessing() {
        this.isProcessing = false;
        this.processBtn.disabled = false;
        this.processBtn.innerHTML = '<i class="fas fa-play"></i> Extract ASCII Art';
        this.progressSection.style.display = 'none';
        
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        
        if (this.backupPollingInterval) {
            clearInterval(this.backupPollingInterval);
            this.backupPollingInterval = null;
        }
        
        if (this.wsTimeout) {
            clearTimeout(this.wsTimeout);
            this.wsTimeout = null;
        }
    }
    
    updateProgress(progress, message) {
        this.progressFill.style.width = `${progress}%`;
        this.progressText.textContent = message;
    }
    
    logToTerminal(message, type = 'info') {
        const line = document.createElement('div');
        line.className = 'terminal-line';
        
        const prompt = document.createElement('span');
        prompt.className = 'prompt';
        prompt.textContent = '$';
        
        const text = document.createElement('span');
        text.className = `text ${type}`;
        text.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        
        line.appendChild(prompt);
        line.appendChild(text);
        this.terminal.appendChild(line);
        
        // Auto-scroll to bottom
        this.terminal.scrollTop = this.terminal.scrollHeight;
    }
    
    clearTerminal() {
        this.terminal.innerHTML = `
            <div class="terminal-line">
                <span class="prompt">$</span>
                <span class="text">Terminal cleared</span>
            </div>
        `;
    }
    
    async downloadResult() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/session/${this.currentSessionId}`);
            const sessionData = await response.json();
            
            if (sessionData.ascii_art) {
                const blob = new Blob([sessionData.ascii_art], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ascii-art-${Date.now()}.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.logToTerminal('ASCII art downloaded successfully', 'success');
            }
        } catch (error) {
            this.logToTerminal(`Download failed: ${error.message}`, 'error');
        }
    }
    
    async copyResult() {
        if (!this.asciiContent.textContent) return;
        
        try {
            await navigator.clipboard.writeText(this.asciiContent.textContent);
            this.logToTerminal('ASCII art copied to clipboard', 'success');
            
            // Visual feedback
            this.copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                this.copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            }, 2000);
            
        } catch (error) {
            this.logToTerminal(`Copy failed: ${error.message}`, 'error');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    

    
    changeTheme(theme) {
        const root = document.documentElement;
        
        // Theme configurations
        const themes = {
            dark: {
                '--primary-color': '#00d9ff',
                '--secondary-color': '#ff6b6b',
                '--accent-color': '#4ecdc4',
                '--dark-bg': '#1a1a1a',
                '--darker-bg': '#0d1117',
                '--light-bg': '#21262d'
            },
            cyberpunk: {
                '--primary-color': '#ff0080',
                '--secondary-color': '#00ff80',
                '--accent-color': '#8000ff',
                '--dark-bg': '#0a0a0a',
                '--darker-bg': '#000000',
                '--light-bg': '#1a0a1a'
            },
            matrix: {
                '--primary-color': '#00ff41',
                '--secondary-color': '#008f11',
                '--accent-color': '#00ff80',
                '--dark-bg': '#0d1b0d',
                '--darker-bg': '#000800',
                '--light-bg': '#1a2e1a'
            },
            classic: {
                '--primary-color': '#4a90e2',
                '--secondary-color': '#e74c3c',
                '--accent-color': '#27ae60',
                '--dark-bg': '#2c3e50',
                '--darker-bg': '#1a252f',
                '--light-bg': '#34495e'
            }
        };
        
        const themeConfig = themes[theme] || themes.dark;
        
        Object.entries(themeConfig).forEach(([property, value]) => {
            root.style.setProperty(property, value);
        });
        
        this.logToTerminal(`Theme changed to: ${theme}`, 'info');
    }
    

    
    applyGradientColors(art) {
        const lines = art.split('\n');
        const colors = ['#ff0080', '#ff4080', '#ff8080', '#ffbf80', '#ffff80', '#bfff80', '#80ff80', '#80ffbf', '#80ffff', '#80bfff', '#8080ff', '#bf80ff'];
        
        return lines.map((line, index) => {
            const color = colors[index % colors.length];
            return `<span style="color: ${color}">${this.escapeHtml(line)}</span>`;
        }).join('\n');
    }
    
    applyMatrixColors(art) {
        const colors = ['#003300', '#006600', '#009900', '#00cc00', '#00ff00', '#33ff33', '#66ff66', '#99ff99'];
        const lines = art.split('\n');
        
        return lines.map((line, index) => {
            const color = colors[index % colors.length];
            return `<span style="color: ${color}; text-shadow: 0 0 5px ${color};">${this.escapeHtml(line)}</span>`;
        }).join('\n');
    }
    
    applyCyberpunkColors(art) {
        const colors = ['#ff0080', '#8000ff', '#0080ff', '#00ff80', '#ff8000'];
        const lines = art.split('\n');
        
        return lines.map((line, index) => {
            const color = colors[index % colors.length];
            return `<span style="color: ${color}; text-shadow: 0 0 10px ${color};">${this.escapeHtml(line)}</span>`;
        }).join('\n');
    }
    

    
    handleError(data) {
        this.logToTerminal(`Processing error: ${data.message}`, 'error');
        this.stopProcessing();
    }
    
    handleCompletion(data) {
        this.logToTerminal('Processing completed successfully!', 'success');
        this.updateProgress(100, 'Completed');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ASCIIArtViewer();
});

// Add some visual effects
document.addEventListener('DOMContentLoaded', () => {
    // Add particle background effect
    const createParticle = () => {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 2px;
            height: 2px;
            background: #00d9ff;
            border-radius: 50%;
            pointer-events: none;
            z-index: -1;
            animation: float 6s linear infinite;
            left: ${Math.random() * 100}vw;
            animation-delay: ${Math.random() * 6}s;
        `;
        
        document.body.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
        }, 6000);
    };
    
    // Create particles periodically
    setInterval(createParticle, 500);
    
    // Add CSS for particle animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.1; }
            90% { opacity: 0.1; }
            100% { transform: translateY(-100px) rotate(360deg); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
});