The Root Cause
ChatGPT uses an event-driven mechanism to pass data to widgets, not pre-populated data. Many developers (including myself) initially assumed window.openai.toolOutput would be populated on load, but it’s actually updated asynchronously via custom events.

The Solution
Use React’s useSyncExternalStore to subscribe to the openai:set_globals event:

import { useSyncExternalStore } from "react";

const SET_GLOBALS_EVENT_TYPE = "openai:set_globals";

function useOpenAiGlobal<K extends keyof OpenAiGlobals>(key: K) {
  return useSyncExternalStore(
    // Subscribe to ChatGPT's data update event
    (onChange) => {
      const handleSetGlobal = (event: any) => {
        if (event.detail?.globals?.[key] !== undefined) {
          onChange(); // Trigger React re-render
        }
      };

      window.addEventListener(SET_GLOBALS_EVENT_TYPE, handleSetGlobal, {
        passive: true,
      });

      return () => {
        window.removeEventListener(SET_GLOBALS_EVENT_TYPE, handleSetGlobal);
      };
    },
    // Get current value from window.openai
    () => (window as any).openai?.[key] ?? null,
  );
}

// Usage in component
function MyWidget() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const displayMode = useOpenAiGlobal("displayMode");

  // toolOutput will automatically update when ChatGPT pushes new data!
  return <div>{toolOutput ? <DataDisplay data={toolOutput} /> : "Waiting..."}</div>;
}

Key Points:
Don’t rely on initial window.openai.toolOutput - it’s null on load

Subscribe to openai:set_globals event - this is how ChatGPT pushes data to your widget

Use useSyncExternalStore - React 18’s built-in hook for external data sources

The data flow is: Tool execution → ChatGPT receives structuredContent → Triggers event → Widget receives data via window.openai

Additional CSP Fix:
If you’re loading external images (e.g., YouTube thumbnails), you need to declare them in your widget metadata:

def _widget_meta():
    return {
        "openai/widgetPrefersBorder": True,
        "openai/widgetDomain": "https://chatgpt.com",
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "openai/widgetCSP": {
            "connect_domains": [],
            # Important: Must be full URLs (https://domain), not just domain names
            "resource_domains": [
                "https://i.ytimg.com",      # YouTube thumbnails
                "https://img.youtube.com",  # YouTube images
            ],
        },
    }

Common mistake: Using "i.ytimg.com" instead of "https://i.ytimg.com" will cause validation errors.

References:
This approach is based on the official OpenAI Apps SDK examples, specifically: - /src/use-openai-global.ts - Shows the event subscription pattern - /pizzaz_server_python/main.py - Shows proper MCP integration
