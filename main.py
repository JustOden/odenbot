import os
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="o!", intents=intents)


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


@bot.tree.command()
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey {interaction.user.mention}! This is a slash command!", ephemeral=True)


@bot.tree.command()
@app_commands.describe(arg="Thing to say:")
async def say(interaction: discord.Interaction, arg: str):
    await interaction.response.send_message(f"{interaction.user.name} said: `{arg}`")


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

keep_alive()
asyncio.run(main())
