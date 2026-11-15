import re
from ..base import MemoryProviderBase, logger
import time
import json
import os
import yaml
from config.config_loader import get_project_dir
from config.manage_api_client import generate_and_save_chat_summary
import asyncio
from core.utils.util import check_model_key

# [patch vn-memory] Khi chạy cùng trang quản lý: server tự tóm tắt bộ nhớ bằng LLM của agent
# (key riêng + key dự phòng), prompt tiếng Việt, rồi ghi vào ai_agent.summary_memory.
VN_MEMORY_PROMPT = """Bạn là bộ nhớ dài hạn của một robot trò chuyện. Từ đoạn hội thoại mới và BỘ NHỚ CŨ,
hãy viết lại BỘ NHỚ MỚI về người dùng (những người nói chuyện với robot), bằng tiếng Việt.

Ghi nhớ (nếu có trong hội thoại):
- Tên, biệt danh, cách xưng hô mong muốn; ngày/tháng/năm sinh, tuổi; nơi sống, công việc, trường lớp
- Người thân, bạn bè, thú cưng (tên + quan hệ); ngày quan trọng (sinh nhật người thân, kỷ niệm…)
- Sở thích, món ăn, bài hát, môn học, điều không thích; mục tiêu, kế hoạch, lời hứa, việc cần nhắc
- Sự kiện đáng nhớ kèm NGÀY CỤ THỂ (đổi "hôm nay/mai/hôm qua" thành ngày tháng năm dựa trên THỜI GIAN HIỆN TẠI)
- Nếu có nhiều người khác nhau nói chuyện (ví dụ "[Người nói: Huy] ..."), ghi riêng thông tin cho từng người

Quy tắc:
- Giữ lại toàn bộ thông tin cũ còn đúng; thông tin mới mâu thuẫn thì cập nhật (ghi "trước đây: …" nếu hữu ích)
- KHÔNG ghi: lệnh điều khiển thiết bị/robot, âm lượng, phát nhạc, thời tiết, giờ hiện tại, câu chào hỏi vô nghĩa
- Không bịa, chỉ ghi điều người dùng thật sự nói
- Trình bày gạch đầu dòng ngắn gọn, nhóm theo từng người, tối đa khoảng 1500 ký tự
- Chỉ trả về nội dung bộ nhớ, không giải thích. Nếu không có gì mới, trả về nguyên BỘ NHỚ CŨ."""


def _save_summary_to_db(device_mac, summary):
    """[patch vn-memory] Ghi bộ nhớ vào agent đang gắn với thiết bị (cột ai_agent.summary_memory)."""
    import pymysql
    conn = pymysql.connect(host=os.environ.get("XZ_DB_HOST", "xiaozhi-esp32-server-db"),
                           port=int(os.environ.get("XZ_DB_PORT", "3306")),
                           user=os.environ.get("XZ_DB_USER", "root"),
                           password=os.environ.get("XZ_DB_PASSWORD", "123456"),
                           database=os.environ.get("XZ_DB_NAME", "xiaozhi_esp32_server"),
                           charset="utf8mb4", connect_timeout=5)
    try:
        with conn.cursor() as cur:
            n = cur.execute(
                "UPDATE ai_agent a JOIN ai_device d ON d.agent_id = a.id "
                "SET a.summary_memory = %s WHERE d.mac_address = %s",
                (summary, device_mac))
        conn.commit()
        return n
    finally:
        conn.close()


short_term_memory_prompt = """
# 时空记忆编织者

## 核心使命
构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹
根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务

## 记忆法则
### 1. 三维度记忆评估（每次更新必执行）
| 维度       | 评估标准                  | 权重分 |
|------------|---------------------------|--------|
| 时效性     | 信息新鲜度（按对话轮次） | 40%    |
| 情感强度   | 含💖标记/重复提及次数     | 35%    |
| 关联密度   | 与其他信息的连接数量      | 25%    |

### 2. 动态更新机制
**名字变更处理示例：**
原始记忆："曾用名": ["张三"], "现用名": "张三丰"
触发条件：当检测到「我叫X」「称呼我Y」等命名信号时
操作流程：
1. 将旧名移入"曾用名"列表
2. 记录命名时间轴："2024-02-15 14:32:启用张三丰"
3. 在记忆立方追加：「从张三到张三丰的身份蜕变」

### 3. 空间优化策略
- **信息压缩术**：用符号体系提升密度
  - ✅"张三丰[北/软工/🐱]"
  - ❌"北京软件工程师，养猫"
- **淘汰预警**：当总字数≥900时触发
  1. 删除权重分<60且3轮未提及的信息
  2. 合并相似条目（保留时间戳最近的）

## 记忆结构
输出格式必须为可解析的json字符串，不需要解释、注释和说明，保存记忆时仅从对话提取信息，不要混入示例内容
```json
{
  "时空档案": {
    "身份图谱": {
      "现用名": "",
      "特征标记": [] 
    },
    "记忆立方": [
      {
        "事件": "入职新公司",
        "时间戳": "2024-03-20",
        "情感值": 0.9,
        "关联项": ["下午茶"],
        "保鲜期": 30 
      }
    ]
  },
  "关系网络": {
    "高频话题": {"职场": 12},
    "暗线联系": [""]
  },
  "待响应": {
    "紧急事项": ["需立即处理的任务"], 
    "潜在关怀": ["可主动提供的帮助"]
  },
  "高光语录": [
    "最打动人心的瞬间，强烈的情感表达，user的原话"
  ]
}
```
"""


