---
title: 贝叶斯优化
weight: -10
draft: false
description: 贝叶斯优化原理及其MATLAB实现
slug: bayesianopt
language: zh-cn
tags:
  - math
  - MATLAB
  - CUMCM
series:
  - 数学建模
series_order: 1
date: 2024-08-05
lastmod: 2024-12-20
authors:
  - 程序员羊肉
---

## 引用文献

我对于贝叶斯优化的理解也并不多，主要参考下面的内容👇

- [【机器学习】一文看懂贝叶斯优化/Bayesian Optimization](https://blog.csdn.net/qq_27590277/article/details/115451660)

- [一文详解贝叶斯优化（Bayesian Optimization）原理](https://www.cnblogs.com/milliele/p/17782631.html)

- [贝叶斯优化(BayesianOptimization)](https://blog.csdn.net/Leon_winter/article/details/86604553)

- [超参数优---贝叶斯优化及其改进（PBT优化）](https://blog.csdn.net/xys430381_1/article/details/103871212)

- [贝叶斯优化 (Bayesian Optimization)](https://leovan.me/cn/2020/06/bayesian-optimization/)

- [MATLAB官方文档](https://ww2.mathworks.cn/help/stats/bayesopt.html?s_tid=srchtitle_site_search_1_bayesopt)

- [Exploring Bayesian Optimization](https://distill.pub/2020/bayesian-optimization/)

## 优点和算法原理

这里重点描述贝叶斯优化的优点以及其算法原理。如果你只关注“怎么用”，可以先了解贝叶斯优化的优点，然后跳转到[MATLAB用法]({{< relref "#matlab用法" >}})

### 优点

### 算法原理

## MATLAB用法

### 代码一览

```matlab
% 定义目标函数
function y = objectiveFcn(x)
    y = (1 - x.x1)^2 + 100 * (x.x2 - x.x1^2)^2;
end

% 定义优化变量
vars = [optimizableVariable('x1', [-2, 2])
        optimizableVariable('x2', [-2, 2])];

% 执行贝叶斯优化
results = bayesopt(@objectiveFcn, vars, ...
                   'AcquisitionFunctionName', 'expected-improvement-plus', ...
                   'MaxObjectiveEvaluations', 30, ...
                   'IsObjectiveDeterministic', true, ...
                   'Verbose', 1);

% 查看结果
bestPoint = results.XAtMinObjective;
bestObjective = results.MinObjective;

fprintf('最优解 x1: %.4f, x2: %.4f\n', bestPoint.x1, bestPoint.x2);
fprintf('最优目标值: %.4f\n', bestObjective);
```

### 参数说明

Params | Meaning
----- | -----
`AcquisitionFunctionName` | 选择采集函数，这决定了算法在每次采样之后如何选取下一个采样点
`MaxObjectiveEvaluations` | 最大迭代轮次
`IsObjectiveDeterministic` | 如果目标函数是确定的，不包含噪声，则设置为 `true` ；否则设置为 `false`
`Verbose` | 决定了结果输出的详细程度，所有的输出可能包含多张图表

每个参数具体的可选值见官方文档: [bayesopt](https://ww2.mathworks.cn/help/stats/bayesopt.html?s_tid=srchtitle_site_search_1_bayesopt)；官方写的相当细致，还有很多样例。

> [!NOTE] 说明
> 数学建模人必会技能之一就是读文档😝
