import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from googletrans import Translator, LANGUAGES
from dotenv import load_dotenv
from keep_alive import keep_alive
from jisho_api.word import Word

load_dotenv()
t = Translator()
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
	user_id = os.environ["USER_ID"]
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
	await ctx.send("I am a bot designed by Oden and a work in progress. Do '!help' for list of commands and '!help <command_name>' for more instructions")


class PageView(discord.ui.View):
	current_page : int = 1
	sep : int = 1

	async def send(self, ctx):
		self.message = await ctx.send(view=self)
		await self.update_message(self.data[:self.sep])

	def create_embed(self, data):
		embed = discord.Embed(title="Jisho", url="https://jisho.org/", description="This bot uses jisho's api. *[Click here for site](https://jisho.org/)*", colour=discord.Colour.random())
		
		for item in data:
			embed.add_field(name=f"{self.current_page}/{int(len(self.data) / self.sep)}", value=item, inline=False)
		return embed

	async def update_message(self, data):
		self.update_buttons()
		msg = await self.message.edit(embed=self.create_embed(data), view=self)
		#await msg.add_reaction("🔎")

	def update_buttons(self):
		if self.current_page == 1:
			self.first_page_button.disabled = True
			self.prev_button.disabled = True
		else:
			self.first_page_button.disabled = False
			self.prev_button.disabled = False

		if self.current_page == int(len(self.data) / self.sep):
			self.next_button.disabled = True
			self.last_page_button.disabled = True
		else:
			self.next_button.disabled = False
			self.last_page_button.disabled = False

	@discord.ui.button(label="<<", style=discord.ButtonStyle.primary)
	async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.current_page = 1
		until_item = self.current_page * self.sep
		await self.update_message(self.data[:until_item])
	
	@discord.ui.button(label="<", style=discord.ButtonStyle.primary)
	async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.current_page -=1
		until_item = self.current_page * self.sep
		from_item = until_item - self.sep
		await self.update_message(self.data[from_item:until_item])
	
	@discord.ui.button(label=">", style=discord.ButtonStyle.primary)
	async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.current_page +=1
		until_item = self.current_page * self.sep
		from_item = until_item - self.sep
		await self.update_message(self.data[from_item:until_item])
		
		
	@discord.ui.button(label=">>️", style=discord.ButtonStyle.primary)
	async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.defer()
		self.current_page = int(len(self.data) / self.sep) 
		until_item = self.current_page * self.sep
		from_item = until_item - self.sep
		await self.update_message(self.data[from_item:])


@bot.command()
async def jisho(ctx, *, arg):
	page_view = PageView()
	request = Word.request(arg).json()
	entries = json.loads(request)
	results = [item for item in entries["data"]]
	data = []

	for result in results:
		entry = ""
		word = result["japanese"][0]["word"] if result["japanese"][0]["word"] else result["japanese"][0]["reading"]
		reading = f"【{result['japanese'][0]['reading']}】" if result["japanese"][0]["word"] and result["japanese"][0]["reading"] else ""
		fq = "\ncommon word" if result["is_common"] else ""
		jlpt = ", " + (", ".join(result["jlpt"])) if result["jlpt"] and fq else "" or "\n"+(", ".join(result["jlpt"])) if result["jlpt"] else ""
		tags = ", " + (", ".join(result["tags"])) if result["tags"] and (jlpt or fq) else "" or "\n" + (", ".join(result["tags"])) if result["tags"] else ""
		entry = f"**{word}{reading}**{fq}{jlpt}{tags}\n"
	
		for index, result2 in enumerate(result["senses"], start=1):	
			parts_of_speech = "\n"+"***"+(", ".join(result2["parts_of_speech"])) + "***" if result2["parts_of_speech"] else ""
			links = result2["links"] if result2["links"] else ""
			english_definitions = ', '.join(result2["english_definitions"])
			tags = "\n" + (", ".join(result2["tags"])) if result2["tags"] else ""
			restrictions = ", Only applies to " + (", ".join(result2["restrictions"])) if result2["restrictions"] and tags else "" or "\nOnly applies to " + ", ".join(result2["restrictions"]) if result2["restrictions"] else ""
			see_also = "".join(result2["see_also"])
			see_also_link = "https://jisho.org/search/" + ("%20".join(see_also.split())) if " " in see_also else "https://jisho.org/search/" + see_also
			see_also = f", *see also [{see_also}]({see_also_link})*" if result2["see_also"] and (tags or restrictions) else "" or f"\n*see also [{see_also}]({see_also_link})*" if result2["see_also"] else ""
			info = ", "+(", ".join(result2["info"])) if result2["info"] and (tags or restrictions or see_also) else "" or ", ".join(result2["info"]) if result2["info"] else ""
			entry += f"{parts_of_speech}\n{index}. {english_definitions}{tags}{restrictions}{see_also}{info}"
			
			if links:
				list_ = []
				
				for link in links:
					text = link["text"]
					url = link["url"]
					text_url = f"[{text}]({url})"
					list_.append(text_url)
				entry+="\n"
				entry+= "*"+("\n".join(list_))+"*"
			entry+="\n"
		
		if len(result["japanese"]) > 1:
			list_ = []
			
			for dict_ in result["japanese"][1:]:
				word = dict_["word"] if dict_["word"] else dict_["reading"]
				reading = f"【{dict_['reading']}】" if dict_["word"] else ""
				other_form = f"{word}{reading}"
				list_.append(other_form)
			entry+= "\nOther forms\n" + "、".join(list_)
		data.append(entry)
	page_view.data = data
	await page_view.send(ctx)


