# Miniclaw - Local AI Agent

A local AI agent that runs on your machine, connecting your browser to native OS capabilities.

## Structure

```
miniclaw/
├── miniclaw-web/        # Browser UI (open index.html)
│   ├── index.html
│   ├── style.css
│   └── client.js
├── miniclaw-executor/   # Node.js backend (run on your PC)
│   ├── server.js
│   ├── package.json
│   ├── start.bat        # Windows
│   ├── start.ps1        # PowerShell
│   └── start.sh         # Mac / Linux
├── RULES_MINI.md
└── ARCHITECT_MINICLAW.md
```

## Quick Start

1. Go to `miniclaw-executor/`
2. Run `start.bat` (Windows) or `bash start.sh` (Mac/Linux)
3. Open `miniclaw-web/index.html` in your browser
