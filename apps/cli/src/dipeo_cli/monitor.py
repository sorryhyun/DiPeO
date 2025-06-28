import webbrowser


def monitor_command(args: list[str]) -> None:
    """Open browser monitoring page"""
    # If a diagram ID is provided, include it in the URL
    if args:
        diagram_id = args[0]
        monitor_url = f"http://localhost:3000/?monitor=true&diagram={diagram_id}"
    else:
        monitor_url = "http://localhost:3000/?monitor=true"
    print(f"🌐 Opening browser monitor at {monitor_url}")
    webbrowser.open(monitor_url)
