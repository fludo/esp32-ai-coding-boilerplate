# Third-Party Notices

## ai-coding-project-boilerplate

The Claude Code rules, agents, commands and generic skills under `.claude/`, `CLAUDE.md` and `docs/guides/` are adapted from
[fludo/ai-coding-project-boilerplate](https://github.com/fludo/ai-coding-project-boilerplate)
(fork of [shinpr/ai-coding-project-boilerplate](https://github.com/shinpr/ai-coding-project-boilerplate)), under the following license:

```
MIT License

Copyright (c) 2025 Shinsuke Kagawa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## esp32-claude-workbench

The following files are copied or adapted from
[agodianel/esp32-claude-workbench](https://github.com/agodianel/esp32-claude-workbench) at commit `f4b67c33f6fb1e6e3e3be7eaba7ca88128da8966`:

- `.claude/skills/esp32-platform/references/chips/*.json` (copied)
- `.claude/skills/esp32-platform/references/pin-limitations.md` (adapted from `skills/esp32-pin-audit/references/hardware_limitations.md`)
- `.claude/skills/esp32-debugging/references/*.md` (copied with an added header, from `skills/esp32-crash-review/references/`, `skills/esp32-build-fix/references/`, `skills/esp32-log-triage/references/`)

```
MIT License

Copyright (c) 2026 ESP32 Claude Workbench Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## claude-skills-esp32

Behavioral rails (board safety, don't-fabricate, secrets injection) and regression prompts 1-4 in `docs/guides/skill-regression-prompts.md` are inspired by
[bdherouville/claude-skills-esp32](https://github.com/bdherouville/claude-skills-esp32). No text was copied (the repository carries no license file).
