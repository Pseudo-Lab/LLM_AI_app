




class MemoryStorage:
    def __init__(self):
        self.chat_history = ["<CHAT_HISTORY_START>"]

    def human_message_save(self, message: str):
        self.chat_history.append("Human: " + message)

    def ai_message_save(self, message: str):
        self.chat_history.append("AI: " + message)

    def get_chat_history(self, user_input: str):
        return "\n".join(self.chat_history[:-1]) + "<CHAT_HISTORY_END>\nHuman: " + user_input
