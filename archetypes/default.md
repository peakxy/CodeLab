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
# 文章详情页是否显示浏览数和点赞数。
showViews: true
showLikes: true
# Keep this ID unchanged when moving or renaming the article.
firebaseStatsId: "{{ .Name }}"
---
