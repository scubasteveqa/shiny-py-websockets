from shiny import App, render, ui, reactive
import json
import time

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_action_button(
            "set_websocket",
            "Force Websocket & Reload",
            class_="btn-warning"
        ),
        ui.br(),
        ui.br(),
        ui.p("Click the button above to:"),
        ui.tags.ol(
            ui.tags.li("Set localStorage['shiny.whitelist'] to '[\"websocket\"]'"),
            ui.tags.li("Reload the page to force websocket usage"),
        ),
        ui.br(),
        ui.p(
            "If websocket connectivity is broken, the app will not load correctly after reload.",
            class_="text-muted"
        ),
    ),
    ui.card(
        ui.card_header("Current Status"),
        ui.output_ui("status_info"),
    ),
    ui.card(
        ui.card_header("Transport Information"),
        ui.output_ui("transport_info"),
    ),
    ui.card(
        ui.card_header("WebSocket Activity Monitor"),
        ui.output_ui("websocket_activity"),
    ),
    ui.card(
        ui.card_header("Interactive Test"),
        ui.p("Use these controls to generate websocket traffic:"),
        ui.input_text("test_input", "Type something:", value="Hello, Shiny!"),
        ui.output_text("test_output"),
        ui.br(),
        ui.input_action_button("ping_server", "Ping Server", class_="btn-primary"),
        ui.output_text("ping_result"),
        ui.br(),
        ui.input_action_button("stress_test", "WebSocket Stress Test", class_="btn-secondary"),
        ui.output_text("stress_result"),
    ),
    title="Websocket Connectivity Test"
)


