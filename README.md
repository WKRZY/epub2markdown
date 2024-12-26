# epub2markdown

一个将EPUB文件转换为Markdown格式的Python工具，支持图片和元数据处理。

## 功能特点

- 支持将EPUB转换为单个或多个Markdown文件
- 提取并处理图片（保存为文件或嵌入base64编码）
- 保留图书元数据
- 生成目录结构
- 支持嵌套章节
- 转换进度条显示

## 环境要求

- Python 3.12 或更高版本
- requirements.txt中列出的依赖包

## 安装步骤

1. 克隆仓库： 
```bash
git clone https://github.com/yourusername/epub2markdown.git
cd epub2markdown
```
2. 创建虚拟环境（可选但推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Windows系统使用: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```python
from src.epub_reader import EpubReader

# 初始化阅读器，指定epub文件路径
reader = EpubReader("path/to/your/book.epub")

# 转换为单个Markdown文件（包含嵌入式图片）
reader.save_as_single_file_markdown()

# 或转换为多个Markdown文件（图片单独保存）
reader.save_as_markdown()
```

### 可用方法

1. `save_as_markdown(output_dir=None)`: 转换为多个Markdown文件
   - 创建包含章节文件和图片的目录
   - 生成包含元数据和目录的README.md
   - 图片保存在assets目录中

2. `save_as_single_markdown(output_path=None)`: 转换为单个Markdown文件
   - 创建包含所有章节的单个Markdown文件
   - 图片保存在assets目录中
   - 保持图片的相对链接

3. `save_as_single_file_markdown(output_path=None)`: 转换为独立的Markdown文件
   - 创建包含所有内容的单个Markdown文件
   - 图片以base64格式嵌入，无需额外文件
   - 文件可移植性好，但体积较大

4. `analyze()`: 打印图书信息
   - 显示元数据
   - 显示目录结构
   - 预览章节内容

### 输出结构

使用 `save_as_markdown()` 时的目录结构：
```
book_name_markdown/
├── README.md           # 书籍信息和目录
├── chapter_001.md      # 第一章
├── chapter_002.md      # 第二章
└── assets/            # 图片目录
    ├── image1.jpg
    └── image2.png
```

## 贡献

欢迎提交Pull Request来改进这个项目！

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件