def extract_json_data(json_code):
    start = json_code.find("```json")
    # 从start开始找到下一个```结束
    end = json_code.find("```", start + 1)
    # print("start:", start, "end:", end)
    if start == -1 or end == -1:
        try:
            jsonData = json.loads(json_code)
            return json_code
        except Exception as e:
            print("Error:", e)
        return ""
    jsonData = json_code[start + 7 : end]
    return jsonData


TAG = __name__


class MemoryProvider(MemoryProviderBase):
    def __init__(self, config, summary_memory):
        super().__init__(config)
        self.short_memory = ""
        self.save_to_file = True
        self.memory_path = get_project_dir() + "data/.memory.yaml"
        self.load_memory(summary_memory)

    def init_memory(
        self, role_id, llm, summary_memory=None, save_to_file=True, **kwargs
    ):
        super().init_memory(role_id, llm, **kwargs)
        self.save_to_file = save_to_file
        self.load_memory(summary_memory)

    def load_memory(self, summary_memory):
        # api获取到总结记忆后直接返回
        if summary_memory or not self.save_to_file:
            self.short_memory = summary_memory
            return

        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        if self.role_id in all_memory:
            self.short_memory = all_memory[self.role_id]

    def save_memory_to_file(self):
        all_memory = {}
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                all_memory = yaml.safe_load(f) or {}
        all_memory[self.role_id] = self.short_memory
        with open(self.memory_path, "w", encoding="utf-8") as f:
            yaml.dump(all_memory, f, allow_unicode=True)

    async def save_memory(self, msgs, session_id=None):
        # 打印使用的模型信息
        model_info = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
        logger.bind(tag=TAG).debug(f"使用记忆保存模型: {model_info}")
        api_key = getattr(self.llm, "api_key", None)
        memory_key_msg = check_model_key("记忆总结专用LLM", api_key)
        if memory_key_msg:
            logger.bind(tag=TAG).error(memory_key_msg)
        if self.llm is None:
            logger.bind(tag=TAG).error("LLM is not set for memory provider")
            return None

        if len(msgs) < 2:
            return None

        msgStr = ""
        for msg in msgs:
            content = msg.content

            # Extract content from JSON format if present (for ASR with emotion/language tags)
            try:
                if content and content.strip().startswith("{") and content.strip().endswith("}"):
                    data = json.loads(content)
                    if "content" in data:
                        # [patch vn-memory] giữ tên người nói (nhận diện giọng) để bộ nhớ tách theo từng người
                        spk = str(data.get("speaker") or "").strip()
                        content = (f"[Người nói: {spk}] " if spk and spk != "未知说话人" else "") + str(data["content"])
            except (json.JSONDecodeError, KeyError, TypeError):
                # If parsing fails, use original content
                pass

            if msg.role == "user":
                msgStr += f"User: {content}\n"
            elif msg.role == "assistant":
                msgStr += f"Assistant: {content}\n"
        if self.short_memory and len(self.short_memory) > 0:
            msgStr += "历史记忆：\n"
            msgStr += self.short_memory

        # 当前时间
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msgStr += f"当前时间：{time_str}"

        if self.save_to_file:
            try:
                result = self.llm.response_no_stream(
                    short_term_memory_prompt,
                    msgStr,
                    max_tokens=2000,
                    temperature=0.2,
                )
                json_str = extract_json_data(result)
                json.loads(json_str)  # 检查json格式是否正确
                self.short_memory = json_str
                self.save_memory_to_file()
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error in saving memory: {e}")
        else:
            # [patch vn-memory] thay cho Java (prompt tiếng Trung + key chung): tự tóm tắt bằng LLM của agent
            try:
                convo = msgStr.split("历史记忆：")[0].split("当前时间：")[0].replace("User:", "Người dùng:").replace("Assistant:", "Robot:")
                user_prompt = (f"BỘ NHỚ CŨ:\n{self.short_memory or '(trống)'}\n\n"
                               f"THỜI GIAN HIỆN TẠI: {time_str}\n\nHỘI THOẠI MỚI:\n{convo}")
                result = (self.llm.response_no_stream(VN_MEMORY_PROMPT, user_prompt) or "").strip()
                # bỏ nhãn prompt nếu Gemini chép lại ("BỘ NHỚ CŨ:", "BỘ NHỚ MỚI:") và giá trị "(trống)"
                result = re.sub(r"^\s*(BỘ NHỚ (CŨ|MỚI)|THỜI GIAN HIỆN TẠI|HỘI THOẠI MỚI)\s*:\s*", "", result,
                                flags=re.IGNORECASE | re.MULTILINE).strip()
                if result.strip("() \n").lower() in ("trống", "", "không có", "none"):
                    logger.bind(tag=TAG).info("Không có gì mới để ghi nhớ")
                    return
                if result and "LLM" not in result[:20]:
                    rows = _save_summary_to_db(self.role_id, result[:3000])
                    self.short_memory = result
                    logger.bind(tag=TAG).info(f"Đã cập nhật bộ nhớ ({len(result)} ký tự, {rows} agent): {result[:120]}…")
            except Exception as e:
                logger.bind(tag=TAG).error(f"Lưu bộ nhớ (tiếng Việt) thất bại: {e}")
        logger.bind(tag=TAG).info(
            f"Save memory successful - Role: {self.role_id}, Session: {session_id}"
        )

        return self.short_memory

    async def query_memory(self, query: str) -> str:
        return self.short_memory