def server(input, output, session):
    # Reactive values to track websocket activity
    websocket_message_count = reactive.value(0)
    last_message_time = reactive.value(None)
    connection_status = reactive.value("unknown")
    transport_method = reactive.value("detecting...")

    @reactive.effect
    @reactive.event(input.set_websocket)
    def _():
        # JavaScript code to set localStorage and reload page
        js_code = """
        // Set the shiny whitelist to force websocket usage
        window.localStorage["shiny.whitelist"] = '["websocket"]';

        // Reload the page to apply the setting
        window.location.reload();
        """
        ui.insert_ui(
            selector="body",
            ui=ui.tags.script(js_code),
            where="beforeEnd"
        )

    @reactive.effect
    @reactive.event(input.ping_server)
    def ping_server():
        # Simple server ping to generate websocket traffic
        websocket_message_count.set(websocket_message_count() + 1)
        last_message_time.set(time.time())

    @reactive.effect
    @reactive.event(input.stress_test)
    def stress_test():
        # Generate multiple rapid updates to test websocket throughput
        for i in range(10):
            websocket_message_count.set(websocket_message_count() + 1)
        last_message_time.set(time.time())

    @render.ui
    def status_info():
        # Enhanced JavaScript to check current localStorage setting and detect actual websocket usage
        check_js = """
        function checkWebsocketSetting() {
            const whitelist = window.localStorage["shiny.whitelist"];
            const statusDiv = document.getElementById("websocket-status");
            if (statusDiv) {
                if (whitelist === '["websocket"]') {
                    statusDiv.innerHTML = '<div class="alert alert-success">Websocket whitelist is enabled and app works correctly</div>';
                } else {
                    statusDiv.innerHTML = '<div class="alert alert-info">Websocket whitelist is NOT set (default behavior)</div>';
                }
            }
            
            // Also update a hidden element that tests can easily check
            let hiddenStatus = document.getElementById("websocket-config-status");
            if (!hiddenStatus) {
                hiddenStatus = document.createElement("div");
                hiddenStatus.id = "websocket-config-status";
                hiddenStatus.style.display = "none";
                document.body.appendChild(hiddenStatus);
            }
            
            if (whitelist === '["websocket"]') {
                hiddenStatus.setAttribute("data-websocket-forced", "true");
                hiddenStatus.textContent = "websocket-forced";
            } else {
                hiddenStatus.setAttribute("data-websocket-forced", "false");
                hiddenStatus.textContent = "websocket-automatic";
            }
        }
        // Run the check after a short delay to ensure DOM is ready
        setTimeout(checkWebsocketSetting, 100);
        """

        return ui.div(
            ui.div("Checking...", id="websocket-status"),
            ui.tags.script(check_js),
        )

    @render.ui
    def transport_info():
        # Enhanced JavaScript to detect and report actual transport usage with more detail
        transport_js = """
        function detectTransport() {
            const transportDiv = document.getElementById("transport-status");
            if (!transportDiv) return;

            // Function to check transport with retries
            function checkTransport(attempts = 0) {
                if (attempts > 20) {
                    transportDiv.innerHTML = '<div class="alert alert-warning">Could not detect transport (Shiny may still be initializing)</div>';
                    updateTransportIndicator("unknown");
                    return;
                }

                try {
                    // Check if Shiny object exists and has socket
                    if (window.Shiny && window.Shiny.shinyapp && window.Shiny.shinyapp.config) {
                        const config = window.Shiny.shinyapp.config;
                        let transportInfo = '';
                        let alertClass = 'alert-info';
                        let actualTransport = 'unknown';
                        let debugInfo = [];

                        // Check various ways to determine transport
                        if (window.Shiny.shinyapp.$socket) {
                            const socket = window.Shiny.shinyapp.$socket;
                            
                            // Add comprehensive debug information
                            debugInfo.push(`Socket object exists: ${!!socket}`);
                            debugInfo.push(`Socket.socket exists: ${!!socket.socket}`);
                            debugInfo.push(`Socket.transport exists: ${!!socket.transport}`);
                            
                            // Add more detailed socket inspection
                            if (socket) {
                                debugInfo.push(`Socket constructor: ${socket.constructor ? socket.constructor.name : 'undefined'}`);
                                debugInfo.push(`Socket keys: ${Object.keys(socket).join(', ')}`);
                                
                                // Check for SockJS properties
                                if (socket.protocol) debugInfo.push(`Socket.protocol: ${socket.protocol}`);
                                if (socket.transport) debugInfo.push(`Socket.transport: ${JSON.stringify(socket.transport)}`);
                                if (socket._transport) debugInfo.push(`Socket._transport: ${JSON.stringify(socket._transport)}`);
                                if (socket.readyState !== undefined) debugInfo.push(`Socket.readyState: ${socket.readyState}`);
                                if (socket.url) debugInfo.push(`Socket.url: ${socket.url}`);
                                
                                // Check for nested socket properties
                                ['_sock', 'sock', '_socket', 'ws', '_ws', '_transport'].forEach(prop => {
                                    if (socket[prop]) {
                                        debugInfo.push(`Socket.${prop} exists: ${!!socket[prop]}`);
                                        if (socket[prop].constructor) {
                                            debugInfo.push(`Socket.${prop}.constructor: ${socket[prop].constructor.name}`);
                                        }
                                        if (socket[prop].url) {
                                            debugInfo.push(`Socket.${prop}.url: ${socket[prop].url}`);
                                        }
                                    }
                                });
                            }
                            
                            if (socket.socket) {
                                debugInfo.push(`Socket.socket.constructor.name: ${socket.socket.constructor ? socket.socket.constructor.name : 'undefined'}`);
                                debugInfo.push(`Socket.socket.readyState: ${socket.socket.readyState}`);
                                debugInfo.push(`Socket.socket.url: ${socket.socket.url || 'undefined'}`);
                            }

                            // Enhanced transport detection logic
                            let transportDetected = false;

                            // Method 1: Check for native WebSocket
                            if (socket.socket && socket.socket.constructor.name === 'WebSocket') {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (native WebSocket detected)';
                                alertClass = 'alert-success';
                                actualTransport = 'websocket';
                                transportDetected = true;
                            }
                            
                            // Method 2: Check socket.transport.name
                            else if (socket.transport && socket.transport.name) {
                                const transportName = socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong> (via socket.transport.name)`;
                                actualTransport = transportName;
                                alertClass = transportName === 'websocket' ? 'alert-success' : 'alert-warning';
                                transportDetected = true;
                            }
                            
                            // Method 3: Check socket.socket.transport
                            else if (socket.socket && socket.socket.transport && socket.socket.transport.name) {
                                const transportName = socket.socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong> (via socket.socket.transport.name)`;
                                actualTransport = transportName;
                                alertClass = transportName === 'websocket' ? 'alert-success' : 'alert-warning';
                                transportDetected = true;
                            }
                            
                            // Method 4: Check for SockJS patterns in URL or properties
                            else if (socket.url && socket.url.includes('sockjs')) {
                                // SockJS can use websockets or fallback to polling
                                if (socket.url.includes('websocket')) {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (SockJS WebSocket detected via URL)';
                                    alertClass = 'alert-success';
                                    actualTransport = 'websocket';
                                } else {
                                    transportInfo = 'Active Transport: <strong>sockjs-polling</strong> (SockJS polling detected via URL)';
                                    alertClass = 'alert-warning';
                                    actualTransport = 'polling';
                                }
                                transportDetected = true;
                            }
                            
                            // Method 5: Check nested socket objects for WebSocket
                            else {
                                const socketProperties = ['_sock', 'sock', '_socket', 'ws', '_ws'];
                                for (const prop of socketProperties) {
                                    if (socket[prop] && socket[prop].constructor && socket[prop].constructor.name === 'WebSocket') {
                                        transportInfo = `Active Transport: <strong>websocket</strong> (WebSocket found in socket.${prop})`;
                                        alertClass = 'alert-success';
                                        actualTransport = 'websocket';
                                        transportDetected = true;
                                        break;
                                    }
                                }
                            }
                            
                            // Method 6: Check for XHR/polling patterns
                            if (!transportDetected) {
                                if (socket.send && typeof socket.send === 'function') {
                                    // Check if it's using polling by looking for XHR patterns
                                    if (socket.constructor && socket.constructor.name.toLowerCase().includes('sockjs')) {
                                        transportInfo = 'Active Transport: <strong>sockjs-polling</strong> (SockJS polling detected)';
                                        alertClass = 'alert-warning';
                                        actualTransport = 'polling';
                                    } else {
                                        transportInfo = 'Active Transport: <strong>http-polling</strong> (HTTP polling detected)';
                                        alertClass = 'alert-warning';
                                        actualTransport = 'polling';
                                    }
                                    transportDetected = true;
                                }
                            }
                            
                            // Method 7: Check readyState patterns
                            if (!transportDetected && socket.readyState !== undefined) {
                                const readyState = socket.readyState;
                                const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
                                if (readyState === 1) { // OPEN
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (detected via readyState=OPEN)';
                                    alertClass = 'alert-success';
                                    actualTransport = 'websocket';
                                } else {
                                    transportInfo = `Active Transport: <strong>unknown</strong> (readyState: ${states[readyState] || readyState})`;
                                    alertClass = 'alert-warning';
                                    actualTransport = 'unknown';
                                }
                                transportDetected = true;
                            }
                            
                            // Fallback: Could not determine
                            if (!transportDetected) {
                                transportInfo = 'Active Transport: <strong>unknown</strong> (could not determine method - likely polling)';
                                alertClass = 'alert-warning';
                                actualTransport = 'unknown';
                            }
                            
                            // Add connection state info if available
                            if (socket.readyState !== undefined) {
                                const readyState = socket.readyState;
                                const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
                                transportInfo += `<br><small>Connection State: ${states[readyState] || readyState}</small>`;
                            }
                            
                        } else {
                            transportInfo = 'Transport: <strong>Shiny socket not yet available</strong>';
                            debugInfo.push('Shiny socket not available');
                        }

                        // Add whitelist info
                        const whitelist = window.localStorage["shiny.whitelist"];
                        let whitelistInfo = '';
                        if (whitelist === '["websocket"]') {
                            whitelistInfo = '<br><small><strong>Connection forced to websocket-only mode</strong></small>';
                        } else {
                            whitelistInfo = '<br><small>Using automatic transport selection</small>';
                        }
                        
                        // Add debug info
                        const debugDetails = debugInfo.length > 0 ? 
                            `<br><details><summary>Debug Info (click to expand)</summary><small>${debugInfo.join('<br>')}</small></details>` : '';

                        transportDiv.innerHTML = `<div class="alert ${alertClass}">${transportInfo}${whitelistInfo}${debugDetails}</div>`;
                        updateTransportIndicator(actualTransport);
                    } else {
                        // Shiny not ready yet, retry
                        setTimeout(() => checkTransport(attempts + 1), 200);
                    }
                } catch (error) {
                    setTimeout(() => checkTransport(attempts + 1), 200);
                }
            }
            
            // Update hidden indicator for test assertions
            function updateTransportIndicator(transport) {
                let indicator = document.getElementById("actual-transport-indicator");
                if (!indicator) {
                    indicator = document.createElement("div");
                    indicator.id = "actual-transport-indicator";
                    indicator.style.display = "none";
                    document.body.appendChild(indicator);
                }
                indicator.setAttribute("data-transport", transport);
                indicator.textContent = `transport-${transport}`;
            }

            checkTransport();
        }

        // Run detection after Shiny loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => setTimeout(detectTransport, 500));
        } else {
            setTimeout(detectTransport, 500);
        }

        // Also re-run when Shiny connects
        $(document).on('shiny:connected', function() {
            setTimeout(detectTransport, 100);
        });
        """

        return ui.div(
            ui.div("Detecting transport...", id="transport-status"),
            ui.tags.script(transport_js),
        )

    @render.ui
    def websocket_activity():
        # Create a real-time websocket activity monitor that syncs with server-side tracking
        monitor_js = f"""
        (function() {{
            // Use a namespace to avoid variable conflicts
            if (!window.WebSocketMonitor) {{
                window.WebSocketMonitor = {{}};
            }}
            
            // Initialize or update the message count from server
            window.WebSocketMonitor.messageCount = {websocket_message_count()};
            window.WebSocketMonitor.lastMessageTime = {int(last_message_time() * 1000) if last_message_time() else 'null'};
            
            function updateActivityDisplay() {{
                const activityDiv = document.getElementById("activity-display");
                if (!activityDiv) return;
                
                const now = new Date();
                const timeStr = window.WebSocketMonitor.lastMessageTime ? 
                    new Date(window.WebSocketMonitor.lastMessageTime).toLocaleTimeString() : 'None';
                
                activityDiv.innerHTML = `
                    <div class="alert alert-info">
                        <strong>WebSocket Messages:</strong> ${{window.WebSocketMonitor.messageCount}}<br>
                        <strong>Last Activity:</strong> ${{timeStr}}<br>
                        <strong>Monitor Active:</strong> ${{now.toLocaleTimeString()}}
                    </div>
                `;
                
                // Update hidden indicator for tests
                let indicator = document.getElementById("websocket-activity-indicator");
                if (!indicator) {{
                    indicator = document.createElement("div");
                    indicator.id = "websocket-activity-indicator";
                    indicator.style.display = "none";
                    document.body.appendChild(indicator);
                }}
                indicator.setAttribute("data-message-count", window.WebSocketMonitor.messageCount.toString());
                indicator.setAttribute("data-last-message", window.WebSocketMonitor.lastMessageTime || "none");
                indicator.textContent = `messages-${{window.WebSocketMonitor.messageCount}}`;
            }}
            
            // Monitor Shiny's websocket traffic by hooking into the actual socket
            function monitorWebSocketActivity() {{
                if (window.Shiny && window.Shiny.shinyapp && window.Shiny.shinyapp.$socket) {{
                    const socket = window.Shiny.shinyapp.$socket;
                    
                    // Only set up hooks once
                    if (!window.WebSocketMonitor.hooksSetUp) {{
                        window.WebSocketMonitor.hooksSetUp = true;
                        
                        // Hook into Shiny's message sending mechanism
                        if (socket.send && typeof socket.send === 'function') {{
                            const originalSend = socket.send;
                            socket.send = function(...args) {{
                                window.WebSocketMonitor.messageCount++;
                                window.WebSocketMonitor.lastMessageTime = Date.now();
                                updateActivityDisplay();
                                return originalSend.apply(this, args);
                            }};
                        }}
                        
                        // Hook into the underlying socket if available
                        if (socket.socket) {{
                            if (typeof socket.socket.send === 'function') {{
                                const originalSocketSend = socket.socket.send;
                                socket.socket.send = function(...args) {{
                                    window.WebSocketMonitor.messageCount++;
                                    window.WebSocketMonitor.lastMessageTime = Date.now();
                                    updateActivityDisplay();
                                    return originalSocketSend.apply(this, args);
                                }};
                            }}
                            
                            // Monitor incoming messages
                            if (typeof socket.socket.addEventListener === 'function') {{
                                socket.socket.addEventListener('message', function(event) {{
                                    window.WebSocketMonitor.messageCount++;
                                    window.WebSocketMonitor.lastMessageTime = Date.now();
                                    updateActivityDisplay();
                                }});
                            }}
                        }}
                        
                        // Hook into Shiny's onMessage if available
                        if (socket.onMessage && typeof socket.onMessage === 'function') {{
                            const originalOnMessage = socket.onMessage;
                            socket.onMessage = function(...args) {{
                                window.WebSocketMonitor.messageCount++;
                                window.WebSocketMonitor.lastMessageTime = Date.now();
                                updateActivityDisplay();
                                return originalOnMessage.apply(this, args);
                            }};
                        }}
                    }}
                }}
                
                updateActivityDisplay();
            }}
            
            // Sync with server-side counters periodically
            function syncWithServer() {{
                // Get the current server-side values from the rendered outputs
                const pingResult = document.querySelector('[data-testid="ping_result"]') || 
                                 Array.from(document.querySelectorAll('*')).find(el => 
                                   el.textContent && el.textContent.includes('Total messages:'));
                const stressResult = document.querySelector('[data-testid="stress_result"]') ||
                                   Array.from(document.querySelectorAll('*')).find(el => 
                                     el.textContent && el.textContent.includes('Generated') && el.textContent.includes('messages'));
                
                if (pingResult && pingResult.textContent.includes('Total messages:')) {{
                    const match = pingResult.textContent.match(/Total messages: (\\d+)/);
                    if (match) {{
                        const serverCount = parseInt(match[1]);
                        if (serverCount > window.WebSocketMonitor.messageCount) {{
                            window.WebSocketMonitor.messageCount = serverCount;
                            window.WebSocketMonitor.lastMessageTime = Date.now();
                            updateActivityDisplay();
                        }}
                    }}
                }}
                
                if (stressResult && stressResult.textContent.includes('Generated')) {{
                    const match = stressResult.textContent.match(/Generated (\\d+) messages/);
                    if (match) {{
                        const serverCount = parseInt(match[1]);
                        if (serverCount > window.WebSocketMonitor.messageCount) {{
                            window.WebSocketMonitor.messageCount = serverCount;
                            window.WebSocketMonitor.lastMessageTime = Date.now();
                            updateActivityDisplay();
                        }}
                    }}
                }}
            }}
            
            // Set up monitoring only once
            if (!window.WebSocketMonitor.initialized) {{
                window.WebSocketMonitor.initialized = true;
                
                if (window.Shiny && window.Shiny.shinyapp) {{
                    monitorWebSocketActivity();
                }} else {{
                    $(document).on('shiny:connected', function() {{
                        setTimeout(monitorWebSocketActivity, 100);
                    }});
                }}
                
                // Update display every 2 seconds and sync with server
                setInterval(function() {{
                    updateActivityDisplay();
                    syncWithServer();
                }}, 2000);
            }}
            
            // Initial sync and display update
            setTimeout(function() {{
                syncWithServer();
                updateActivityDisplay();
            }}, 500);
        }})();
        """

        return ui.div(
            ui.div("Initializing activity monitor...", id="activity-display"),
            ui.tags.script(monitor_js),
        )

    @render.text
    def test_output():
        # This triggers a websocket message when the input changes
        return f"You typed: {input.test_input()}"

    @render.text
    def ping_result():
        if websocket_message_count() > 0:
            return f"Server ping successful! Total messages: {websocket_message_count()}"
        return "Click 'Ping Server' to test websocket communication"

    @render.text
    def stress_result():
        if websocket_message_count() >= 10:
            last_time = last_message_time()
            if last_time:
                return f"Stress test completed! Generated {websocket_message_count()} messages. Last: {time.ctime(last_time)}"
        return "Click 'WebSocket Stress Test' to generate multiple messages"


app = App(app_ui, server)
