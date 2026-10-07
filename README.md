#我的第一个Agent

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