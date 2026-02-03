import os
import json
import mimetypes
from pathlib import Path
import requests


def get_access_token():
    """
    获取访问凭证，优先级：
    1. assets/wechat_config.json 配置文件
    2. 环境变量（WECHAT_MP_APPID + WECHAT_MP_APPSECRET）
    3. 环境变量（WECHAT_MP_ACCESS_TOKEN）
    """
    appid = ""
    secret = ""
    
    # 1. 优先读取配置文件
    config_path = Path(__file__).parent.parent / "assets" / "wechat_config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            appid = config.get("appId", "").strip()
            secret = config.get("appSecret", "").strip()
        except Exception as e:
            print(f"Warning: Failed to read config file: {e}")
    
    # 2. 回退到环境变量
    if not appid or not secret:
        use_stable = os.getenv("WECHAT_MP_USE_STABLE_TOKEN", "").lower() in {"1", "true", "yes"}
        appid = os.getenv("WECHAT_MP_APPID", "")
        secret = os.getenv("WECHAT_MP_APPSECRET", "")
        
        # 如果环境变量也没有，尝试直接的 access_token
        if not (use_stable and appid and secret):
            token = os.getenv("WECHAT_MP_ACCESS_TOKEN", "")
            if token:
                return token
    
    # 3. 使用稳定凭证获取 access_token
    if appid and secret:
        url = "https://api.weixin.qq.com/cgi-bin/stable_token"
        payload = {"grant_type": "client_credential", "appid": appid, "secret": secret}
        r = requests.post(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, timeout=15).json()
        token = r.get("access_token", "")
        if token:
            return token
        else:
            msg = json.dumps(r, ensure_ascii=False)
            raise RuntimeError(f"稳定凭证获取失败: {msg}")
    
    # 4. 所有方式都失败
    raise RuntimeError("缺少访问凭证：请在助手设置中配置 AppID 和 AppSecret，或设置环境变量")


def convert_markdown_to_html(text):
    try:
        import markdown
        return markdown.markdown(text, extensions=["extra"])
    except Exception:
        return "<p>" + "</p><p>".join(line for line in text.splitlines()) + "</p>"


def load_content(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    data = p.read_text(encoding="utf-8")
    if p.suffix.lower() in [".md", ".markdown"]:
        return convert_markdown_to_html(data)
    return data


def upload_permanent_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=image"
    with open(image_path, "rb") as f:
        files = {"media": (Path(image_path).name, f, mimetypes.guess_type(image_path)[0] or "application/octet-stream")}
        r = requests.post(url, files=files, timeout=30).json()
    if r.get("errcode", 0) != 0 or "media_id" not in r:
        raise RuntimeError(json.dumps(r, ensure_ascii=False))
    return r["media_id"]


def upload_content_image(access_token, image_path):
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
    with open(image_path, "rb") as f:
        files = {"media": (Path(image_path).name, f, mimetypes.guess_type(image_path)[0] or "application/octet-stream")}
        r = requests.post(url, files=files, timeout=30).json()
    if r.get("errcode", 0) != 0 or "url" not in r:
        raise RuntimeError(json.dumps(r, ensure_ascii=False))
    return r["url"]


def search_and_download_cover_image(query, output_dir=None):
    import tempfile
    import re
    import hashlib
    
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir())
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_query = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')[:50]
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    output_path = output_dir / f"cover_{safe_query}_{query_hash}.jpg"
    
    image_sources = [
        {
            "name": "Pexels",
            "url": "https://api.pexels.com/v1/search",
            "headers": {"Authorization": "563492ad6f91700001000001c4b6c1e6e9f54e8e8b8e8e8e8e8e8e8e"},
            "params": {"query": query, "per_page": 1, "orientation": "landscape"},
            "extract": lambda r: r.get("photos", [{}])[0].get("src", {}).get("large")
        },
        {
            "name": "Lorem Picsum",
            "url": f"https://picsum.photos/1200/630?random={query_hash}",
            "headers": {},
            "params": {},
            "extract": lambda r: None
        }
    ]
    
    for source in image_sources:
        try:
            if source["name"] == "Lorem Picsum":
                image_url = source["url"]
            else:
                r = requests.get(
                    source["url"],
                    headers=source["headers"],
                    params=source["params"],
                    timeout=15
                ).json()
                image_url = source["extract"](r)
                
                if not image_url:
                    print(f"{source['name']} 未找到匹配图片，尝试下一个图片源...")
                    continue
            
            print(f"正在从 {source['name']} 下载图片...")
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            output_path.write_bytes(img_response.content)
            print(f"✓ 成功从 {source['name']} 下载图片")
            return str(output_path)
            
        except Exception as e:
            print(f"{source['name']} 图片获取失败: {str(e)}")
            continue
    
    raise RuntimeError("所有图片源均获取失败，请检查网络连接")


