# DevToolbox

## 项目简介

DevToolbox 是一个本地运行的开发工具包，使用 FastAPI 提供后端接口，使用原生 HTML、CSS、JavaScript 提供浏览器界面。首期包含 JSON 自动修复与格式化、文本对比、Markdown 渲染三个工具。

## 核心功能

- 主页：集中展示当前可用工具和规划中的工具。
- JSON 自动修复与格式化：支持修复不规范 JSON、类 Python 字典、尾逗号等输入，保留中文字符，并提供格式化、复制、层级折叠和字号调节。
- 文本对比：支持普通文本按行对比、文件导入、左右交换、差异统计。
- Markdown 渲染：支持 raw Markdown 左右双栏实时预览，可将 `\n`、`\t`、`\\`、`\"`、`\uXXXX` 等转义符转换为真实含义后再渲染。
- Markdown 渲染对比：在文本对比工具中勾选“Markdown 渲染”后，后端会先渲染并清洗 Markdown，再按可见文本计算差异。

## 环境要求

- macOS 或其他可运行 Python 的系统。
- Python 3.11 或更高版本。

## 安装与依赖

建议在项目目录内创建虚拟环境：

```bash
cd /Users/xieyifei.10/PycharmProjects/DevToolbox
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

如果虚拟环境目录名为 `venv`，激活命令为：

```bash
source venv/bin/activate
```

## 配置说明

当前项目不需要 `.env` 配置文件。服务默认可监听 `127.0.0.1:8000`。如果端口被占用，请换用其他端口启动，不要强制结束占用端口的进程。

## 快速开始

```bash
cd /Users/xieyifei.10/PycharmProjects/DevToolbox
source .venv/bin/activate
uvicorn devtoolbox.main:app --host 127.0.0.1 --port 8000
```

也可以直接执行入口文件，适合 PyCharm 的 Python 运行配置：

```bash
/Users/xieyifei.10/PycharmProjects/DevToolbox/.venv/bin/python \
  /Users/xieyifei.10/PycharmProjects/DevToolbox/devtoolbox/main.py \
  --host 127.0.0.1 \
  --port 8010 \
  --reload
```

如果使用默认 `8000` 端口，启动后访问：

```text
http://127.0.0.1:8000
```

如果使用上面的 PyCharm 直接入口命令，访问：

```text
http://127.0.0.1:8010
```

如需用 uvicorn 命令换端口：

```bash
uvicorn devtoolbox.main:app --host 127.0.0.1 --port 8010
```

## 目录结构

```text
DevToolbox/
├── devtoolbox/
│   ├── main.py                 # FastAPI 入口、页面路由和 API 路由
│   ├── services/               # JSON 修复、文本 diff 等服务层逻辑
│   └── static/                 # 原生前端页面、样式和脚本
├── tests/                      # 单元测试与接口测试
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
└── .log                        # 任务过程、调试结论和验证记录
```

## 开发与测试

```bash
cd /Users/xieyifei.10/PycharmProjects/DevToolbox
source .venv/bin/activate
pytest
```

建议在修改功能后同时检查页面入口：

```bash
curl http://127.0.0.1:8000/health
```

## 协作说明

提交代码前只提交本轮自己改动的内容，避免误包含其他协作者在本地仓库中的改动。
