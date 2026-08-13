---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
# Keep this ID unchanged when moving or renaming the article.
firebaseStatsId: "{{ .Name }}"
---
