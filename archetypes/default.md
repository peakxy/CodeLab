---
# 文章标题，默认根据文件名生成。
title: "{{ replace .Name "-" " " | title }}"
# 发布时间，自动填充为创建文章时的时间。
date: {{ .Date }}
# 新文章先保持草稿，确认内容后改为 false。
draft: true
# 文章摘要，可用于文章列表和 SEO 描述。
description: ""
# 文章标签，没有标签时可以保持为空数组。
tags: []
# 创建文章时随机选择一张封面，生成后保持不变。
featureimage: "{{ index (shuffle (slice "img/featured-patterns/bayesianopt.svg" "img/featured-patterns/code-collaboration-scheme.svg" "img/featured-patterns/ctm-note.svg" "img/featured-patterns/cumcm2024.svg" "img/featured-patterns/hugo-blog.svg" "img/featured-patterns/llm-memory.svg" "img/featured-patterns/llm-training-playbook.svg" "img/featured-patterns/localoverleaf.svg" "img/featured-patterns/plugin-writing-experience.svg" "img/featured-patterns/pytips.svg" "img/featured-patterns/qdrant-feature-guide.svg")) 0 }}"
# 文章详情页是否显示浏览数和点赞数。
showViews: true
showLikes: true
# Keep this ID unchanged when moving or renaming the article.
firebaseStatsId: "{{ .Name }}"
---
