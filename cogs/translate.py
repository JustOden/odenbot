import discord
from discord.ext import commands
from googletrans import Translator, LANGUAGES

t = Translator()


class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def translate(self, ctx, *, args=None):
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
    Example: o!translate ja:en ありがとうございます
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
                    reaction, user = await self.bot.wait_for("reaction_add", check=check)
                    await reaction.remove(user)
                    embed.add_field(name="Pronunciation", value=pronunciation, inline=False)
                    await message.edit(embed=embed)
                    reaction, user = await self.bot.wait_for("reaction_add", check=check)
                    await reaction.remove(user)
                    embed.remove_field(index=1)
                    await message.edit(embed=embed)
        else:
            await ctx.reply(error_msg)


async def setup(bot):
    await bot.add_cog(Translate(bot))