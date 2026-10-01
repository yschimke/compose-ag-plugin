---
name: compose-catalogs-setup
description: Run right after the compose-catalogs plugin is installed, or when the hosted catalog server cannot be reached or asks for access. Checks the hosted preview.coo.ee catalog server, completes the access grant, and shows one catalog so the person sees it working.
---

# Set up Compose Catalogs

This is the plugin's onboarding skill. It needs no local toolchain. Keep it to a few tool calls
and report each step in one line.

1. **Reach the server.** Call `list_projects` on the `compose-preview-catalog` server once; it lists
   the catalogs.
   If the server is unreachable, say so with the error text and stop; do not retry in a loop.
2. **Access.** If the server asks for access:
   - Where the host supports URL elicitation, follow the access link it opens.
   - Otherwise use the text fallback: call `request_access`, show the person the link it returns,
     then call `poll_access` once they say they have approved it.
   - A `COMPOSE_PREVIEW_TOKEN` set in the plugin settings or the environment skips this step.
3. **First catalog.** Name the catalogs in one line (for example Material 3 and Wear). Pick one
   small component with `catalog_list_previews`, render it with `catalog_render_preview`, and
   describe it in a line.
4. **Close** with one line: ask for any component by name ("show the Wear `Button` variants"),
   or open the catalog from the sidebar where the host shows it.
