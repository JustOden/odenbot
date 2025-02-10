import json
import discord
from discord.ext import commands
from jisho_api.word import Word
from jisho_api.kanji import Kanji
from jisho_api.sentence import Sentence
from jisho_api.tokenize import Tokens


class PageView(discord.ui.View):
    current_page : int = 1
    sep : int = 1

    async def send(self, ctx):
        self.message = await ctx.send(view=self)
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        embed = discord.Embed(title="Jisho", url="https://jisho.org/", description="This bot uses an api for jisho. *[Click here for site](https://jisho.org/)*", colour=discord.Colour.random())

        for item in data:
            embed.add_field(name=f"Page {self.current_page} of {int(len(self.data) / self.sep)}", value=item, inline=False)
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


class Jisho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def word_search(self, arg) -> list:
        URL = "https://jisho.org/search/"
        request = Word.request(arg).json()
        entries = json.loads(request)
        results = [item for item in entries["data"]]
        data = []

        add_c = lambda s: ", " + s
        add_nl = lambda s: "\n" + s
        join_c = lambda s: ", ".join(s)
        bold_i = lambda s: "***" + s + "***"
        add_i = lambda s: "*" + s + "*"

        for result in results:
            entry = ""
            word = _word if (_word:=result["japanese"][0]["word"]) else result["japanese"][0]["reading"]
            reading = f"【{_reading}】" if word and (_reading:=result["japanese"][0]["reading"]) else ""
            fq = "\ncommon word" if result["is_common"] else ""
            jlpt = add_c(join_c(_jlpt)) if (_jlpt:=result["jlpt"]) and fq else add_nl(join_c(_jlpt)) if _jlpt else ""
            tags = add_c(join_c(_tags)) if (_tags:=result["tags"]) and (jlpt or fq) else add_nl(join_c(_tags)) if _tags else ""
            entry += f"**{word}{reading}**{fq}{jlpt}{tags}\n"

            for index, result2 in enumerate(result["senses"], start=1):
                parts_of_speech = add_nl(bold_i(join_c(_parts_of_speech))) if (_parts_of_speech:=result2["parts_of_speech"]) else ""
                links = _links if (_links:=result2["links"]) else ""
                english_definitions = join_c(result2["english_definitions"])
                tags = add_nl(join_c(_tags)) if (_tags:=result2["tags"]) else ""
                restrictions = add_c("Only applies to " + join_c(_restrictions)) if (_restrictions:=result2["restrictions"]) and tags else add_nl("Only applies to " + join_c(_restrictions)) if _restrictions else ""
                _see_also = "".join(result2["see_also"])
                see_also_link = URL + ("%20".join(_see_also.split())) if " " in _see_also else URL + _see_also
                see_also = f", *see also [{_see_also}]({see_also_link})*" if _see_also and (tags or restrictions) else f"\n*see also [{_see_also}]({see_also_link})*" if _see_also else ""
                info = add_c(join_c(_info)) if (_info:=result2["info"]) and (tags or restrictions or see_also) else join_c(_info) if _info else ""
                entry += f"{parts_of_speech}\n{index}. {english_definitions}{tags}{restrictions}{see_also}{info}"

                if links:
                    list_ = []
                    for link in links:
                        text = link["text"]
                        url = link["url"]
                        text_url = f"[{text}]({url})"
                        list_.append(text_url)
                    entry += "\n"
                    entry += add_i("\n".join(list_))
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
    
    def kanji_search(self, arg):
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
    
    def example_search(self, arg):
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
    
    def token_search(self, arg):
        request = Tokens.request(arg).json()
        results = json.loads(request)
        data = []
        entry = ""
        for token in results["data"]:
            entry += f"{token['token']} {token['pos_tag']}\n"
        data.append(entry)
        return data

    @commands.command()
    async def jisho(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.word_search(arg)
        await page_view.send(ctx)
    
    @commands.command()
    async def kanji(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.kanji_search(arg)
        await page_view.send(ctx)
    
    @commands.command()
    async def examples(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.example_search(arg)
        await page_view.send(ctx)
    
    @commands.command()
    async def tokenize(self, ctx, *, arg):
        page_view = PageView()
        page_view.data = self.token_search(arg)
        await page_view.send(ctx)


async def setup(bot):
    await bot.add_cog(Jisho(bot))