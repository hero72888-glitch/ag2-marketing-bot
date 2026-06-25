import os
import autogen
from dotenv import load_dotenv

load_dotenv()

# 取出剛剛儲存的 Gemini API Key
gemini_api_key = os.environ.get("GEMINI_API_KEY")

if not gemini_api_key:
    print("WARNING: 找不到 GEMINI_API_KEY")

# 設定 AG2 (AutoGen) 使用 Google Gemini 模型
llm_config = {
    "config_list": [
        {
            "api_type": "google", 
            "model": "gemini-1.5-pro", 
            "api_key": gemini_api_key
        }
    ]
}

# 1. 建立客服專員 Agent (負責回答客人問題)
cs_agent = autogen.AssistantAgent(
    name="CS_Agent",
    system_message="""你是一位專業的客服小幫手。
你的老闆是「黃世豪 (大熊老師)」。
你們的業務是「大熊老師與蘋果老師主持」，專門辦理抓周派對與活動主持。
請用親切、熱情、活潑的語氣回答客人的問題。
如果客人問到具體的價格或是無法決定的事，請回答：「這部分我請大熊老師親自為您解答，請稍候喔！」""",
    llm_config=llm_config,
)

# 2. 建立行銷企劃 Agent (負責寫廣告)
marketing_agent = autogen.AssistantAgent(
    name="Marketing_Agent",
    system_message="你是專業的行銷企劃，負責構思活動促銷貼文與自動推播廣告，語氣要吸引人、有活力。",
    llm_config=llm_config,
)

# 3. 建立人類老闆代理人 (代表世豪)
user_proxy = autogen.UserProxyAgent(
    name="Boss_Proxy",
    system_message="人類老闆的代理人，負責最後審核或接手困難問題。",
    human_input_mode="NEVER",  # 雲端 24 小時運作時，設定為不等待終端機輸入
    max_consecutive_auto_reply=1,
)

def process_customer_message(message_text: str) -> str:
    """處理 LINE 傳來的客服訊息"""
    try:
        # 讓 Boss Proxy (代表客人/系統) 傳送訊息給 CS Agent
        user_proxy.initiate_chat(
            cs_agent,
            message=message_text,
            max_turns=1
        )
        
        # 取得 CS Agent 的最後一次回覆
        last_msg = user_proxy.last_message()
        if last_msg and "content" in last_msg:
            return last_msg["content"]
        return "抱歉，目前客服人員忙碌中，請稍後再試！"
    except Exception as e:
        print(f"Error processing message: {e}")
        return "系統遇到一點小亂流，請稍後再試！"

if __name__ == "__main__":
    # 簡單的本地測試
    print("測試客服大腦中...")
    reply = process_customer_message("請問抓周派對的收費大概是多少？")
    print(f"CS_Agent 回覆: {reply}")
