# Coursera Hub

一个使用Flet框架开发的跨平台桌面客户端，用于下载Coursera网站的视频和课件资源。

## 功能特点

- 支持多种认证方式：CAUTH、浏览器Cookie、用户名密码
- 列出已注册的课程
- 下载课程视频、字幕、测验和笔记本
- 自定义下载路径和视频分辨率
- 实时显示下载进度和日志输出

## 系统要求

- Python 3.8 或更高版本
- uv（推荐的Python包管理器）

## 安装步骤

### 1. 安装依赖

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv add flet requests beautifulsoup4 lxml
```

### 2. 运行应用

```bash
uv run python main.py
```

## 使用说明

1. **选择认证方式**：
   - **CAUTH**：从浏览器中获取 CAUTH 值
   - **浏览器Cookie**：自动从浏览器提取 CAUTH 值
   - **用户名密码**：使用 Coursera 账号登录

2. **输入课程信息**：
   - 课程名称：要下载的课程名称
   - 下载路径：选择保存课程的位置（点击"浏览"按钮选择）

3. **设置下载选项**：
   - 字幕语言：从下拉菜单中选择
   - 视频分辨率：720p、1080p 或 480p
   - 下载测验：勾选下载课程测验
   - 下载笔记本：勾选下载课程笔记本

4. **执行操作**：
   - **列出课程**：显示已注册的所有课程
   - **下载课程**：开始下载指定课程

## 获取 CAUTH 值

1. 打开浏览器并登录 Coursera 网站
2. 按下 F12 打开开发者工具
3. 切换到 "Application" 或 "Storage" 标签
4. 找到 "Cookies" 并选择 `https://www.coursera.org`
5. 查找并复制 CAUTH 的值

## 打包应用

使用 PyInstaller 可以将应用打包成独立可执行文件：

```bash
# 安装 PyInstaller
uv add pyinstaller

# 打包应用
pyinstaller --onefile --windowed --name "Coursera Hub" main.py
```

打包后的可执行文件会生成在 `dist` 目录中。

## 许可证

MIT