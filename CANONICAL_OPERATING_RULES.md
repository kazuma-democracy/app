# Canonical Operating Rules

このrepositoryで作業するagent/threadは、ローカルの `AGENTS.md` / canonical docs / Queue と対象タスクの正本に加えて、次のcross-project canonical operating addendumをGitHubから直接fresh-readすること。

```text
repository: kazuma-democracy/autonomous-dev-oss-lab
ref: main
path: docs/TWO_LAYER_OPERATING_POLICY_2026-09-07.md
```

このファイルは要約ではなく参照ポインタである。上記canonical文書の内容を言い換えず、そのまま適用する。

ローカル固有の製品契約・安全境界がより厳しい場合は、より厳しい規則を維持する。実行可能なrunner/script/configの状態は、実環境で検証されるまで断定しない。
