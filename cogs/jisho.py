import json
import discord
from discord.ext import commands
from jisho_api.word import Word


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
        # await msg.add_reaction("🔎")

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
        super().__init__()
        self.bot = bot

    @commands.command()
    async def jisho(self, ctx, *, arg):
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

            data.append(entry[:1015] + " [...]")
        page_view.data = data
        await page_view.send(ctx)


async def setup(bot):
    await bot.add_cog(Jisho(bot))