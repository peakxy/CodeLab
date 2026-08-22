---
title: "Map 原理分析"
date: 2026-08-22T23:06:49+08:00
draft: false
description: "梳理 Go Map 的旧版哈希桶实现、扩容机制，以及 Go 1.24 Swiss Table 的核心原理。"
tags: ["Go", "Map"]
featureimage: "img/featured-patterns/pytips.svg"
showViews: true
showLikes: true
firebaseStatsId: "map-principles-analysis"
---

# 旧版 Map 的整体结构

Go 1.23 及以前，Map 本质上是一个**哈希表**，最核心的数据结构是 `hmap` 和 `bmap`。

```go
type hmap struct {
    count     int
    flags     uint8
    B         uint8
    noverflow uint16
    hash0     uint32

    buckets    unsafe.Pointer
    oldbuckets unsafe.Pointer
    nevacuate  uintptr

    extra *mapextra
}
```

其中：

- `count`：当前元素数量，`len(map)` 基本就是取它；
- `B`：bucket 数量的指数，bucket 数量是 `2^B`；
- `hash0`：每个 map 自己的哈希种子，降低恶意哈希碰撞风险；
- `buckets`：当前桶数组；
- `oldbuckets`：扩容时指向旧桶；
- `nevacuate`：记录扩容搬迁进度；
- `noverflow`：溢出桶数量。

一个 `bmap` 就是我们常说的一个 **bucket**，一个 bucket 可以放 **8 个 key/value**，并且有一个 `tophash[8]` 保存每个 key 哈希值的一部分。源码层面的 `bmap` 看起来只有 `tophash`，实际编译器会根据具体 key/value 类型构造出 key、value 和 overflow 指针的存储空间。

可以画成：

```text
hmap
 │
 ├── buckets
 │     │
 │     ├── bucket0
 │     │    ├── tophash[8]
 │     │    ├── keys[8]
 │     │    ├── values[8]
 │     │    └── overflow ──> overflow bucket
 │     │
 │     ├── bucket1
 │     └── ...
 │
 └── oldbuckets     // 扩容期间使用
```

bucket 里面不是按照 `key/value/key/value...` 交叉存储，而是**先连续存 key，再连续存 value**，这样可以**减少因为类型对齐产生的内存浪费**。

---

# 查询、写入以及哈希冲突怎么解决

这部分是 Map 原理里最重要的。

假设执行：

```go
v := m[key]
```

首先根据 `key` 和 `hash0` 计算哈希值：

```text
hash = hash(key, hash0)
```

旧版实现大致把 hash 分成两部分使用：

```text
hash
├── 高位：生成 tophash，加速 bucket 内查找
└── 低 B 位：定位 bucket
```

## 查询过程

比如：

```text
bucketIndex = hash & (2^B - 1)
```

用低 `B` 位找到 bucket。

然后：

1. 取 hash 的高位生成 `tophash`；
2. 遍历 bucket 的 8 个槽位；
3. 先比较 `tophash`；
4. `tophash` 相同才真正比较 key；
5. 找不到就继续查 overflow bucket；
6. 都找不到就说明 key 不存在。

这样做的好处是：**先用很便宜的 `tophash` 比较过滤掉绝大多数 key，减少真正的 key 比较。**

旧实现的查询源码也是先定位 bucket，再比较 `tophash`，最后才调用 key 的 equal 方法。

---

## 写入过程

执行：

```go
m[key] = value
```

基本也是：

```text
计算 hash
   ↓
定位 bucket
   ↓
比较 tophash
   ↓
找到相同 key？
  ↙        ↘
是          否
↓           ↓
更新 value  找空槽
             ↓
        bucket 满了？
         ↙      ↘
        否       是
        ↓        ↓
      写入    overflow bucket
```

如果对应 bucket 的 8 个槽全部满了，就会创建 **overflow bucket**，通过**链式结构**继续存。

所以旧版 Go Map 解决哈希冲突，本质上可以理解为：

**bucket + overflow bucket 的链式处理。**

---

# 什么时候扩容？怎么扩？

旧版 Go Map 有两个比较重要的扩容条件。

## 装载因子过高

旧实现的装载因子：

```text
loadFactor = count / 2^B
```

**超过大约 6.5 时触发扩容。** 原因很好理解，每个 bucket 最多放 8 个元素，如果平均已经放到 6.5 个左右，就意味着发生冲突和 overflow 的概率越来越高，查询性能开始下降。这种情况下：

```text
B = B + 1

bucket 数：
2^B  →  2^(B+1)
```

