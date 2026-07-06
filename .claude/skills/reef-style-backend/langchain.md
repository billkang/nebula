# LangChain 开发规范

## 概述

LangChain 是 Python 生态中的 AI 集成框架，提供统一的 API 来调用 LLM、管理对话、构建 RAG 应用。

## 核心概念

### ChatModel
LangChain 的中央 API，用于与大语言模型交互。

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 初始化
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 基础调用
response = llm.invoke([
    SystemMessage(content="你是一个专业的 Python 开发者助手"),
    HumanMessage(content="解释 FastAPI 的依赖注入")
])
print(response.content)
```

**最佳实践：**
- `ChatOpenAI` / `ChatAnthropic` 在应用初始化时创建一次，通过依赖注入传递
- 不要在每个请求中重新创建 LLM 实例
- `temperature=0` 用于确定性结果，`temperature>0` 用于创意场景
- API Key 通过环境变量读取，不硬编码

### Prompt Template

结构化提示词模板：

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，请用{language}回答"),
    ("human", "{question}"),
])

chain = prompt | llm
result = chain.invoke({"role": "Python专家", "language": "中文", "question": "什么是异步编程？"})
```

### Tool / 函数调用

AI 模型调用外部函数的能力：

```python
from langchain_core.tools import tool

@tool
def get_user_order(user_id: str) -> list[dict]:
    """获取用户订单信息"""
    # 实际业务逻辑调用 Service 层
    return order_service.get_orders(user_id)


# 绑定工具后调用
llm_with_tools = llm.bind_tools([get_user_order])
```

**最佳实践：**
- `@tool` 的 docstring 会被模型理解，写清楚参数含义和返回值格式
- 工具函数内部调用 Service 层，不在工具内写业务逻辑
- `bind_tools([])` 传工具数组，不逐个 `.bind()` 调用

### Chain / LCEL

LangChain Expression Language — 声明式管道：

```python
from langchain_core.output_parsers import StrOutputParser

# 链式组装
chain = prompt | llm | StrOutputParser()

# 执行
result = chain.invoke({"question": "Python 异步编程的最佳实践？"})
```

### RAG（检索增强生成）

```python
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

# 创建向量存储
vector_store = InMemoryVectorStore.from_texts(
    texts=["文档内容1", "文档内容2"],
    embedding=OpenAIEmbeddings()
)

# 检索
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# RAG 链
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

combine_docs_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
result = rag_chain.invoke({"question": "某个话题"})
```

## 依赖管理

```bash
# 基础安装
uv add langchain langchain-openai

# 按需安装其他 provider
uv add langchain-anthropic   # Claude
uv add langchain-google-ai   # Gemini

# 向量存储
uv add langchain-community

# RAG 相关
uv add chromadb tiktoken
```

## 常见坑

| 场景 | 问题 | 正确做法 |
|------|------|---------|
| API Key 管理 | 硬编码在代码中 | 从 `os.getenv("OPENAI_API_KEY")` 读取 |
| 每次请求新建 LLM | 性能差、连接池耗尽 | 应用启动时创建单例，通过 DI 注入 |
| 工具函数逻辑过重 | 工具内包含全部业务逻辑 | 工具只做参数解析 + 调用 Service |
| 忽略 `async` 支持 | LCEL 链中调同步 IO | 使用 `ainvoke()` 和 async retriever |
| prompt 不设 system message | 模型行为不可控 | 始终设置 system message 定义角色和约束 |