@bot.command()
async def translate(ctx, *, args=None):
	"""
<key>→<language>
af→afrikaans
sq→albanian
am→amharic
ar→arabic
hy→armenian
az→azerbaijani
eu→basque
be→belarusian
bn→bengali
bs→bosnian
bg→bulgarian
ca→catalan
ceb→cebuano
ny→chichewa
zh-cn→chinese (simplified)
zh-tw→chinese (traditional)
co→corsican
hr→croatian
cs→czech
da→danish
nl→dutch
en→english
eo→esperanto
et→estonian
tl→filipino
fi→finnish
fr→french
fy→frisian
gl→galician
ka→georgian
de→german
el→greek
gu→gujarati
ht→haitian creole
ha→hausa
haw→hawaiian
iw→hebrew
he→hebrew
hi→hindi
hmn→hmong
hu→hungarian
is→icelandic
ig→igbo
id→indonesian
ga→irish
it→italian
ja→japanese
jw→javanese
kn→kannada
kk→kazakh
km→khmer
ko→korean
ku→kurdish (kurmanji)
ky→kyrgyz
lo→lao
la→latin
lv→latvian
lt→lithuanian
lb→luxembourgish
mk→macedonian
mg→malagasy
ms→malay
ml→malayalam
mt→maltese
mi→maori
mr→marathi
mn→mongolian
my→myanmar (burmese)
ne→nepali
no→norwegian
or→odia
ps→pashto
fa→persian
pl→polish
pt→portuguese
pa→punjabi
ro→romanian
ru→russian
sm→samoan
gd→scots gaelic
sr→serbian
st→sesotho
sn→shona
sd→sindhi
si→sinhala
sk→slovak
sl→slovenian
so→somali
es→spanish
su→sundanese
sw→swahili
sv→swedish
tg→tajik
ta→tamil
te→telugu
th→thai
tr→turkish
uk→ukrainian
ur→urdu
ug→uyghur
uz→uzbek
vi→vietnamese
cy→welsh
xh→xhosa
yi→yiddish
yo→yoruba
zu→zulu

Using any KEY from above, specify a <from> or <to> language. One or both keys can be implied.

!translate <from>:<to><message>
Example: !translate ja:en ありがとうございます
Output: Thank you

Can also translate replied messages.
	"""
	seperator = ":"
	default_lang = "en"
	error_msg = "There's nothing to translate 🗿"
	
	if str(ctx.message.type) == "MessageType.default" and args:
		all_words = args.split()
		keys = all_words[0].split(seperator) if seperator in all_words[0] else (None, None)
		first_key = keys[0] if keys[0] in LANGUAGES else None
		second_key = keys[1] if keys[1] in LANGUAGES else None
		msg = args[len(all_words[0])+1:] if first_key or second_key else args
		from_ = first_key if first_key else t.detect(msg).lang
		to = second_key if second_key else default_lang
	elif str(ctx.message.type) == "MessageType.reply":
		msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
		msg = msg.content
		keys = args.split(seperator) if args and seperator in args else (None, None)
		from_ = keys[0] if keys[0] in LANGUAGES else t.detect(msg).lang
		to = keys[1] if keys[1] in LANGUAGES else default_lang
	else:
		await ctx.reply("Do `!help translate` for instructions")
		return
		
	if msg:
		from_ = from_[0] if isinstance(from_, list) else from_
		translation = t.translate(msg, src=from_, dest=to)
		pronunciation = translation.extra_data["translation"][-1][2]
		
		embed = discord.Embed(colour=discord.Colour.random())
		embed.add_field(name="Translation", value=translation.text, inline=False)
		message = await ctx.reply(embed=embed)
		
		if all((pronunciation, translation.text != pronunciation, pronunciation != msg)):
			await message.add_reaction("🔎")
			check = lambda reaction, user: all((reaction.message.id == message.id, str(reaction.emoji) == "🔎"))
			
			while True:
				reaction, user = await bot.wait_for("reaction_add", check=check)
				await reaction.remove(user)
				embed.add_field(name="Pronunciation", value=pronunciation, inline=False)
				await message.edit(embed=embed)
				reaction, user = await bot.wait_for("reaction_add", check=check)
				await reaction.remove(user)
				embed.remove_field(index=1)
				await message.edit(embed=embed)
	else:
		await ctx.reply(error_msg)

keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")

bot.run(TOKEN)
