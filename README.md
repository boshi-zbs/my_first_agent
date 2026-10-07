#我的第一个Agent

## 架构说明
用户输入->加入history->调模型->解析返回
- **是工具调用**：执行工具->结果加入history->回到调模型
- **不是工具调用**：直接输出回答
### 关键设计：
- history 超过 4 条时压缩成摘要，控制 token 消耗
- max_steps=5 防止无限循环
- 工具返回格式不固定，parse_tool_call 兼容多种格式
- 工具层做安全边界，不信任模型传来的参数

## 这是什么
一个命令行Agent,支持多工具调用、上下文记忆、安全边界

## 怎么运行
1.安装依赖：`pip install openai python-dotenv`
2.在`python_learn/`下建`.env`,写入`API_KEY=你的key`
3.进入`model/`目录：`cd model`
4.运行`python main.py`
## 文件说明
- `main.py`:入口
- `chat.py`:主循环、system prompt生成、日志
- `tools.py`:工具定义、注册表、执行器
- `llm.py`:初始化LLM客户端
- `parser.py`:解析模型返回的工具调用

## 已实现的工具
- `search_web(query)`:博查在线搜索
- `read_file(path)`:读取model/下的文件
- `calculator(expression)`:计算数学表达式

## 安全边界
- `read_file`只允许读model/下的文件
- `calculator`只允许基本数学运算，拒绝函数调用

## 日志
每轮工具调用记录写入`agent_logs.json`。

## 运行示例
**你**：搜索python教程
**本轮工具调用记录**：
- **第1步**：search_web({'query': 'python教程'}) → 
- 
标题：【免费】python基础教程资源-CSDN文库 资源-CSDN文库

摘要：需积分: 0 95 浏览量 2018-02-24 11:02:16 上传 评论 Pyhon基础教程 浏览:46 Python 基础教程:python 安装,基本概念,运算符和表达式等等 PYTHON基础教程 浏览:188 课程从 Python 开发环境搭建开始,随后介绍了 Python 的基础知识和基本概念,包括列表、元组、字符串、字典以及各种语句。然后,循序渐进地介绍了一些相对高级的主题,包括抽象、异常、文件、GUI,网络编程,爬虫等。 python教程基础 浏览:88 python教程使用, 包含一些python的基础用途,适合刚入门 python基础教程 浏览:24 里面是培训机构的python基础视频的内容,有视频,文档,用到的工具等. pythonpdf教程-python基础教程pdf.pdf 浏览:67 pythonpdf教程_python基础教程pdf Python 学习路线图 一、 Python 学习的四个阶段 第一阶段 该阶段首先通过介绍不同领域的三种操作系统,操作系统的发展简史以及 Linux 系统的文件目录结构让大家对 Linux 系统有一个... python基础教程源代码-python基础教程第三版源代码.pdf 浏览:136 《Python基础教程》第三版源代码是一份详细的学习资源,涵盖了Python编程的多个核心概念和实践技巧。这个源代码集合包括了从基础语法到高级特性的各种示例,旨在帮助初学者逐步掌握Python编程。 在Python的基础部分... python基础教程第二版答案-Python基础教程(第2版).pdf 浏览:152 5星·资源好评率100% 《Python基础教程(第2版)》是一本全面介绍Python编程的指南,适合初学者入门。Python作为一种解释型、面向对象、动态数据类型的高级程序设计语言,因其

链接：https://download.csdn.net/download/steven_88888/10256636

标题：如何实现python视频教程的具体操作步骤_mob649e816aeef7的技术博客_51CTO博客

摘要：©著作权归作者所有:来自51CTO博客作者mob649e816aeef7的原创作品,请联系作者获取转载授权,否则将追究法律责任 Python视频教程 简介 Python是一种高级编程语言,它简单易学,功能强大,广泛应用于数据分析、人工智能、Web开发等领域。对于初学者来说,视频教程是学习Python的一种很好的方式。本文将介绍一些优秀的Python视频教程,并提供一些示例代码帮助读者更好地理解。 1. Coursera上的Python for Everybody Coursera上的Python for Everybody是由密歇根大学提供的一门免费的Python入门课程。该课程深入浅出地介绍了Python的基础知识和编程概念,并通过实践项目帮助学生巩固所学的知识。 以下是一个简单的Python示例代码,演示了如何打印"Hello, World!": print("Hello, World!") 2. YouTube上的Corey Schafer Python教程 Corey Schafer在YouTube上提供了一系列Python教程,从Python的基础知识到高级主题都有涉及。他的教程通俗易懂,深入浅出,非常适合初学者。 以下是一个示例代码,演示了如何定义一个函数并调用它: def greet(name): print("Hello, " + name + "!")greet("Alice") 3. Udemy上的Complete Python Bootcamp Udemy上的Complete Python Bootcamp是一门全面的Python教程,由Jose Portilla教授提供。该教程包含大量的练习和项目,帮助学生实践他们所学的知识。 以下是一个示例代码,演示了如何使用条件语句判断一个数字是奇数还是偶数: number = 5if number % 2 ==

链接：https://blog.51cto.com/u_16175526/6706823

标题：Python教程(原文).docx_淘豆网

摘要：Python教程(原文) 来自淘豆网www.taodocs.com转载请标明出处. 微信 客服 手机 查看

链接：https://www.taodocs.com/p-419930470.html

**Agent**:根据网络搜索结果，我为您整理了一些Python教程相关的资源，主要分为文档资料和视频课程两类：

**一、文档与基础学习资料**
- **CSDN文库免费资源合集**：该平台提供了一份免费的Python基础教程资源，内容从开发环境搭建、基本概念、运算符与表达式，到列表、元组、字符串、字典等数据结构，再到抽象、异常、文件处理、GUI、网络编程及爬虫等进阶主题均有覆盖。此外，还包含了《Python基础教程》第三版的源代码、PDF教程以及第二版答案等辅助材料。
- **淘豆网文档**：站内转载了一份《Python教程(原文)》的文档，可供在线查看。

**二、优质视频教程推荐**
根据51CTO博客的整理，以下几个视频课程适合不同需求的学习者：
- **Coursera上的“Python for Everybody”**：由密歇根大学提供，是一门免费的入门课程，通过深入浅出的方式介绍基础知识并搭配实践项目。
- **YouTube上的Corey Schafer Python教程**：系列视频涵盖了从基础到高级的主题，讲解通俗易懂，非常适合初学者入门。
- **Udemy上的“Complete Python Bootcamp”**：由Jose Portilla教授主讲，包含大量练习和项目实战，内容较为全面。

您可以根据自己喜欢的学习方式（阅读文档或观看视频）来选择对应的资源进行学习。

你：