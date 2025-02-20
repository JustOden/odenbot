import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=("o!", "O!"), intents=intents)


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    try:
        synced = await bot.tree.sync()
    except Exception as e:
        print(e)
    else:
        print(f"Synced {len(synced)} slash command(s)")
    user_id = os.environ.get("USER_ID")
    user = await bot.fetch_user(user_id)
    await user.send("Online")


@bot.command()
async def info(ctx):
    await ctx.send("I am a bot designed by Oden and a work in progress. Do 'o!help' for list of commands and 'o!help <command_name>' for more instructions")


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load()
        TOKEN = os.getenv("DISCORD_TOKEN")
        await bot.start(TOKEN)

# keep_alive()
asyncio.run(main())
