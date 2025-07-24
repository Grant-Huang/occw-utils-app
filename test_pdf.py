import PyPDF2
import os

def extract_pdf_text(pdf_path):
    """提取PDF文件内容"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n=== 第 {i+1} 页 ===\n"
                text += page_text
                text += "\n"
        return text
    except Exception as e:
        print(f"PDF解析失败: {e}")
        return ""

if __name__ == "__main__":
    pdf_path = "upload/sample.pdf"
    if os.path.exists(pdf_path):
        text = extract_pdf_text(pdf_path)
        print("PDF内容:")
        print(text)
        
        # 保存到文件以便查看
        with open("pdf_content.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("\nPDF内容已保存到 pdf_content.txt")
    else:
        print(f"PDF文件不存在: {pdf_path}") 