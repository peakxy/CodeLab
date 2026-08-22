# CodeLab

CodeLab 是技术博客，主要记录 Go、全栈开发、AI Agent，以及真实工程问题的排查和解决过程。

博客基于 [Hugo](https://gohugo.io/) 和 [Blowfish](https://blowfish.page/) 构建，并通过 GitHub Actions 发布到 GitHub Pages。

- 在线访问：<https://peakxy.github.io/CodeLab/>
- 内容目录：`content/`
- 主题配置：`config/_default/`

## 本地运行

请先安装 Hugo Extended，然后克隆仓库并初始化主题子模块：

```bash
git clone --recurse-submodules https://github.com/peakxy/CodeLab.git
cd CodeLab
hugo server -D
```

浏览器访问 <http://localhost:1313/CodeLab/> 即可预览博客。

## 怎么为博客贡献

欢迎通过 Issue 或 Pull Request 补充文章、修正文案和改进网站。

创建新文章前，请在仓库根目录运行：

```bash
hugo new content blog/<分类>/<文章名>/index.md
```

例如：

```bash
hugo new content blog/go/getting-started/index.md
```

随后编辑生成的 `index.md`：

1. 填写标题、摘要和标签，并完成正文。
2. 将 `draft` 改为 `false` 后再正式发布。
3. 保持 `firebaseStatsId` 唯一且稳定；移动或重命名文章时不要修改它，以免丢失原有浏览量和点赞数据。
4. 提交前运行以下命令检查内容并构建站点：

   ```bash
   python3 scripts/validate_firebase_stats.py
   hugo --minify
   ```

确认构建成功后，将变更提交到自己的分支并发起 Pull Request。
