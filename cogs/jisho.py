import json
import discord
from discord.ext import commands
from jisho_api.word import Word
from jisho_api.kanji import Kanji
from jisho_api.sentence import Sentence
from jisho_api.tokenize import Tokens

URL = "https://jisho.org/search/"


class PageView(discord.ui.View):
    current_page : 1
    sep : 1
    
    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the author of this command can perform this action.", ephemeral=True)
            return False
        return True
    
    # async def on_timeout(self):
    #     await self.ctx.send(f"Interaction for {self.invoked_command} done by {self.ctx.author} has timed out.", ephemeral=True)

    async def send(self, ctx, arg):
        self.ctx = ctx
        self.arg = arg
        self.invoked_command = ctx.invoked_with
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        url = URL+("%20".join(self.arg)) if " " in URL else URL + self.arg
        embed = discord.Embed(title=self.arg, url=url, colour=discord.Colour.random())

        if len(self.data) > 1:
            for entry in data:
                embed.add_field(name=f"Page {self.current_page} of {int(len(self.data) / self.sep)}", value=entry, inline=False)
                embed.title = self.arg
        else:
            for entry in data:
                embed.add_field(name="Result", value=entry, inline=False)
                embed.title = self.arg

        return embed

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

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
        
        if self.invoked_command in ("jisho", "j", "J"):
            self.jisho_button.disabled = True
        else:
            self.jisho_button.disabled = False
        
        if self.invoked_command in ("kanji", "k", "K"):
            self.kanji_button.disabled = True
        else:
            self.kanji_button.disabled = False
        
        if self.invoked_command in ("examples", "e", "E"):
            self.examples_button.disabled = True
        else:
            self.examples_button.disabled = False

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.primary)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        until_item = self.current_page * self.sep
        await self.update_message(self.data[:until_item])

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_message(self.data[from_item:until_item])

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_message(self.data[from_item:until_item])

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.sep)
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_message(self.data[from_item:])

    @discord.ui.button(label="言葉", style=discord.ButtonStyle.primary)
    async def jisho_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.invoked_command = "j"
        self.data = Jisho.word_search(self.arg)
        self.current_page = 1
        await self.update_message(self.data[:self.sep])

    @discord.ui.button(label="漢字", style=discord.ButtonStyle.primary)
    async def kanji_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.invoked_command = "k"
        self.data = Jisho.kanji_search(self.arg)
        self.current_page = 1
        await self.update_message(self.data[:self.sep])

    @discord.ui.button(label="例文", style=discord.ButtonStyle.primary)
    async def examples_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.invoked_command = "e"
        self.data = Jisho.examples_search(self.arg)
        self.current_page = 1
        await self.update_message(self.data[:self.sep])