def extract_keywords_from_content(content_text, max_keywords=3, used_keywords=None):
    import re
    
    if used_keywords is None:
        used_keywords = set()
    
    text = re.sub(r'<[^>]+>', '', content_text)
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    
    title_match = re.search(r'^#\s+(.+?)$', content_text, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
        title = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', title)
    else:
        title = ""
    
    first_paragraph = ""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if len(paragraphs) > 1:
        first_paragraph = paragraphs[1]
    
    common_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '将', '可以', '能', '与', '为', '等', '更', '中', '及', '而', '对', '从', '让', '使', '通过', '如何', '什么', '怎么', '为什么',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'you', 'your', 'we', 'our', 'they', 'their', 'how', 'what', 'when', 'where', 'why', 'which'
    }
    
    words = text.split()
    word_freq = {}
    for word in words:
        word = word.strip().lower()
        if len(word) >= 2 and word not in common_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    if title:
        title_words = title.split()
        for word in title_words:
            word = word.strip().lower()
            if len(word) >= 2 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 5
    
    if first_paragraph:
        para_words = first_paragraph.split()
        for word in para_words:
            word = word.strip().lower()
            if len(word) >= 2 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 2
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:max_keywords * 3]]
    
    keyword_mapping = {
        'ai': 'artificial intelligence technology',
        '人工智能': 'artificial intelligence technology',
        '机器学习': 'machine learning neural network',
        '深度学习': 'deep learning neural network',
        '神经网络': 'neural network deep learning',
        '自然语言': 'natural language processing',
        '图像识别': 'image recognition computer vision',
        '自动驾驶': 'autonomous driving self-driving car',
        '智能助手': 'smart assistant virtual assistant',
        '职场': 'workplace professional office',
        '工作': 'work business professional',
        '效率': 'productivity efficiency workflow',
        '技术': 'technology innovation digital',
        '数据': 'data analytics visualization',
        '分析': 'analysis insights research',
        '远程': 'remote work telecommuting',
        '协作': 'collaboration teamwork cooperation',
        '学习': 'learning education training',
        '创新': 'innovation creativity breakthrough',
        '管理': 'management leadership strategy',
        '团队': 'team collaboration group',
        '项目': 'project planning execution',
        '产品': 'product development design',
        '设计': 'design creative interface',
        '开发': 'development programming coding',
        '营销': 'marketing advertising promotion',
        '创业': 'startup entrepreneurship business',
        '投资': 'investment finance capital',
        '自动化': 'automation workflow efficiency',
        '优化': 'optimization improvement performance',
        '未来': 'future innovation technology',
        '趋势': 'trend forecast prediction',
        '突破': 'breakthrough innovation achievement',
        '应用': 'application implementation usage',
        '系统': 'system platform infrastructure',
        '平台': 'platform ecosystem network',
        '服务': 'service customer support',
        '客户': 'customer client user',
        '用户': 'user experience interface',
        '体验': 'experience design interaction',
        '界面': 'interface design user experience',
        '流程': 'process workflow procedure',
        '方案': 'solution strategy approach',
        '策略': 'strategy planning tactics',
        '模型': 'model framework architecture',
        '算法': 'algorithm computation method',
        '云计算': 'cloud computing infrastructure',
        '大数据': 'big data analytics',
        '物联网': 'internet of things iot',
        '区块链': 'blockchain cryptocurrency',
        '安全': 'security privacy protection',
        '隐私': 'privacy security data protection',
        '网络': 'network connectivity internet',
        '移动': 'mobile smartphone app',
        '应用程序': 'application software app',
        '软件': 'software development programming',
        '硬件': 'hardware device technology',
        '设备': 'device hardware gadget',
        '智能': 'smart intelligent ai',
        '数字化': 'digital transformation technology',
        '转型': 'transformation change innovation',
        '增长': 'growth development expansion',
        '发展': 'development growth progress',
        '进步': 'progress advancement innovation',
        '变革': 'transformation change revolution',
        '革命': 'revolution transformation breakthrough',
        '医疗': 'healthcare medical medicine',
        '健康': 'health wellness fitness',
        '教育': 'education learning teaching',
        '交通': 'transportation traffic mobility',
        '能源': 'energy power sustainability',
        '环境': 'environment sustainability green',
        '可持续': 'sustainability green eco-friendly',
        '金融': 'finance banking investment',
        '电商': 'e-commerce online shopping',
        '零售': 'retail shopping commerce',
        '制造': 'manufacturing production industry',
        '工业': 'industry manufacturing production',
        '农业': 'agriculture farming food',
        '娱乐': 'entertainment media content',
        '媒体': 'media content communication',
        '社交': 'social media networking',
        '通信': 'communication networking connectivity',
        '5g': '5g network connectivity',
        '6g': '6g future network'
    }
    
    english_keywords = []
    for kw in keywords:
        if kw in used_keywords:
            continue
        
        if kw in keyword_mapping:
            mapped = keyword_mapping[kw]
            if mapped not in ' '.join(english_keywords):
                english_keywords.append(mapped)
                used_keywords.add(kw)
        elif re.match(r'^[a-zA-Z]+$', kw):
            if kw not in ' '.join(english_keywords):
                english_keywords.append(kw)
                used_keywords.add(kw)
        else:
            if kw not in used_keywords:
                english_keywords.append(kw)
                used_keywords.add(kw)
        
        if len(english_keywords) >= max_keywords:
            break
    
    result = ' '.join(english_keywords[:max_keywords]) if english_keywords else "abstract concept art"
    return result


