import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, User
import blackboxai
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - FILL THESE WITH YOUR OWN VALUES
API_ID = 'your_api_id'  # Get from https://my.telegram.org
API_HASH = 'your_api_hash'  # Get from https://my.telegram.org
PHONE_NUMBER = 'your_phone_number'  # Your phone number with country code
OPENAI_API_KEY = 'your_openai_api_key'  # Get from https://platform.openai.com

# Initialize clients
client = TelegramClient('session_name', API_ID, API_HASH)
openai.api_key = OPENAI_API_KEY

class TelegramAITagger:
    def __init__(self):
        self.is_ready = False
        self.current_chat = None
    
    async def initialize(self):
        """Initialize the Telegram client"""
        await client.start(phone=PHONE_NUMBER)
        self.is_ready = True
        logger.info("Client initialized successfully!")
    
    async def get_all_members(self, chat_entity):
        """Get all members from a chat"""
        try:
            participants = await client.get_participants(chat_entity)
            return participants
        except Exception as e:
            logger.error(f"Error getting members: {e}")
            return []
    
    async def tag_all_members(self, chat_entity, message="", delay=2):
        """Tag all members one by one with optional message"""
        members = await self.get_all_members(chat_entity)
        
        if not members:
            await client.send_message(chat_entity, "No members found or no permission to get members.")
            return
        
        tagged_count = 0
        for member in members:
            if not member.bot and not member.deleted:
                try:
                    # Create mention
                    if member.username:
                        mention = f"@{member.username}"
                    else:
                        mention = f"[{member.first_name or ''}](tg://user?id={member.id})"
                    
                    # Send message with mention
                    full_message = f"{mention} {message}".strip()
                    await client.send_message(chat_entity, full_message)
                    
                    tagged_count += 1
                    logger.info(f"Tagged: {member.first_name} (Total: {tagged_count})")
                    
                    # Delay between tags to avoid rate limiting
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Error tagging {member.first_name}: {e}")
                    continue
        
        await client.send_message(chat_entity, f"✅ Completed tagging {tagged_count} members!")
    
    async def chat_with_member_ai(self, chat_entity, member, message):
        """Chat with a specific member using AI"""
        try:
            # Get member info for context
            member_info = f"{member.first_name or ''} {member.last_name or ''}".strip()
            if member.username:
                member_info += f" (@{member.username})"
            
            # Prepare context for AI
            context = f"You are having a private conversation with {member_info}. Be friendly and helpful."
            
            # Generate AI response
            response = await self.generate_ai_response(message, context)
            
            # Send the response
            await client.send_message(chat_entity, response)
            
        except Exception as e:
            logger.error(f"Error in AI chat: {e}")
            await client.send_message(chat_entity, "Sorry, I encountered an error processing your message.")
    
    async def generate_ai_response(self, message, context=""):
        """Generate AI response using OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "I'm having trouble generating a response right now."
    
    async def list_chats(self):
        """List all available chats"""
        dialogs = await client.get_dialogs()
        chats = []
        
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                chats.append({
                    'id': dialog.id,
                    'name': dialog.name,
                    'type': 'Channel' if dialog.is_channel else 'Group',
                    'entity': dialog.entity
                })
        
        return chats

# Command handler
tagger = TelegramAITagger()

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command"""
    help_text = """
🤖 **Telegram AI Tagger Bot**

**Available Commands:**
`/tagall [message]` - Tag all members one by one
`/listchats` - List all your groups and channels
`/setchat` - Set current chat for operations
`/ai [message]` - Chat with AI in current chat

**Examples:**
`/tagall Hello everyone!`
`/ai How are you doing?`
"""
    await event.reply(help_text)

@client.on(events.NewMessage(pattern='/listchats'))
async def list_chats_handler(event):
    """Handle /listchats command"""
    chats = await tagger.list_chats()
    
    if not chats:
        await event.reply("No groups or channels found.")
        return
    
    response = "📋 **Your Groups & Channels:**\n\n"
    for i, chat in enumerate(chats, 1):
        response += f"{i}. **{chat['name']}** ({chat['type']})\n"
    
    await event.reply(response)

@client.on(events.NewMessage(pattern='/setchat'))
async def set_chat_handler(event):
    """Set current chat for operations"""
    tagger.current_chat = await event.get_chat()
    chat_title = getattr(tagger.current_chat, 'title', 'Private Chat')
    await event.reply(f"✅ Current chat set to: **{chat_title}**")

@client.on(events.NewMessage(pattern='/tagall'))
async def tag_all_handler(event):
    """Handle /tagall command"""
    if not tagger.current_chat:
        await event.reply("❌ Please set a chat first using /setchat")
        return
    
    # Extract message after command
    message_text = event.raw_text.replace('/tagall', '').strip()
    
    await event.reply(f"🚀 Starting to tag all members... (Message: {message_text or 'No additional message'})")
    await tagger.tag_all_members(tagger.current_chat, message_text)

@client.on(events.NewMessage(pattern='/ai'))
async def ai_chat_handler(event):
    """Handle /ai command"""
    if not tagger.current_chat:
        await event.reply("❌ Please set a chat first using /setchat")
        return
    
    message_text = event.raw_text.replace('/ai', '').strip()
    if not message_text:
        await event.reply("❌ Please provide a message for AI")
        return
    
    # Get the sender info
    sender = await event.get_sender()
    await tagger.chat_with_member_ai(tagger.current_chat, sender, message_text)

async def main():
    """Main function"""
    await tagger.initialize()
    logger.info("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
