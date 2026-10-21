# 🤖 Mini RAG Chatbot

一个基于 FastAPI 和 DeepSeek 的简易知识库流式聊天机器人。

## ✨ 功能特性
- 📄 支持上传 TXT 格式的知识库文件
- ⚡ 使用 `httpx` 进行异步请求
- 🌊 支持 SSE (Server-Sent Events) 流式打字机输出
- 🔒 安全的 API Key 管理（通过 `.env`）

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt