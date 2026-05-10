import requests

def send_ntfy_message(
    topic, 
    message, 
    title=None, 
    priority="default", 
    tags=None, 
    click_url=None, 
    attach_url=None, 
    filename=None,
):
    """
    Sends a message to a ntfy topic.
    
    Args:
        topic (str): The ntfy topic name.
        message (str): The body of the notification.
        title (str, optional): The headline of the notification.
        priority (str, optional): Priority levels: 'max', 'high', 'default', 'low', 'min'.
        tags (list, optional): List of strings (emojis or tags) to include.
        click_url (str, optional): URL to open when the notification is clicked.
        attach_url (str, optional): URL of an image or file to attach.
        filename (str, optional): Name for the attachment.
    """
    
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": ",".join(tags) if tags else None,
        "Click": click_url,
        "Attach": attach_url,
        "Filename": filename,
    }
    
    # Remove None values from headers
    headers = {k: v for k, v in headers.items() if v is not None}
    
    try:
        response = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")
        return None