class Jisho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def word_search(arg: str) -> list:
        request = Word.request(arg).json()
        entries = json.loads(request)
        results = [item for item in entries["data"]]
        data = []
        
        add_nl = lambda s: "\n" + s
        join_c = lambda s: ", ".join(s)
        bold_i = lambda s: "***" + s + "***"
        add_i = lambda s: "*" + s + "*"

        for result in results:
            entry = ""
            word = _word if (_word:=result["japanese"][0]["word"]) else result["japanese"][0]["reading"]
            reading = _reading if word and (_reading:=result["japanese"][0]["reading"]) else ""

            fq = "common word" if result["is_common"] else ""
            jlpt = join_c(_jlpt) if (_jlpt:=result["jlpt"]) else ""
            tags = join_c(_tags) if (_tags:=result["tags"]) else ""
            
            joined = add_nl(f"`{_joined}`") if (_joined:=join_c([i for i in (fq, jlpt, tags) if i])) else ""
            entry += f"**{word}【{reading}】**{joined}\n"

            for index, senses in enumerate(result["senses"], start=1):
                parts_of_speech = add_nl(bold_i(join_c(_parts_of_speech))) if (_parts_of_speech:=senses["parts_of_speech"]) else ""
                links = _links if (_links:=senses["links"]) else ""

                english_definitions = join_c(senses["english_definitions"])
                tags = join_c(_tags) if (_tags:=senses["tags"]) else ""
                restrictions = "Only applies to " + join_c(_restrictions) if (_restrictions:=senses["restrictions"]) else ""

                _see_also = "".join(senses["see_also"])
                see_also_link = URL + ("%20".join(_see_also.split())) if " " in _see_also else URL + _see_also
                see_also = f"*see also [{_see_also}]({see_also_link})*" if _see_also else ""

                info = join_c(_info) if (_info:=senses["info"]) else ""
                joined = add_nl(_joined) if (_joined:=join_c([i for i in (tags, restrictions, see_also, info) if i])) else ""
                entry += f"{parts_of_speech}\n{index}. {english_definitions}{joined}"

                if links:
                    list_ = []
                    
                    for link in links:
                        text = link["text"]
                        url = link["url"]
                        text_url = f"[{text}]({url})"
                        list_.append(text_url)
                        
                    entry += add_nl(add_i("\n".join(list_)))
                    
                entry += "\n"

            if len(result["japanese"]) > 1:
                list_ = []
                
                for dict_ in result["japanese"][1:]:
                    word = _word if (_word:=dict_["word"]) else dict_["reading"]
                    reading = f"【{dict_['reading']}】" if dict_["word"] else ""
                    other_form = f"{word}{reading}"
                    list_.append(other_form)
                    
                entry += "\nOther forms\n" + "、".join(list_)

            if len(entry) > 1015:
                entry = entry[:1015] + " [...]"

            data.append(entry)
            
        return data

    @staticmethod
    def kanji_search(arg: str) -> list:
        results = [json.loads(Kanji.request(i).json()) for i in arg]
        data = []

        for result in results:
            entry = ""
            kanji = result["data"]["kanji"]
            strokes = result["data"]["strokes"]
            
            main_meanings = result["data"]["main_meanings"]
            kun_readings = result["data"]["main_readings"]["kun"]
            on_readings = result["data"]["main_readings"]["on"]
            
            grade = result["data"]["meta"]["education"]["grade"]
            jlpt = result["data"]["meta"]["education"]["jlpt"]
            newspaper_rank = result["data"]["meta"]["education"]["newspaper_rank"]
            
            entry += f"Kanji: {kanji}\nStrokes: {strokes}\nMain meanings: {main_meanings}\nKun-readings: {kun_readings}\nOn-readings: {on_readings}\nGrade: {grade}\nJLPT: {jlpt}\nNewspaper rank: {newspaper_rank}"
            data.append(entry)
            
        return data
    
    @staticmethod
    def examples_search(arg: str) -> list:
        request = Sentence.request(arg).json()
        results = json.loads(request)
        data = []
        entry = ""

        for index, result in enumerate(results["data"], start=1):
            japanese = result["japanese"]
            en_translation = result["en_translation"]
            entry += f"{index}. {japanese}\n{en_translation}\n\n"

        if len(entry) > 1015:
            entry = entry[:1015]  + " [...]"

        data.append(entry)

        return data
    
    @staticmethod
    def token_search(arg: str) -> list:
        request = Tokens.request(arg).json()
        results = json.loads(request)
        data = []
        entry = ""
        
        for token in results["data"]:
            entry += f"{token['token']} {token['pos_tag']}\n"
            
        data.append(entry)
        
        return data

    @commands.command(aliases=["j", "J"])
    async def jisho(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.word_search(arg)
        await page_view.send(ctx, arg)
    
    @commands.command(aliases=["k", "K"])
    async def kanji(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.kanji_search(arg)
        await page_view.send(ctx, arg)
    
    @commands.command(aliases=["e", "E"])
    async def examples(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.examples_search(arg)
        await page_view.send(ctx, arg)
    
    @commands.command(aliases=["tn"])
    async def tokenize(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.token_search(arg)
        await page_view.send(ctx, arg)
        print("Success?")


async def setup(bot):
    await bot.add_cog(Jisho(bot))