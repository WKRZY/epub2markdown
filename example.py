from src.epub_reader import EpubReader


def main():
    try:
        # 使用示例
        epub_path = r".\从ChatGPT到AIGC：智能创作与应用赋能.epub"
        reader = EpubReader(epub_path)

        # 分析epub内容
        reader.analyze()

        # 转换为单个Markdown文件（包含图片）
        reader.save_as_single_file_markdown()

        # 转换为多个Markdown文件
        reader.save_as_markdown()

    except Exception as e:
        print(f"Error processing epub file: {str(e)}")


if __name__ == "__main__":
    main()
