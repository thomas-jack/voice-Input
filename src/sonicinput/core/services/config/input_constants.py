"""Input method constants."""


class InputMethods:
    """Supported input methods."""

    CLIPBOARD = "clipboard"
    SENDINPUT = "sendinput"
    SMART = "smart"

    AVAILABLE_METHODS = [CLIPBOARD, SENDINPUT, SMART]

    METHOD_DESCRIPTIONS = {
        CLIPBOARD: "Clipboard-based input (most compatible)",
        SENDINPUT: "Direct input simulation (faster)",
        SMART: "Smart method selection (recommended)",
    }