也就是 **2 倍扩容**。

---

## overflow bucket 太多

还有一种情况：**元素并不多，但是 overflow bucket 特别多**

比如不断进行 **插入 → 删除 → 插入 → 删除**，可能导致 bucket 分布非常松散。

这时候装载因子不一定超过 6.5，但是查找效率已经下降了。

Go 会进行一次：**等量扩容**

也就是：**bucket 数量基本不变，但是把元素重新整理到新的 buckets 中，把大量没必要的 overflow bucket 消掉**。

所以两个扩容可以概括成：

| 场景          | 扩容方式 | 目的     |
| ------------- | -------- | -------- |
| 元素太多      | 2 倍扩容 | 增加空间 |
| overflow 太多 | 等量扩容 | 整理碎片 |

---

# 扩容为什么不是一次搬完？

假设 map 特别大，如果扩容的时候一次性把几百万个 key 全搬完：

```text
一次插入
   ↓
触发扩容
   ↓
搬几百万元素
   ↓
延迟突然非常高
```

所以旧版 Go Map 使用的是**渐进式扩容**。

`hashGrow()` 主要先：

```text
buckets → oldbuckets
申请新的 buckets
```

真正的数据搬迁是在后续 map 操作过程中逐渐完成。

例如执行：

```go
m[k] = v
delete(m, k)
```

会顺手做一部分 `growWork / evacuate`。

所以一次扩容 ≠ 一次性搬完全部数据

而是：

```text
第 1 次写 → 搬一点
第 2 次写 → 搬一点
第 3 次写 → 搬一点
...
```

以此平摊扩容成本。书里的源码分析同样指出，`hashGrow` 主要建立新旧 buckets 关系，真正搬迁由后续 `growWork` 完成。

这也是一个很好的面试关键词：**空间换时间 + 增量迁移，降低单次操作的尾延迟。**

---

# 并发和遍历有什么特点？

## 普通 Map 不是并发安全的

Go 原生的 `map[K]V` **不支持无同步的并发读写、并发写。**

例如：

```go
go func() {
    m["a"] = 1
}()

go func() {
    fmt.Println(m["a"])
}()
```

这是 data race，运行时也可能直接报：

```text
fatal error: concurrent map read and map write
```

或者：

```text
fatal error: concurrent map writes
```

所以普通 map 不是线程安全的，需要外部加锁或使用 `sync.Map`。通常可以选择 `sync.RWMutex + map`，或者在特定场景下使用 `sync.Map`。

---

## Map 遍历顺序没有保证

```go
for k, v := range m {
}
```

**不能依赖遍历顺序。**

旧版实现中初始化 iterator 时会**随机选择**：

```text
startBucket
offset
```

从而让遍历没有稳定顺序。

所以千万不要写：

```go
for k := range m {
    // 默认认为按照插入顺序
}
```

如果业务确实需要按顺序遍历，标准做法分三步：先把 map 的所有 key 收集到一个 slice 里，再对这个 slice 排序，最后按排序后的 key 逐个去 map 里取值。

```go
// 1. 收集所有 key
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}

// 2. 对 key 排序
sort.Strings(keys)

// 3. 按排序后的 key 遍历取值
for _, k := range keys {
    v := m[k]
    fmt.Println(k, v)
}
```

---

## 遍历期间可以 delete / insert，但有明确语义

这个很容易和「并发读写不安全」混淆。

在**同一个 goroutine 的 range 过程中**：

```go
for k := range m {
    delete(m, k)
}
```

这是允许的。

新增元素则**可能遍历到，也可能遍历不到**。

但是**另一个 goroutine 无同步地同时修改 map，仍然是不安全的。**

---

# Go 1.24 的 Swiss Table

从 Go 1.24 开始，我们平时用的 `map` 底层换了一套实现，名字叫 **Swiss Table**。官方的 Go 1.24 Release Notes 和 Go Blog 都明确说明了这一点。

**旧版的结构**是一层层往下挂的：

```text
hmap（总控）
  ↓
bucket（桶，一桶 8 个格子）
  ↓
装不下了？挂一个 overflow bucket
  ↓
再装不下？再挂一个
```

**新版的结构**变成了分层管理：

```text
Map（总控）
  ↓
Directory（目录，负责分配）
  ↓
Table（一张小表）
  ↓
Group（一组，8 个格子）
  ↓
8 个 slot + 一张 control word（标签条）
```

这是新旧两版最本质的区别。

下面逐层看新版各层的核心结构体。

