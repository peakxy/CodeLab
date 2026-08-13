# Featured pattern library

These SVG patterns were migrated from `hugo_main`. The 25 source `featured.svg`
files contain 11 unique designs, so this directory stores one copy of each design.

Use a pattern from an article's front matter:

```yaml
featureimage: "img/featured-patterns/pytips.svg"
```

Blowfish resolves this path through Hugo's global `assets` resources. A page-local
`featured.svg` still takes precedence when no `featureimage` is configured.

## Source mapping

| Pattern | Source article bundles using the same design |
| --- | --- |
| `bayesianopt.svg` | `bayesianopt`, `cloud-server-build`, `llm-engineering-note`, `philosophy-of-programming` |
| `code-collaboration-scheme.svg` | `code-collaboration-scheme`, `llm-foundation-notes` |
| `ctm-note.svg` | `ctm-note`, `moravecs-paradox`, `neo4j-basics`, `predictive-coding-survey` |
| `cumcm2024.svg` | `cumcm2024`, `schedule-management-report`, `trials-and-growth`, `ubuntu-note` |
| `hugo-blog.svg` | `hugo-blog`, `rstar-note` |
| `llm-memory.svg` | `llm-memory`, `note-to-blog-report` |
| `llm-training-playbook.svg` | `llm-training-playbook`, `mysql-basics` |
| `localoverleaf.svg` | `localoverleaf` |
| `plugin-writing-experience.svg` | `plugin-writing-experience` |
| `pytips.svg` | `pytips` |
| `qdrant-feature-guide.svg` | `qdrant-feature-guide`, `rag-report` |

All 25 source `background.svg` files are identical. Their single unique design is
stored at `assets/img/background-patterns/hugo-main.svg`.