def extract_section_keywords(section_text, max_keywords=3, used_keywords=None):
    import re
    
    if used_keywords is None:
        used_keywords = set()
    
    text = re.sub(r'<[^>]+>', '', section_text)
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    h2_title = lines[0] if lines else ""
    
    h2_title = re.sub(r'^\d+[\.\、]\s*', '', h2_title)
    
    section_content = ' '.join(lines[1:3]) if len(lines) > 1 else ""
    
    combined_text = h2_title + " " + section_content
    combined_text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', combined_text)
    
    common_words = {
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '将', '可以', '能', '与', '为', '等', '更', '中', '及', '而', '对', '从', '让', '使', '通过',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can'
    }
    
    words = combined_text.split()
    word_freq = {}
    for word in words:
        word = word.strip().lower()
        if len(word) >= 2 and word not in common_words and word not in used_keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    title_words = h2_title.split()
    for word in title_words:
        word = word.strip().lower()
        if len(word) >= 2 and word not in common_words and word not in used_keywords:
            word_freq[word] = word_freq.get(word, 0) + 3
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    top_words = [word for word, freq in sorted_words[:max_keywords * 2]]
    
    keyword_mapping = {
        'ai': 'artificial intelligence robot',
        '人工智能': 'artificial intelligence robot',
        '机器学习': 'machine learning algorithm',
        '深度学习': 'deep learning network',
        '神经网络': 'neural network brain',
        '自然语言': 'natural language text',
        '图像识别': 'image recognition vision',
        '自动驾驶': 'autonomous vehicle car',
        '智能助手': 'virtual assistant robot',
        '自动化': 'automation robot workflow',
        '创造力': 'creativity innovation art',
        '智能': 'smart technology device',
        '助手': 'assistant helper support',
        '效率': 'productivity efficiency time',
        '提升': 'improvement growth progress',
        '数据': 'data analytics chart',
        '驱动': 'driven powered engine',
        '决策': 'decision making strategy',
        '远程': 'remote distance online',
        '协作': 'collaboration teamwork meeting',
        '高效': 'efficient productive fast',
        '个性化': 'personalized custom tailored',
        '学习': 'learning education study',
        '成长': 'growth development progress',
        '职场': 'workplace office business',
        '工作': 'work business professional',
        '技术': 'technology innovation digital',
        '创新': 'innovation creativity breakthrough',
        '管理': 'management leadership organization',
        '团队': 'team group collaboration',
        '项目': 'project planning task',
        '产品': 'product design development',
        '设计': 'design creative interface',
        '开发': 'development programming code',
        '营销': 'marketing advertising campaign',
        '创业': 'startup entrepreneurship business',
        '投资': 'investment finance money',
        '分析': 'analysis research data',
        '沟通': 'communication discussion talk',
        '培训': 'training education workshop',
        '绩效': 'performance achievement result',
        '战略': 'strategy planning vision',
        '客户': 'customer client service',
        '服务': 'service support help',
        '质量': 'quality excellence standard',
        '流程': 'process workflow procedure',
        '会议': 'meeting conference discussion',
        '日程': 'schedule calendar planning',
        '邮件': 'email message communication',
        '文档': 'document file paper',
        '搜索': 'search find query',
        '回复': 'reply response answer',
        '洞察': 'insight discovery analysis',
        '预测': 'prediction forecast future',
        '风险': 'risk danger warning',
        '趋势': 'trend direction future',
        '语音': 'voice audio speech',
        '翻译': 'translation language international',
        '纪要': 'notes minutes record',
        '白板': 'whiteboard brainstorm meeting',
        '推荐': 'recommendation suggestion advice',
        '反馈': 'feedback review comment',
        '模拟': 'simulation virtual model',
        '练习': 'practice training exercise',
        '同理心': 'empathy understanding emotion',
        '适应': 'adaptation flexibility change',
        '释放': 'unleash release freedom',
        '优化': 'optimization improvement performance',
        '未来': 'future tomorrow innovation',
        '突破': 'breakthrough achievement milestone',
        '应用': 'application usage implementation',
        '系统': 'system platform infrastructure',
        '平台': 'platform ecosystem network',
        '用户': 'user interface experience',
        '体验': 'experience interaction design',
        '界面': 'interface design screen',
        '方案': 'solution approach method',
        '策略': 'strategy tactics plan',
        '模型': 'model framework structure',
        '算法': 'algorithm computation logic',
        '云计算': 'cloud computing server',
        '大数据': 'big data analytics',
        '物联网': 'iot device sensor',
        '区块链': 'blockchain crypto technology',
        '安全': 'security protection safety',
        '隐私': 'privacy confidential secure',
        '网络': 'network internet connectivity',
        '移动': 'mobile smartphone device',
        '应用程序': 'application app software',
        '软件': 'software program code',
        '硬件': 'hardware device equipment',
        '设备': 'device gadget equipment',
        '数字化': 'digital technology transformation',
        '转型': 'transformation change evolution',
        '增长': 'growth expansion development',
        '发展': 'development progress evolution',
        '进步': 'progress advancement innovation',
        '变革': 'transformation revolution change',
        '革命': 'revolution breakthrough transformation',
        '医疗': 'healthcare hospital medicine',
        '健康': 'health wellness fitness',
        '教育': 'education school learning',
        '交通': 'transportation vehicle traffic',
        '能源': 'energy power electricity',
        '环境': 'environment nature green',
        '可持续': 'sustainability eco green',
        '金融': 'finance banking money',
        '电商': 'ecommerce shopping online',
        '零售': 'retail store shopping',
        '制造': 'manufacturing factory production',
        '工业': 'industry factory manufacturing',
        '农业': 'agriculture farming crop',
        '娱乐': 'entertainment fun media',
        '媒体': 'media content news',
        '社交': 'social networking community',
        '通信': 'communication network signal',
        '5g': '5g network wireless',
        '6g': '6g future network'
    }
    
    english_keywords = []
    
    for word in top_words:
        if word in used_keywords:
            continue
        
        if word in keyword_mapping:
            mapped = keyword_mapping[word]
            if mapped not in ' '.join(english_keywords):
                english_keywords.append(mapped)
                used_keywords.add(word)
        elif re.match(r'^[a-zA-Z]+$', word):
            if word not in ' '.join(english_keywords):
                english_keywords.append(word)
                used_keywords.add(word)
        else:
            if word not in used_keywords:
                english_keywords.append(word)
                used_keywords.add(word)
        
        if len(english_keywords) >= max_keywords:
            break
    
    result = ' '.join(english_keywords) if english_keywords else "modern concept design"
    return result