**顶层 Map 结构体**（对应旧版的 hmap），源码在 `internal/runtime/maps/map.go`：

```go
type Map struct {
    used              uint64         // 元素个数，len() 直接取它
    seed              uintptr        // 哈希种子，每个 map 随机生成
    dirPtr            unsafe.Pointer // 指向 Directory；小 map 时直接指向单个 group
    dirLen            int            // Directory 长度，0 表示小 map 模式
    globalDepth       uint8          // 用哈希高位多少 bit 选 table
    globalShift       uint8          // 哈希右移位数，64 - globalDepth
    writing           uint8          // 并发写检测标记
    tombstonePossible bool           // 是否可能存在 tombstone（墓碑）
    clearSeq          uint64         // 清空操作序号，遍历中检测 clear
}
```

其中：

- `used`：当前元素总数，`len(map)` 就是读这个字段，所以 O(1)；
- `seed`：每个 map 独有的随机哈希种子，防止哈希碰撞攻击；
- `dirPtr` / `dirLen`：指向 Directory（一个 `*table` 指针数组）。`dirLen == 0` 时是小 map 优化，数据直接存在一个 group 里，不需要 Directory 和 Table；
- `globalDepth` / `globalShift`：可扩展哈希的核心参数，用哈希的高位选 table，`dirLen = 2^globalDepth`；
- `writing`：并发写检测标记，多个 goroutine 同时写会触发 panic；
- `tombstonePossible`：标记是否可能有墓碑（删除标记），影响遍历和清理逻辑。

**Table 结构体**（一张独立的瑞士哈希表），源码在 `internal/runtime/maps/table.go`：

```go
type table struct {
    used       uint16          // 当前元素个数
    capacity   uint16          // 总 slot 数，始终是 2^N
    growthLeft uint16          // 还能放多少元素就需要扩容（含 tombstone）
    localDepth uint8           // 该 table 创建时的深度，可能小于 globalDepth
    index      int             // 在 Directory 中的起始索引，-1 表示已失效
    groups     groupsReference // Group 数组，每个 Group 8 个 slot + control word
}
```

其中：

- `capacity`：单张 table 最大不超过 `maxTableCapacity`（1024 个 slot），超过就拆分成两张 table；
- `growthLeft`：剩余可写入空间，用完就触发 rehash（原地翻倍扩容或拆分成两张 table）；
- `localDepth`：该 table 自己的深度，Directory 中多个索引可能指向同一张 table，所以它可能小于 `globalDepth`；
- `groups`：实际存储数据的 Group 数组。

**Directory** 本身不是复杂结构体，就是一个 `*table` 指针数组，长度为 `2^globalDepth`。多个索引可以指向同一张 table——这是可扩展哈希（extendible hashing）的关键，让单张 table 拆分时不需要立刻把整个目录翻倍。

**Group** 是最小存储单元，8 个 slot 加一个 8 字节 control word：

```text
Group
├── ctrl [8]uint8   // 8 字节控制字，1 字节对应 1 个 slot
└── slots [8]        // 8 个 slot，每个存一个 key/value
```

整体结构可以画成：

```text
Map
 │
 ├── used / seed / globalDepth ...   // 元数据
 │
 └── dirPtr → Directory（*table 数组，长度 2^globalDepth）
          │
          ├── table0
          │    ├── used / capacity / growthLeft / localDepth
          │    └── groups[]
          │         ├── Group0: ctrl[8] + slot0~7
          │         ├── Group1: ctrl[8] + slot0~7
          │         └── ...
          │
          ├── table1 （可能和 table0 指向同一张表）
          └── ...
```

另外有个**小 map 优化**：如果元素不超过 8 个，`dirPtr` 直接指向一个单独的 Group，不需要 Directory 和 Table，省一次间接寻址和内存分配。

---

## Swiss Table 的 Group：8 个格子一组

新版里，**8 个 slot（格子）组成一个 Group**，就像快递柜里一排有 8 个柜门。

关键在于：这 8 个格子旁边，还跟着一张 **control word（标签条）**，正好 8 个字节，**每个字节对应一个格子**。

每个格子对应的那个字节（control byte），只可能是三种状态：

- **empty**：这个格子是空的
- **deleted**：这里曾经存过东西，后来删了
- **H2**：这个格子被占用了，字节里存的是该 key 哈希值的低 7 位

那 H2 是什么？一个 key 的哈希值会被拆成两部分：

```text
哈希值（64 位）
├── H1（高 57 位）：定位 Group，构造探查顺序
└── H2（低 7 位）：在 Group 内快速筛选
```

