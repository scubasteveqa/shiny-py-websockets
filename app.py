
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

                            // Method 1: Check for native WebSocket constructor
                            if (socket.socket && socket.socket.constructor && socket.socket.constructor.name === 'WebSocket') {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (native WebSocket detected)';
                                alertClass = 'alert-success';
                                actualTransport = 'websocket';
                                transportDetected = true;
                                debugInfo.push('Detection method: Native WebSocket constructor');
                            }
                            
                            // Method 2: Check for WebSocket URL patterns
                            else if (socket.url && (socket.url.includes('ws://') || socket.url.includes('wss://') || socket.url.includes('/websocket'))) {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (WebSocket URL detected)';
                                alertClass = 'alert-success';
                                actualTransport = 'websocket';
                                transportDetected = true;
                                debugInfo.push(`Detection method: WebSocket URL pattern (${socket.url})`);
                            }
                            
                            // Method 3: Check socket.transport.name
                            else if (socket.transport && socket.transport.name) {
                                const transportName = socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong> (via socket.transport.name)`;
                                actualTransport = transportName;
                                alertClass = transportName === 'websocket' ? 'alert-success' : 'alert-warning';
                                transportDetected = true;
                                debugInfo.push(`Detection method: socket.transport.name = ${transportName}`);
                            }
                            
                            // Method 4: Check nested WebSocket objects
                            else {
                                const socketProperties = ['_sock', 'sock', '_socket', 'ws', '_ws', '_conn'];
                                for (const prop of socketProperties) {
                                    if (socket[prop]) {
                                        debugInfo.push(`Checking socket.${prop}: ${socket[prop].constructor ? socket[prop].constructor.name : 'no constructor'}`);
                                        if (socket[prop].constructor && socket[prop].constructor.name === 'WebSocket') {
                                            transportInfo = `Active Transport: <strong>websocket</strong> (WebSocket found in socket.${prop})`;
                                            alertClass = 'alert-success';
                                            actualTransport = 'websocket';
                                            transportDetected = true;
                                            debugInfo.push(`Detection method: WebSocket in socket.${prop}`);
                                            break;
                                        }
                                        // Check for websocket-like properties
                                        if (socket[prop].url && (socket[prop].url.includes('ws://') || socket[prop].url.includes('wss://'))) {
                                            transportInfo = `Active Transport: <strong>websocket</strong> (WebSocket URL in socket.${prop})`;
                                            alertClass = 'alert-success';
                                            actualTransport = 'websocket';
                                            transportDetected = true;
                                            debugInfo.push(`Detection method: WebSocket URL in socket.${prop}.url`);
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            // Method 5: Check for SockJS WebSocket mode
                            if (!transportDetected && socket.url && socket.url.includes('sockjs')) {
                                if (socket.url.includes('websocket') || socket.url.includes('/ws')) {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (SockJS WebSocket mode)';
                                    alertClass = 'alert-success';
                                    actualTransport = 'websocket';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: SockJS WebSocket mode');
                                } else if (socket.url.includes('xhr') || socket.url.includes('polling')) {
                                    transportInfo = 'Active Transport: <strong>xhr-polling</strong> (SockJS XHR polling mode)';
                                    alertClass = 'alert-warning';
                                    actualTransport = 'polling';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: SockJS XHR polling mode');
                                } else {
                                    transportInfo = 'Active Transport: <strong>sockjs-unknown</strong> (SockJS mode undetermined)';
                                    alertClass = 'alert-info';
                                    actualTransport = 'unknown';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: SockJS undetermined mode');
                                }
                            }
                            
                            // Method 6: Analyze constructor and properties for better classification
                            if (!transportDetected) {
                                if (socket.constructor && socket.constructor.name === 'PromisedConnection') {
                                    // This is Shiny's HTTP-based connection
                                    transportInfo = 'Active Transport: <strong>http-polling</strong> (Shiny PromisedConnection)';
                                    alertClass = 'alert-warning';
                                    actualTransport = 'polling';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: Shiny PromisedConnection (HTTP polling)');
                                } else if (socket.send && typeof socket.send === 'function') {
                                    // Has send method but not clearly WebSocket
                                    transportInfo = 'Active Transport: <strong>unknown-polling</strong> (has send method, likely polling)';
                                    alertClass = 'alert-warning';
                                    actualTransport = 'polling';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: Send method present, assuming polling');
                                }
                            }
                            
                            // Method 7: Final attempt using readyState and other indicators
                            if (!transportDetected) {
                                const readyState = socket.readyState;
                                if (readyState === 1 && socket.constructor && socket.constructor.name !== 'PromisedConnection') {
                                    // Connected state, not PromisedConnection, might be WebSocket
                                    transportInfo = 'Active Transport: <strong>possibly-websocket</strong> (readyState=OPEN, unknown constructor)';
                                    alertClass = 'alert-info';
                                    actualTransport = 'unknown';
                                    transportDetected = true;
                                    debugInfo.push('Detection method: ReadyState analysis (inconclusive)');
                                } else {
                                    const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
                                    transportInfo = `Active Transport: <strong>unknown</strong> (readyState: ${states[readyState] || readyState})`;
                                    alertClass = 'alert-warning';
                                    actualTransport = 'unknown';
                                    transportDetected = true;
                                    debugInfo.push(`Detection method: ReadyState = ${readyState} (${states[readyState] || 'unknown'})`);
                                }
                            }
                            
                            // Fallback: Truly could not determine
                            if (!transportDetected) {
                                transportInfo = 'Active Transport: <strong>unknown</strong> (detection failed - insufficient information)';
                                alertClass = 'alert-warning';
                                actualTransport = 'unknown';
                                debugInfo.push('Detection method: All methods failed');
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
        
