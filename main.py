import os
import discord
from litellm import completion

SYSTEM_PROMPT = (
    "You are a cat. "
    "Your only allowed output is exactly the lowercase word meow. "
    "Never explain, analyze, or use extra words. "
    "Output exactly: meow"
)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    try:
        response = completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message.content}
            ],
            temperature=0,
            max_tokens=5
        )
        reply = response.choices[0].message.content or "meow"
        await message.channel.send(reply)
    except Exception:
        await message.channel.send("meow")

client.run(os.environ.get("DISCORD_CODE"))
