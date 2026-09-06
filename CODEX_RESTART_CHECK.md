# `codex_apps` timeout: conclusive diagnosis

The following failure is reproducible:

```
MCP client for `codex_apps` failed to start: MCP startup failed: timed out awaiting tools/list after 30s
```

## Findings already verified

- ChatGPT was launched and `codex doctor` reported that its desktop app-server initialized successfully.
- macOS DNS and direct HTTPS/TLS checks to `chatgpt.com`, `persistent.oaistatic.com`, and GitHub succeeded.
- The standard terminal CLI (`codex-cli 0.153.4`) reproduced the timeout in a new interactive session.
- The Codex binary bundled with ChatGPT (`codex-cli 0.153.1`) reproduced the same timeout in a new interactive session.
- OpenAI Status reported all systems operational when checked.
- The project has no `codex_apps` configuration entry.

## Conclusion

This is a persistent failure in the hosted Apps MCP service or its account-specific Apps inventory. Restarting Codex, starting ChatGPT, changing CLI versions, changing this project's configuration, or diagnosing DNS again has already been ruled out.

## Next action: OpenAI support report

Submit the exact error and include:

```text
Terminal Codex version: 0.153.4
ChatGPT-bundled Codex version: 0.153.1
ChatGPT desktop app version: 26.901.31953
macOS: 26.6.2 (Apple Silicon)
```

State that the timeout occurs with ChatGPT desktop running and is reproduced by both the terminal and bundled Codex runtimes. Attach the output of:

```sh
codex doctor --json
```

Include the timestamp of a fresh reproduction and request investigation of the account's hosted `codex_apps` MCP `tools/list` response.
