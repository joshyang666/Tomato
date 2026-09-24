import docx
import re
import time
import pyperclip
from playwright.sync_api import sync_playwright

# ================= 1. 读取并拆分 Word 文档 =================
def parse_word_document(file_path):
    print(f"正在读取文件: {file_path}")
    doc = docx.Document(file_path)
    chapters = []
    current_title = ""
    current_content = []
    
    # 匹配“第X章”、“第X节”等标题的正则表达式
    pattern = re.compile(r'^第[零一二三四五六七八九十百千万\d]+[章节]')
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue
        
        if pattern.match(text): # 如果匹配到新章节标题
            if current_title:
                chapters.append({
                    "title": current_title, 
                    "content": "\n".join(current_content)
                })
            current_title = text
            current_content = [] # 清空正文缓存，准备读取下一章
        else:
            current_content.append(text)
            
    # 把最后一章加进去
    if current_title:
        chapters.append({"title": current_title, "content": "\n".join(current_content)})
    
    print(f"解析完成，共发现 {len(chapters)} 章。")
    return chapters


# ================= 2. Playwright 自动化上传逻辑 =================
def auto_upload_to_fanqiao(chapters):
    # 启动 Playwright
    with sync_playwright() as p:
        try:
            # 连接到刚才通过调试模式打开的 Chrome 浏览器 (端口 9222)
            print("正在连接浏览器，请确保你已经通过命令打开了Chrome，并在番茄后台页面...")
            # 将原来的 http://localhost:9222 修改为：
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")  
            
            # 获取当前打开的页面（我们假设你当前停留的标签页就是番茄后台）
            contexts = browser.contexts
            if not contexts:
                print("未找到浏览器上下文，请检查浏览器是否正常打开。")
                return
            page = contexts[0].pages[0]
            
            # 确保页面加载完成
            page.bring_to_front()
            print(f"成功接管页面: {page.title()}")

            

            # 开始循环上传每一章
            for index, chapter in enumerate(chapters):
                raw_title = chapter['title']
                content = chapter['content']
                print(f"正在处理第 {index+1}/{len(chapters)} 章: {raw_title}")

                # ================= 新增：拆分章节号与章节名 =================
                # 用正则提取“第X章”里面的数字/汉字，以及后面的实际标题内容
                match = re.search(r'^第([零一二三四五六七八九十百千万\d]+)[章节]\s*(.*)', raw_title)
                if match:
                    chapter_num = match.group(1) # 提取出：4
                    chapter_name = match.group(2) # 提取出：天外废铁
                else:
                    # 如果匹配失败（格式不规范），就默认没有序号，全填进标题框
                    chapter_num = str(index + 1)
                    chapter_name = raw_title
                # ============================================================

                # 1. 监听并点击“新建章节”，接管弹出的新标签页
                with browser.contexts[0].expect_page() as new_page_info:
                    page.locator("text='新建章节'").first.click()
                
                editor_page = new_page_info.value
                editor_page.wait_for_load_state() 
                print("  -> 成功进入新建章节页面")

                # 2. 填写“章节序号” (根据你最新截图定位)
                num_input = editor_page.locator("span.left-input input")
                num_input.fill(chapter_num)
                editor_page.wait_for_timeout(500)

                # 3. 填写“章节标题” (根据之前的占位符定位)
                title_input = editor_page.locator("input[placeholder='请输入标题']")
                title_input.fill(chapter_name)
                editor_page.wait_for_timeout(500)

                # 4. 填写小说正文
                content_editor = editor_page.locator(".syl-editor-container")
                content_editor.click()
                editor_page.wait_for_timeout(300)
                
                # 复制并粘贴正文
                pyperclip.copy(content)
                editor_page.keyboard.press("Control+V")
                print(f"  -> 正文粘贴完成，字数: {len(content)}")
                editor_page.wait_for_timeout(1500) 

                # 5. 点击右上角的“下一步”按钮
                editor_page.locator("text='下一步'").first.click()
                
                # ================= 防线 1：处理错别字弹窗 =================
                print("  -> 正在检测是否有错别字拦截...")
                try:
                    submit_btn = editor_page.locator("button", has_text="提交").first
                    submit_btn.wait_for(state="visible", timeout=4000)
                    print("  -> 触发错别字警告，自动点击【提交】放行...")
                    submit_btn.click()
                    editor_page.wait_for_timeout(1500) # 等待下一个弹窗渲染
                except Exception:
                    pass # 如果没出现，直接忽略

                # ================= 防线 2：处理“内容检测方式”弹窗 =================
                print("  -> 正在检测是否有内容检测弹窗...")
                try:
                    # 精准锁定你截图里的右上角 X 按钮
                    close_btn = editor_page.locator("span.arco-modal-close-icon").first
                    # 最多等 3 秒看它出不出来
                    close_btn.wait_for(state="visible", timeout=3000)
                    print("  -> 发现内容检测弹窗，自动点击【X】关闭...")
                    close_btn.click()
                    editor_page.wait_for_timeout(1500) # 等待关闭动画结束，发布弹窗露面
                except Exception:
                    pass # 如果没出现，直接忽略
                # ============================================================

                # 5. 点击右上角的“下一步”按钮
                editor_page.locator("text='下一步'").first.click()
                
                # ================= 拦截 1：错别字弹窗检测 =================
                print("  -> 正在检测是否有错别字拦截...")
                try:
                    submit_btn = editor_page.locator("button", has_text="提交").first
                    submit_btn.wait_for(state="visible", timeout=4000)
                    print("  -> 触发错别字警告，自动点击【提交】放行...")
                    submit_btn.click()
                    editor_page.wait_for_timeout(1000) # 给下一个可能的弹窗留出渲染时间
                except Exception:
                    print("  -> 无错别字拦截。")
                    pass

                # ================= 拦截 2：内容检测方式弹窗检测 =================
                print("  -> 正在检测是否需要选择内容检测方式...")
                try:
                    # 锁定截图中的“仅基础检测”按钮
                    basic_check_btn = editor_page.locator("button", has_text="仅基础检测").first
                    basic_check_btn.wait_for(state="visible", timeout=4000)
                    print("  -> 触发内容检测选择，自动点击【仅基础检测】...")
                    basic_check_btn.click()
                    editor_page.wait_for_timeout(1000) # 给最终的发布设置弹窗留出渲染时间
                except Exception:
                    print("  -> 无内容检测选择弹窗。")
                    pass
                # ============================================================

                # 6. 在最终的“发布设置”弹窗中勾选“是否使用AI”
                # 多等 1 秒确保之前的遮罩层完全消失，最终弹窗稳定
                editor_page.wait_for_timeout(1000) 
                
                # 勾选 AI 声明（如果你想选否，把 "是" 改成 "否" 即可）
                editor_page.locator("label.arco-radio", has_text="是").click()
                editor_page.wait_for_timeout(500)

                # 7. 点击“确认发布”
                editor_page.locator("button", has_text="确认发布").click()
                print(f"  -> 🎉 【第{chapter_num}章 {chapter_name}】 已成功发布！")
                
                # 等待 3 秒让发布请求发送完成
                editor_page.wait_for_timeout(3000) 

                # 8. 关闭当前编辑页面，准备下一章
                editor_page.close()
                page.bring_to_front()
                page.wait_for_timeout(2000)
                
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            print("全部章节处理完毕，断开浏览器连接。")
            browser.close()

# ================= 3. 执行主程序 =================
if __name__ == "__main__":
    # 替换为你自己的 Word 文档路径
    word_file_path = r"C:\Users\EMC\Desktop\番茄小说\小说.docx" 
    
    # 获取拆分好的章节
    novel_chapters = parse_word_document(word_file_path)
    
    if novel_chapters:
        # 执行上传
        auto_upload_to_fanqiao(novel_chapters)