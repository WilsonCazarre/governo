import os

import discord
from dotenv import load_dotenv


load_dotenv()


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Cheers Love, the {self.user} is here!")


client = MyClient()
client.run(os.getenv('TOKEN'))
