# Run With macOS Automator

Use this guide to start FastAPI and FastMCP together from a double-clickable macOS app.

## Create the Automator App

1. Open **Automator**.
2. Choose **New Document**.
3. Select **Application**.
4. Search for **Run Shell Script**.
5. Drag **Run Shell Script** into the workflow.
6. Set **Shell** to `/bin/zsh`.
7. Paste this command:

```bash
osascript -e 'tell application "Terminal" to do script "cd /Users/danish/Documents/Projects/linkedin-mcp-orchestrator && ./scripts/run-dev.sh"'
```

8. Click **Run** to test it.
9. Save the app as:

```text
Run LinkedIn MCP Dev.app
```

## Use the App

Double-click the saved app from Finder, Spotlight, Launchpad, or the Dock.

The app opens Terminal and runs:

```bash
cd /Users/danish/Documents/Projects/linkedin-mcp-orchestrator
./scripts/run-dev.sh
```

FastAPI starts at:

```text
http://127.0.0.1:8000
```

FastMCP starts at:

```text
http://127.0.0.1:8765/mcp
```

To stop both services, open the Terminal window created by the app and press `Ctrl+C`.
