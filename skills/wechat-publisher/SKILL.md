---
name: wechat-publisher
description: Publishes markdown articles to WeChat Official Account. Use when the user wants to push content, drafts, or articles to WeChat.
---

# WeChat Publisher

This skill allows you to automatically publish Markdown articles to a WeChat Official Account. It handles draft creation, image uploading, and automatic publication (making the article public).

## Usage

The primary script is `scripts/publish.mjs`. It wraps the `@lanyijianke/wechat-official-account-mcp` library and adds auto-publish functionality.

### Command

Run the script using `node` from the skill's `scripts` directory, or referenced absolutely.

```bash
node <path-to-skill>/scripts/publish.mjs push-markdown --input <path-to-markdown-file> --title "<Article Title>"
```

### Parameters

- `--input`: The path to the Markdown file. **Important:** Provide the absolute path or a path relative to where you run the command.
- `--title`: The title of the article to appear in WeChat.

### Behavior

1. **Draft Creation**: The script converts the Markdown to HTML, uploads local images to WeChat, and saves it as a draft.
2. **Auto-Publish**: If draft creation is successful, it automatically triggers the `freepublish/submit` API to make the article public immediately.
3. **Configuration**: Uses `assets/wechat_config.json` for credentials (AppID/AppSecret).

### Example

```bash
node C:\Users\EDY\wechat-publisher\scripts\publish.mjs push-markdown --input "D:\MAX_Workspace\My_Article.md" --title "My Weekly Report"
```

## Requirements

- **Node.js**: Must be installed.
- **Dependencies**: Relies on `D:\MAX_Workspace\node_modules` existing.
- **Config**: `assets/wechat_config.json` must contain valid `appId` and `appSecret`.
- **IP Whitelist**: The machine's IP must be whitelisted in the WeChat Official Account settings.
