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
                    statusDiv.innerHTML = '<div class="alert alert-success">✓ Websocket whitelist is SET</div>';
                } else {
                    statusDiv.innerHTML = '<div class="alert alert-info">ℹ Websocket whitelist is NOT set (default behavior)</div>';
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
    
    @render.text
    def test_output():
        return f"You typed: {input.test_input()}"

app = App(app_ui, server)