简单说：**H1 负责定位到哪一组，H2 负责在组内快速判断"这个格子可能是我要找的吗"**。当前 Go 源码也是这样定义的。

---

## 查一个 key，到底经历了什么？

比如你写 `m[key]`，新版是这么找的：

1. 先算 `hash(key)`
2. 用哈希的高位选到某个 Table
3. 用 H1 确定一个"探查顺序"（probe sequence），也就是先看哪组、再看哪组
4. 找到第一个 Group 后，**一次性把这组 8 个格子的标签字节全扫一遍**
5. 筛出 H2 相同的格子（可能有多个）
6. 只有这些候选格子，才会真正去比较 key 是不是相等

**最大的优化就在第 4 步**：8 个标签字节可以通过位运算（类似 SIMD 的方式）**一次比较完**，而不是像旧版那样 slot0 比一次、slot1 比一次、slot2 比一次……

这就好比你找快递：旧版是一个个柜门拉开看；新版是先扫一眼柜门上的取件码尾号，尾号对得上的才去开柜门——大部分柜子连开都不用开。所以 CPU 缓存命中率更高，查得也更快。

官方源码的查询逻辑也是如此：先通过 H1 构造探查顺序，然后对整个 Group 调用 `matchH2` 筛出候选 slot，只有 H2 命中的才真正比较 key；遇到 empty 就可以直接结束查找。

---

## 哈希冲突了怎么办？

这是新旧版另一个本质区别。

**旧版用的是"链地址"思想**：一个桶装不下了，就在后面挂一个 overflow bucket，像链条一样接下去。

```text
bucket → overflow → overflow
```

**新版 Swiss Table 用的是"开放寻址"**：这一组满了或者冲突了，就按照探查顺序（probe sequence）去下一组找空位，不挂链条。

```text
Group A 满了 → 去 Group B → 再去 Group C
```

所以如果有人问"Go Map 怎么解决哈希冲突"，一定要分版本说：**旧实现靠 overflow bucket 挂链；Go 1.24 之后的 Swiss Table 用开放寻址 + 顺序探查。**

---

# Swiss Table 怎么扩容？

新版没有简单粗暴地把整个 map 一次性翻倍扩容。

原因是 Go 很在意服务器的 **tail latency（尾延迟）**：想象一个几 GB 的大 map，如果某次插入突然要把整张表复制一遍，那这一次操作的延迟会非常夸张，可能把线上请求卡住。

所以 Go 在 Swiss Table 外面又套了一层 **extendible hashing（可扩展哈希）**，结构大概是这样：

```text
Map
└── Directory（目录）
    ├── Table A
    │   └── Groups
    ├── Table B
    │   └── Groups
    └── Table C
```

哈希的高位用来选择进哪个 Table。当前实现中，**一个 Table 最多装 1024 个 slot**。Table 小的时候可以自己扩容；达到上限后，就把它**拆成两个 Table**：

```text
Table
      ↓
    split
   ↙     ↘
 T1       T2
```

必要时 Directory 也跟着翻倍。这样做的好处是：**每次只拆一个 Table，而不是整个 map 一起搬**，单次扩容的成本就被控制住了。官方源码明确把单个 table 最大容量设为 1024。

另外，Swiss Table 每组 8 个格子，但**平均最多只放 7 个**，也就是最大平均装载率：

```text
7 / 8 = 87.5%
```

留一个空位是为了让探查（probing）更高效，当前源码中的 `maxAvgGroupLoad = 7` 就是这个意思。

---

# 面试官最可能继续追问的几个点

你把 Map 讲到这个程度以后，我觉得下一轮大概率就是围绕这些问：

1. **为什么 bucket 是 8 个元素？**
2. **为什么 `tophash` 能提高查询效率？**
3. **为什么 Map 元素不能直接取地址？**
4. **扩容的时候一个 key 怎么判断去 X bucket 还是 Y bucket？**
5. **为什么遍历是无序的？**
6. **为什么并发读写 Map 会 panic？**
7. **`sync.Map` 和 `map + RWMutex` 怎么选？**
8. **Swiss Table 为什么比旧 Map 快？**
9. **Swiss Table 的 tombstone 是干什么的？**
10. **为什么 Swiss Table 用开放寻址后，Go 还要搞 Directory + 多 Table？**

其中 **第 4、8、9、10** 特别适合把你和只背旧版 `hmap/bmap` 的候选人区分开。

> （注：部分内容可能由 AI 生成）
