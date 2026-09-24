🚀 使用指南
1. 开启浏览器调试模式
在运行脚本前，必须先以调试模式启动浏览器。请彻底关闭所有正在运行的 Edge/Chrome 进程，然后通过终端或快捷方式运行以下命令：

Edge 浏览器 (Windows):
DOS
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\edge_debug_profile"


Chrome 浏览器 (Windows):
DOS
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_profile"
注：--user-data-dir 路径可自定义，用于保存隔离的浏览器缓存。

2. 登录番茄后台
在刚才打开的调试浏览器中，手动访问 番茄小说作家专区 并完成登录。
进入你要更新的作品的 “章节管理” 页面，并保持该页面打开。

3. 配置并运行脚本
在代码的 main 函数中修改你的 Word 文档路径：

Python
if __name__ == "__main__":
    # 替换为你自己的 Word 文档路径
    word_file_path = r"D:\MyNovel\FirstVolume.docx" 
    novel_chapters = parse_word_document(word_file_path)
    
    if novel_chapters:
        auto_upload_to_fanqiao(novel_chapters)
在终端中执行脚本：

Bash
python upload.py
脚本将自动建立连接，逐章解析文档并完成上传与发布流程。

⚠️ 免责声明 (Disclaimer)
本项目仅供 Python 自动化技术学习与交流使用。自动化脚本的高频请求可能会触发平台风控机制，使用者应自行承担因过度依赖或违规操作导致账号受限等相关风险。请合理控制发布频率，尊重平台规则。
