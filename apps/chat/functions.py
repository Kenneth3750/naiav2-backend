import tiktoken


def num_tokens_from_messages(messages):
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // 4



def num_tokens_from_messages_big(messages, model="gpt-4o-mini-2024-07-18"):
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using o200k_base encoding.")
        encoding = tiktoken.get_encoding("o200k_base")
    if model in {
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06"
        }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif "gpt-3.5-turbo" in model:
        print("Warning: using approximate token count for gpt-3.5-turbo")
        return num_tokens_from_messages_big(messages, model="gpt-3.5-turbo-0125")
    elif "gpt-4o-mini" in model:
        print("Warning: using approximate token count for gpt-4o-mini")
        return num_tokens_from_messages_big(messages, model="gpt-4o-mini-2024-07-18")
    elif "gpt-4o" in model:
        print("Warning: using approximate token count for gpt-4o")
        return num_tokens_from_messages_big(messages, model="gpt-4o-2024-08-06")
    elif "gpt-4" in model:
        print("Warning: using approximate token count for gpt-4")
        return num_tokens_from_messages_big(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            if isinstance(value, str):
                num_tokens += len(encoding.encode(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and "text" in item:
                        num_tokens += len(encoding.encode(item["text"]))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens



def get_last_four_messages(messages):
    if messages:
        # Take last 4 messages and filter out tool calls and messages without content
        last_four_messages = messages[-4:]
        valid_messages = []
        
        for msg in last_four_messages:
            # Skip tool calls and messages without content
            if msg.get("role") == "tool" or msg.get("content") is None:
                continue
            
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content:
                message_text = ""
                
                # Handle different content formats
                if isinstance(content, list):
                    # Handle OpenAI format with [{'type': 'text', 'text': '...'}]
                    texts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            texts.append(item.get("text", ""))
                    if texts:
                        message_text = " ".join(texts)
                elif role == "assistant":
                    try:
                        # Parse JSON if it's a string (NAIA format)
                        parsed_content = json.loads(content) if isinstance(content, str) else content
                        # If it's a list of NAIA JSON objects, extract text
                        if isinstance(parsed_content, list):
                            texts = [item.get("text", "") for item in parsed_content if isinstance(item, dict) and "text" in item]
                            if texts:
                                message_text = " ".join(texts)
                        else:
                            message_text = str(content)
                    except (json.JSONDecodeError, TypeError):
                        # If not JSON, use as is
                        message_text = str(content)
                else:
                    # For other messages, convert to string safely
                    message_text = str(content)
                
                # Add role prefix and append to valid messages
                if message_text.strip():
                    if role == "user":
                        valid_messages.append(f"User: {message_text}")
                    elif role == "assistant":
                        valid_messages.append(f"Assistant: {message_text}")
                    elif role == "developer":
                        valid_messages.append(f"System: {message_text}")
                    else:
                        valid_messages.append(f"{role.capitalize()}: {message_text}")
        
        last_messages_text = " ".join(valid_messages) if valid_messages else "No previous messages found."
    else:
        last_messages_text = "No previous messages found."

    print(f"Last messages text: {last_messages_text}")
    return last_messages_text