def insert_images_into_content(access_token, content_html, base_dir, downloaded_images, 
                               used_keywords=None, material_dir=None, used_material_images=None):
    import re
    
    if used_keywords is None:
        used_keywords = set()
    if used_material_images is None:
        used_material_images = set()
    
    h2_pattern = re.compile(r'(<h2[^>]*>.*?</h2>)(.*?)(?=<h2|$)', re.DOTALL | re.IGNORECASE)
    sections = h2_pattern.findall(content_html)
    
    if not sections or len(sections) < 2:
        return content_html
    
    total_sections = len(sections)
    insert_positions = []
    
    if total_sections >= 5:
        insert_positions = [1, 3]
    elif total_sections >= 3:
        insert_positions = [1]
    
    result_html = content_html
    inserted_count = 0
    
    for idx in insert_positions:
        if idx >= len(sections):
            continue
        
        h2_tag, section_content = sections[idx]
        section_text = h2_tag + section_content
        
        try:
            if material_dir:
                print(f"正在为第 {idx+1} 个章节从素材库选择图片...")
                image_path = select_image_from_material_dir(material_dir, used_material_images)
                print(f"✓ 已选择素材库图片: {Path(image_path).name}")
            else:
                keywords = extract_section_keywords(section_text, max_keywords=2, used_keywords=used_keywords)
                if not keywords:
                    print(f"× 第 {idx+1} 个章节无法提取关键词，跳过")
                    continue
                
                print(f"正在为第 {idx+1} 个章节搜索图片，关键词: {keywords}")
                image_path = search_and_download_cover_image(keywords, base_dir)
                downloaded_images.append(image_path)
            
            wechat_url = upload_content_image(access_token, image_path)
            
            img_tag = f'<p style="text-align: center;"><img src="{wechat_url}" style="max-width: 100%; height: auto;" /></p>'
            
            insert_marker = h2_tag
            result_html = result_html.replace(insert_marker, insert_marker + img_tag, 1)
            inserted_count += 1
            print(f"✓ 已在第 {idx+1} 个章节插入图片")
        except Exception as e:
            print(f"× 第 {idx+1} 个章节图片插入失败: {str(e)}")
            continue
    
    print(f"共插入 {inserted_count} 张正文图片")
    return result_html


def replace_local_images_with_wechat_urls(access_token, content_html, base_dir):
    import re
    def repl(match):
        src = match.group(1).strip()
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            return match.group(0)
        local_path = Path(base_dir, src).resolve()
        if not local_path.exists():
            return match.group(0)
        url = upload_content_image(access_token, str(local_path))
        return match.group(0).replace(src, url)
    pattern = re.compile(r'<img[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
    return pattern.sub(repl, content_html)


def select_image_from_material_dir(material_dir, used_images=None):
    if used_images is None:
        used_images = set()
    
    material_path = Path(material_dir)
    if not material_path.exists() or not material_path.is_dir():
        raise ValueError(f"素材目录不存在或不是目录: {material_dir}")
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    available_images = [
        img for img in material_path.iterdir()
        if img.is_file() and img.suffix.lower() in image_extensions and str(img) not in used_images
    ]
    
    if not available_images:
        raise ValueError(f"素材目录中没有可用的图片（或所有图片已被使用）: {material_dir}")
    
    selected_image = available_images[0]
    used_images.add(str(selected_image))
    
    return str(selected_image)
