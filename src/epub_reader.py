import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text
import os
import base64
from datetime import datetime
import re
from tqdm import tqdm
from urllib.parse import unquote


class EpubReader:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.book = None
        self.metadata = {}
        self.images = {}  # 存储图片数据

        # 初始化HTML转Markdown转换器
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = False
        self.html2text.body_width = 0
        self.html2text.unicode_snob = True
        self.html2text.skip_internal_links = True

    def load_book(self):
        try:
            self.book = epub.read_epub(self.epub_path)
            return True
        except Exception as e:
            print(f"加载epub文件失败: {str(e)}")
            return False

    def get_metadata(self):
        if not self.book:
            return

        metadata_fields = {
            'title': ('DC', 'title'),
            'creator': ('DC', 'creator'),
            'language': ('DC', 'language'),
            'publisher': ('DC', 'publisher'),
            'identifier': ('DC', 'identifier'),
            'date': ('DC', 'date'),
            'description': ('DC', 'description'),
            'rights': ('DC', 'rights'),
            'subject': ('DC', 'subject')
        }

        for field, (namespace, name) in metadata_fields.items():
            value = self.book.get_metadata(namespace, name)
            if value and value[0]:
                self.metadata[field] = value[0][0] if isinstance(value[0], tuple) else value[0]
            else:
                self.metadata[field] = "未知"

    def print_metadata(self):
        print("\n书籍元数据:")
        print("-" * 50)
        for key, value in self.metadata.items():
            print(f"{key.capitalize()}: {value}")

    def print_toc(self, toc=None, level=0):
        """改进的目录打印函数"""
        if toc is None:
            toc = self.book.toc
            print("\n目录结构:")
            print("-" * 50)
            if not toc:
                print("没有找到目录结构")
                return

        for item in toc:
            try:
                if isinstance(item, tuple):
                    # 安全获取标题
                    title = item[0] if len(item) > 0 else "未知标题"
                    # 安全获取子目录
                    children = item[2] if len(item) > 2 else []
                    print("  " * level + f"- {title}")
                    if children:
                        self.print_toc(children, level + 1)
                elif isinstance(item, list):
                    # 处理列表类型的目录项
                    self.print_toc(item, level)
                else:
                    # 处理其他类型的目录项
                    print("  " * level + f"- {str(item)}")
            except Exception as e:
                print(f"处理目录项时出错: {str(e)}")
                continue

    def get_chapter_content(self, chapter):
        try:
            soup = BeautifulSoup(chapter.get_content(), 'html.parser')
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            return h.handle(str(soup))
        except Exception as e:
            return f"解析章节内容时出错: {str(e)}"

    def print_chapters(self, max_preview_length=200):
        print("\n章节内容:")
        print("-" * 50)

        chapters_found = False
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters_found = True
                print(f"\n文档ID: {item.id}")
                content = self.get_chapter_content(item)
                preview = content[:max_preview_length]
                if len(content) > max_preview_length:
                    preview += "..."
                print(preview + "\n")
                print("-" * 50)

        if not chapters_found:
            print("没有找到章节内容")

    def analyze(self):
        if not self.load_book():
            return

        try:
            self.get_metadata()
            self.print_metadata()
            self.print_toc()
            self.print_chapters()
        except Exception as e:
            print(f"分析过程中出错: {str(e)}")

    def _clean_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        return re.sub(r'[\\/*?:"<>|]', '', filename)

    def _get_chapter_markdown(self, chapter) -> str:
        """将章节内容转换为Markdown格式"""
        try:
            # 解析HTML内容
            soup = BeautifulSoup(chapter.get_content(), 'html.parser')

            # 获取标题
            title = ""
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()

            # 转换为Markdown
            markdown = self.html2text.handle(str(soup))

            # 如果有标题，确保它在文档开头并使用一级标题格式
            if title and not markdown.startswith(f"# {title}"):
                markdown = f"# {title}\n\n{markdown}"

            return markdown
        except Exception as e:
            return f"转换章节内容时出错: {str(e)}"

    def _extract_images(self):
        """提取epub中的所有图片"""
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                # 获取图片ID和内容
                image_id = item.id
                image_content = item.content
                image_name = unquote(item.file_name.split('/')[-1])

                self.images[image_id] = {
                    'content': image_content,
                    'name': image_name,
                    'media_type': item.media_type
                }

    def _save_images(self, output_dir: str) -> dict:
        """
        保存图片到assets目录
        
        Returns:
            dict: 图片ID到文件路径的映射
        """
        assets_dir = os.path.join(output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)

        image_paths = {}
        for image_id, image_data in self.images.items():
            # 生成安全的文件名
            safe_name = self._clean_filename(image_data['name'])
            if not safe_name:
                safe_name = f"image_{image_id}{self._get_extension(image_data['media_type'])}"

            # 保存图片
            image_path = os.path.join(assets_dir, safe_name)
            with open(image_path, 'wb') as f:
                f.write(image_data['content'])

            # 存储相对路径
            image_paths[image_id] = os.path.join('assets', safe_name)

        return image_paths

    def _get_extension(self, media_type: str) -> str:
        """根据媒体类型获取文件扩展名"""
        extensions = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/svg+xml': '.svg'
        }
        return extensions.get(media_type, '.jpg')

    def _process_html_content(self, html_content: str, image_paths: dict) -> str:
        """处理HTML内容，替换图片引用"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 处理图片标签
        for img in soup.find_all('img'):
            src = img.get('src', '')

            # 提取图片ID
            image_id = src.split('/')[-1].split('.')[0]

            if image_id in image_paths:
                # 更新图片源为相对路径
                img['src'] = image_paths[image_id]

                # 添加alt文本
                if not img.get('alt'):
                    img['alt'] = f"Image {image_id}"

        return str(soup)

    def save_as_markdown(self, output_dir: str = None) -> None:
        """将epub内容保存为Markdown文件"""
        if not self.book:
            if not self.load_book():
                return

        # 获取元数据
        self.get_metadata()

        # 提取所有图片
        self._extract_images()

        # 获取书名作为默认目录名
        book_title = self.metadata.get('title', 'unknown_book')
        book_title = self._clean_filename(book_title)

        # 设置输出目录
        if not output_dir:
            output_dir = f"{book_title}_markdown"
        os.makedirs(output_dir, exist_ok=True)

        # 保存图片并获取路径映射
        image_paths = self._save_images(output_dir)

        # 创建README.md
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {book_title}\n\n")
            f.write("## 图书信息\n\n")
            for key, value in self.metadata.items():
                f.write(f"- **{key.capitalize()}**: {value}\n")
            f.write("\n## 目录\n\n")

        # 保存章节内容
        print("\n开始转换章节...")
        chapter_index = 1
        for item in tqdm(self.book.get_items()):
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # 处理HTML内容
                processed_html = self._process_html_content(item.get_content().decode('utf-8'), image_paths)

                # 转换为Markdown
                markdown_content = self.html2text.handle(processed_html)

                # 生成章节文件名
                chapter_filename = f"chapter_{chapter_index:03d}.md"
                chapter_path = os.path.join(output_dir, chapter_filename)

                # 保存章节内容
                with open(chapter_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                # 更新README.md
                with open(readme_path, "a", encoding="utf-8") as f:
                    title = markdown_content.split('\n', 1)[0].lstrip("#").strip()
                    if not title:
                        title = f"Chapter {chapter_index}"
                    f.write(f"- [{title}]({chapter_filename})\n")

                chapter_index += 1

        print(f"\n转换完成！")
        print(f"- 文件保存在: {output_dir}")
        print(f"- 总计转换 {chapter_index - 1} 个章节")
        print(f"- 总计处理 {len(image_paths)} 张图片")
        print(f"- 目录索引保存在: {readme_path}")

    def save_as_single_markdown(self, output_path: str = None) -> None:
        """将epub内容保存为单个Markdown文件"""
        if not self.book:
            if not self.load_book():
                return

        # 获取元数据
        self.get_metadata()

        # 提取所有图片
        self._extract_images()

        # 获取书名
        book_title = self.metadata.get('title', 'unknown_book')
        book_title = self._clean_filename(book_title)

        # 设置输出路径和资源目录
        if not output_path:
            output_path = f"{book_title}.md"
        output_dir = os.path.dirname(output_path) or '.'

        # 保存图片并获取路径映射
        image_paths = self._save_images(output_dir)

        print(f"\n开始转换为单个Markdown文件...")

        with open(output_path, "w", encoding="utf-8") as f:
            # 写入标题和元数据
            f.write(f"# {book_title}\n\n")
            f.write("## 图书信息\n\n")
            for key, value in self.metadata.items():
                f.write(f"- **{key.capitalize()}**: {value}\n")
            f.write("\n---\n\n")

            # 写入章节内容
            chapter_count = 0
            for item in tqdm(self.book.get_items()):
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 处理HTML内容
                    processed_html = self._process_html_content(item.get_content().decode('utf-8'), image_paths)

                    # 转换为Markdown
                    markdown_content = self.html2text.handle(processed_html)
                    f.write(f"\n{markdown_content}\n")
                    f.write("\n---\n\n")
                    chapter_count += 1

        print(f"\n转换完成！")
        print(f"- 文件保存为: {output_path}")
        print(f"- 总计转换 {chapter_count} 个章节")
        print(f"- 总计处理 {len(image_paths)} 张图片")

    def save_as_single_file_markdown(self, output_path: str = None) -> None:
        """
        将epub内容（包括图片）保存为单个独立的Markdown文件
        图片将使用base64编码直接嵌入到markdown中
        
        Args:
            output_path: 输出文件路径，默认为'书名_single.md'
        """
        if not self.book:
            if not self.load_book():
                return

        # 获取元数据
        self.get_metadata()

        # 提取所有图片
        self._extract_images()

        # 获取书名
        book_title = self.metadata.get('title', 'unknown_book')
        book_title = self._clean_filename(book_title)

        # 设置输出路径
        if not output_path:
            output_path = f"{book_title}_single.md"

        # 创建图片ID到base64数据的映射
        image_data = {}
        for image_id, img in self.images.items():
            # 转换为base64
            b64_data = base64.b64encode(img['content']).decode()
            # 创建data URL
            image_data[image_id] = f"data:{img['media_type']};base64,{b64_data}"

        print(f"\n开始转换为单个独立Markdown文件...")

        with open(output_path, "w", encoding="utf-8") as f:
            # 写入标题和元数据
            f.write(f"# {book_title}\n\n")
            f.write("## 图书信息\n\n")
            for key, value in self.metadata.items():
                f.write(f"- **{key.capitalize()}**: {value}\n")
            f.write("\n---\n\n")

            # 写入章节内容
            chapter_count = 0
            for item in tqdm(self.book.get_items()):
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 处理HTML内容，替换图片引用为base64数据
                    soup = BeautifulSoup(item.get_content().decode('utf-8'), 'html.parser')

                    # 处理图片标签
                    for img in soup.find_all('img'):
                        src = img.get('src', '')
                        # 提取图片ID
                        image_id = src.split('/')[-1].split('.')[0]

                        if image_id in image_data:
                            # 更新图片源为base64数据
                            img['src'] = image_data[image_id]

                            # 添加alt文本
                            if not img.get('alt'):
                                img['alt'] = f"Image {image_id}"

                    # 转换为Markdown
                    markdown_content = self.html2text.handle(str(soup))
                    f.write(f"\n{markdown_content}\n")
                    f.write("\n---\n\n")
                    chapter_count += 1

        print(f"\n转换完成！")
        print(f"- 文件保存为: {output_path}")
        print(f"- 总计转换 {chapter_count} 个章节")
        print(f"- 总计嵌入 {len(image_data)} 张图片")