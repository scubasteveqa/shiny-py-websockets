from shiny import App, render, ui, reactive

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
        ui.card_header("Test Content"),
        ui.p("This is a test Shiny app to verify websocket functionality."),
        ui.input_text("test_input", "Type something:", value="Hello, Shiny!"),
        ui.output_text("test_output"),
    ),
    title="Websocket Connectivity Test"
)


def server(input, output, session):
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

    @render.ui
    def status_info():
        # JavaScript to check current localStorage setting
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
        # JavaScript to detect the current transport mechanism
        transport_js = """
        function detectTransport() {
            const transportDiv = document.getElementById("transport-status");
            if (!transportDiv) return;

            // Function to check transport with retries
            function checkTransport(attempts = 0) {
                if (attempts > 20) {
                    transportDiv.innerHTML = '<div class="alert alert-warning">Could not detect transport (Shiny may still be initializing)</div>';
                    // Still provide debug info even when detection fails
                    window.SocketDebugInfo = {
                        error: 'Detection failed after 20 attempts',
                        localStorage: window.localStorage["shiny.whitelist"],
                        timestamp: new Date().toISOString()
                    };
                    return;
                }

                try {
                    // Always provide basic debug info
                    window.SocketDebugInfo = {
                        detectionAttempt: attempts,
                        shinyExists: !!window.Shiny,
                        shinyAppExists: !!(window.Shiny && window.Shiny.shinyapp),
                        shinySocketExists: !!(window.Shiny && window.Shiny.shinyapp && window.Shiny.shinyapp.$socket),
                        localStorage: window.localStorage["shiny.whitelist"],
                        timestamp: new Date().toISOString()
                    };

                    // Check if Shiny object exists and has socket
                    if (window.Shiny && window.Shiny.shinyapp && window.Shiny.shinyapp.config) {
                        const config = window.Shiny.shinyapp.config;
                        let transportInfo = '';
                        let alertClass = 'alert-info';

                        // Check various ways to determine transport
                        if (window.Shiny.shinyapp.$socket) {
                            const socket = window.Shiny.shinyapp.$socket;
                            
                            // Enhanced debugging information
                            window.SocketDebugInfo = {
                                ...window.SocketDebugInfo,
                                socket: socket,
                                socketExists: !!socket,
                                socketSocketExists: !!socket.socket,
                                socketConstructor: socket.constructor ? socket.constructor.name : null,
                                socketSocketConstructor: socket.socket && socket.socket.constructor ? socket.socket.constructor.name : null,
                                socketUrl: socket.url || null,
                                socketSocketUrl: socket.socket && socket.socket.url ? socket.socket.url : null,
                                socketReadyState: socket.socket ? socket.socket.readyState : null,
                                socketTransport: socket.transport || null,
                                socketSocketTransport: socket.socket && socket.socket.transport ? socket.socket.transport : null,
                                socketKeys: Object.keys(socket),
                                socketSocketKeys: socket.socket ? Object.keys(socket.socket) : null,
                                isWebsocketForced: window.localStorage["shiny.whitelist"] === '["websocket"]'
                            };
                            
                            // Check if websocket is forced via localStorage
                            const whitelist = window.localStorage["shiny.whitelist"];
                            const isWebsocketForced = whitelist === '["websocket"]';

                            // Method 1: Check for native WebSocket constructor
                            if (socket.socket && socket.socket.constructor && socket.socket.constructor.name === 'WebSocket') {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (native WebSocket detected)';
                                alertClass = 'alert-success';
                                window.SocketDebugInfo.detectionMethod = 'Native WebSocket constructor';
                            }
                            // Method 2: Check socket.transport.name
                            else if (socket.transport && socket.transport.name) {
                                const transportName = socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong>`;
                                alertClass = transportName === 'websocket' ? 'alert-success' : 'alert-warning';
                                window.SocketDebugInfo.detectionMethod = `socket.transport.name = ${transportName}`;
                            }
                            // Method 3: Check socket.socket.transport
                            else if (socket.socket && socket.socket.transport && socket.socket.transport.name) {
                                const transportName = socket.socket.transport.name;
                                transportInfo = `Active Transport: <strong>${transportName}</strong>`;
                                alertClass = transportName === 'websocket' ? 'alert-success' : 'alert-warning';
                                window.SocketDebugInfo.detectionMethod = `socket.socket.transport.name = ${transportName}`;
                            }
                            // Method 4: Check for WebSocket URL patterns
                            else if (socket.url && (socket.url.includes('ws://') || socket.url.includes('wss://') || socket.url.includes('/websocket'))) {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (WebSocket URL detected)';
                                alertClass = 'alert-success';
                                window.SocketDebugInfo.detectionMethod = `WebSocket URL pattern: ${socket.url}`;
                            }
                            // Method 5: Check for SockJS WebSocket mode
                            else if (socket.url && socket.url.includes('sockjs') && socket.url.includes('websocket')) {
                                transportInfo = 'Active Transport: <strong>websocket</strong> (SockJS WebSocket mode)';
                                alertClass = 'alert-success';
                                window.SocketDebugInfo.detectionMethod = `SockJS WebSocket: ${socket.url}`;
                            }
                            // Method 6: Special case for forced websocket mode
                            else if (isWebsocketForced && socket.socket && socket.socket.readyState !== undefined) {
                                // If websocket is forced but we don't detect clear websocket indicators,
                                // check if it's still working (readyState 1 = OPEN)
                                if (socket.socket.readyState === 1) {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (forced mode - connection active)';
                                    alertClass = 'alert-success';
                                    window.SocketDebugInfo.detectionMethod = `Forced websocket with readyState=${socket.socket.readyState}`;
                                } else {
                                    transportInfo = 'Active Transport: <strong>ERROR</strong> (websocket forced but connection failed)';
                                    alertClass = 'alert-danger';
                                    window.SocketDebugInfo.detectionMethod = `Forced websocket failed, readyState=${socket.socket.readyState}`;
                                }
                            }
                            // Method 7: Check readyState for WebSocket API (only if not forced)
                            else if (!isWebsocketForced && socket.socket && socket.socket.readyState !== undefined) {
                                // Check if it has WebSocket-like properties
                                if (socket.socket.url && (socket.socket.url.includes('ws://') || socket.socket.url.includes('wss://'))) {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (WebSocket API with WS URL)';
                                    alertClass = 'alert-success';
                                    window.SocketDebugInfo.detectionMethod = `WebSocket API with WS URL: ${socket.socket.url}`;
                                } else {
                                    transportInfo = 'Active Transport: <strong>websocket</strong> (WebSocket API detected)';
                                    alertClass = 'alert-success';
                                    window.SocketDebugInfo.detectionMethod = 'WebSocket API via readyState';
                                }
                            }
                            // Method 8: Check for specific polling indicators (only if not forced)
                            else if (!isWebsocketForced && socket.constructor && socket.constructor.name === 'PromisedConnection') {
                                transportInfo = 'Active Transport: <strong>http-polling</strong> (Shiny HTTP connection)';
                                alertClass = 'alert-warning';
                                window.SocketDebugInfo.detectionMethod = 'PromisedConnection detected';
                            }
                            // Method 9: Check for XHR/polling patterns (only if not forced)
                            else if (!isWebsocketForced && socket.url && (socket.url.includes('xhr') || socket.url.includes('polling'))) {
                                transportInfo = 'Active Transport: <strong>xhr-polling</strong> (XHR polling detected)';
                                alertClass = 'alert-warning';
                                window.SocketDebugInfo.detectionMethod = `XHR polling URL: ${socket.url}`;
                            }
                            // Method 10: Handle forced websocket failure case
                            else if (isWebsocketForced) {
                                transportInfo = 'Active Transport: <strong>websocket-fallback</strong> (websocket forced but may have fallen back)';
                                alertClass = 'alert-warning';
                                window.SocketDebugInfo.detectionMethod = 'Websocket forced but unclear if working';
                            }
                            // Fallback: Unable to determine
                            else {
                                transportInfo = 'Active Transport: <strong>unknown</strong> (could not determine method)';
                                alertClass = 'alert-info';
                                window.SocketDebugInfo.detectionMethod = 'All detection methods failed';
                            }
                        } else {
                            transportInfo = 'Transport: <strong>Shiny socket not yet available</strong>';
                            window.SocketDebugInfo.detectionMethod = 'Shiny socket not available';
                        }

                        // Add whitelist info
                        const whitelist = window.localStorage["shiny.whitelist"];
                        let whitelistInfo = '';
                        if (whitelist === '["websocket"]') {
                            whitelistInfo = '<br><small>Connection forced to websocket-only mode</small>';
                        } else {
                            whitelistInfo = '<br><small>Using automatic transport selection</small>';
                        }

                        transportDiv.innerHTML = `<div class="alert ${alertClass}">${transportInfo}${whitelistInfo}</div>`;
                    } else {
                        // Shiny not ready yet, retry
                        setTimeout(() => checkTransport(attempts + 1), 200);
                    }
                } catch (error) {
                    setTimeout(() => checkTransport(attempts + 1), 200);
                }
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

    @render.text
    def test_output():
        return f"You typed: {input.test_input()}"


app = App(app_ui, server)
