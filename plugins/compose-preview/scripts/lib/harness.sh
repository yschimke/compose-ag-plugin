#!/bin/sh
# Shared harness selection for compose-preview hooks.
#
# Generated hook commands must pass --harness=<name>. Environment detection is
# only a compatibility fallback. Codex Stop-hook semantics are unverified
# (issue #6 Q4), so this library deliberately emits no Codex response.

# Sets HARNESS to one of: antigravity, claude, codex, opencode, gemini, unknown.
# An explicit --harness=<name> takes precedence over environment detection.
# Returns 2 for an invalid argument or an unsupported explicit harness.
harness_detect() {
  HARNESS=
  harness_override=
  harness_override_seen=0

  for harness_argument in "$@"; do
    case "$harness_argument" in
      --harness=*)
        if [ "$harness_override_seen" -eq 1 ]; then
          printf '%s\n' 'harness: --harness may be passed only once' >&2
          return 2
        fi
        harness_override=${harness_argument#--harness=}
        harness_override_seen=1
        ;;
      *)
        printf 'harness: unknown argument: %s\n' "$harness_argument" >&2
        return 2
        ;;
    esac
  done

  if [ "$harness_override_seen" -eq 1 ]; then
    case "$harness_override" in
      antigravity|claude|codex|opencode|gemini|unknown)
        HARNESS=$harness_override
        return 0
        ;;
      *)
        printf 'harness: unsupported harness: %s\n' "$harness_override" >&2
        return 2
        ;;
    esac
  fi

  # Keep these ordered: an explicitly requested Claude plugin environment is
  # more specific than any inherited terminal variables from another harness.
  if [ "${CLAUDECODE-}" = "1" ] || [ -n "${CLAUDE_PLUGIN_ROOT-}" ]; then
    HARNESS=claude
  elif [ -n "${CODEX_THREAD_ID-}" ]; then
    HARNESS=codex
  elif [ "${__CFBundleIdentifier-}" = "com.google.antigravity" ] || [ -n "${ANTIGRAVITY_CLI_ALIAS-}" ]; then
    HARNESS=antigravity
  elif [ "${OPENCODE-}" = "1" ]; then
    HARNESS=opencode
  elif [ "${GEMINI_CLI-}" = "1" ]; then
    HARNESS=gemini
  else
    HARNESS=unknown
  fi
}

# Emits the harness's verified "keep going" response to stdout.
#
# Claude and Antigravity have different, known JSON contracts. Codex is
# intentionally fail-closed until #6 Q4 establishes whether a Stop event and
# response contract exist. OpenCode and Gemini are detected but not Stop-hook
# targets. Unknown callers are likewise not allowed to proceed silently.
# Returns 2 for invalid input or a non-target harness; returns 3 for Codex.
harness_emit_continue() {
  harness_reason=${1-}
  if [ "$#" -ne 1 ] || [ -z "$harness_reason" ]; then
    printf '%s\n' 'harness: harness_emit_continue requires one non-empty reason' >&2
    return 2
  fi

  # Reasons are protocol data. Reject control characters instead of risking
  # malformed JSON; printable UTF-8 text is accepted by a normal locale.
  case "$harness_reason" in
    *[![:print:]]*)
      printf '%s\n' 'harness: reason must contain printable characters only' >&2
      return 2
      ;;
  esac

  harness_json_reason=$(printf '%s' "$harness_reason" | sed 's/\\\\/\\\\\\\\/g; s/"/\\\\"/g')
  case "${HARNESS-}" in
    antigravity)
      printf '{"decision":"continue","reason":"%s"}\n' "$harness_json_reason"
      ;;
    claude)
      printf '{"decision":"block","reason":"%s"}\n' "$harness_json_reason"
      ;;
    codex)
      printf '%s\n' 'harness: Codex Stop-hook output is unsupported pending issue #6 Q4' >&2
      return 3
      ;;
    opencode|gemini)
      printf 'harness: %s is not a Stop-hook target\n' "$HARNESS" >&2
      return 2
      ;;
    *)
      printf '%s\n' 'harness: unknown harness has no Stop-hook output contract' >&2
      return 2
      ;;
  esac
}
