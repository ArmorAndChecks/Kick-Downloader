# kickapi/chat_data.py
class ChatMessage:
    def __init__(self, data):
        # Initialize chat message attributes
        self.id = data.get("id")
        self.text = data.get("content", "")
        self.sender = ChatSender(data.get("sender", {}))
        self.date = data.get("created_at", "")

class ChatSender:
    def __init__(self, data):
        # Initialize chat sender attributes
        self.username = data.get("username", "")
        self.user_id = data.get("id", "")

class ChatData:
    def __init__(self, data):
        # Initialize chat data attributes
        # Handle multiple possible response structures from Kick API
        messages_list = []
        if isinstance(data, dict):
            if "messages" in data:
                messages_list = data["messages"]
            elif "data" in data:
                if isinstance(data["data"], dict):
                    messages_list = data["data"].get("messages", [])
                elif isinstance(data["data"], list):
                    messages_list = data["data"]
        
        self.messages = [ChatMessage(m) for m in messages_list if isinstance(m, dict)]
