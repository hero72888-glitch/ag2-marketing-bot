import os
import logging
import logging
from autogen import ConversableAgent, UserProxyAgent
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# 取出儲存的 Gemini API Key
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if not gemini_api_key:
    logger.warning("WARNING: 找不到 GEMINI_API_KEY")

# 設定 AG2 (AutoGen) 使用 Google Gemini 模型
llm_config = {
    "config_list": [
        {
            "model": "gemini-2.5-flash", 
            "api_key": gemini_api_key,
            "api_type": "google"
        }
    ]
}

def load_knowledge():
    knowledge_file = 'knowledge.md'
    if os.path.exists(knowledge_file):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "目前無其他詳細資訊。"

def process_customer_message(message_text: str) -> str:
    """處理 LINE 傳來的客服訊息"""
    try:
        knowledge_text = load_knowledge()
        
        # 每次收到訊息時，建立全新的 Agent 實例，避免多人同時傳訊息時產生衝突 (Concurrency bug)
        cs_agent = ConversableAgent(
            name="CS_Agent",
            system_message=f"""你是「大熊老師與蘋果老師主持」的專屬客服小幫手。
你的老闆是「黃世豪 (大熊老師)」與蘋果老師，專門辦理抓周派對與活動主持。

【本公司服務核心資訊 - 從動態知識庫讀取】
{knowledge_text}

【回覆風格規則】
1. 用親切、熱情、活潑的語氣，像朋友聊天一樣自然。
2. 回覆要簡潔有重點，不要寫太長的文章。
3. 絕對禁止重複或複述客人說過的話！不要像鸚鵡一樣學客人講話。
4. 如果客人只是打招呼，就自然地打招呼回去，簡短有活力就好，不要長篇大論。
5. 如果客人問到需要報價、預約檔期、或是你無法確定的事，請根據知識庫回答有相關方案，然後結尾必定加上：「這部分的詳細內容與價格，我請大熊老師親自為您解答，請稍候喔！😊」
6. 可以適當使用 emoji 讓對話更有溫度，但不要過度使用。""",
            llm_config=llm_config,
        )

        user_proxy = UserProxyAgent(
            name="Boss_Proxy",
            system_message="人類老闆的代理人，負責最後審核或接手困難問題。",
            human_input_mode="NEVER",  
            max_consecutive_auto_reply=1,
            code_execution_config=False,  
        )

        # 讓 Boss Proxy (代表客人/系統) 傳送訊息給 CS Agent
        user_proxy.initiate_chat(
            cs_agent,
            message=message_text,
            max_turns=1,
            clear_history=True
        )
        
        # 取得最後回覆
        last_msg = user_proxy.last_message(cs_agent)
        if last_msg and "content" in last_msg:
            return last_msg["content"]
        return "抱歉，目前客服人員忙碌中，請稍後再試！"
    except Exception as e:
        logger.error(f"AG2 處理失敗: {e}", exc_info=True)
        return "系統遇到一點小亂流，請稍後再試！"

if __name__ == "__main__":
    # 簡單的本地測試
    print("測試客服大腦中...")
    reply = process_customer_message("請問抓周派對的收費大概是多少？")
    print(f"CS_Agent 回覆: {reply}")
