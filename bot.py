
from dotenv import load_dotenv
import discord
import youtube_dl
import asyncio
import os
import search
import datetime
from discord.ext import commands,tasks
import wolframalpha


load_dotenv()
intents = discord.Intents.all() # or .all() if you ticked all, that is easier
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix = '!', intents=intents)
maths = wolframalpha.Client(os.getenv("app_id"))
list = ['fuck','motherfucker','fucker','bastard','Bastard','mf','fck','dickhead','dick','pussy','boobs','Fuck','nigga','Nigga','lavde','Madarchod','madarchod',
'Behenchod','behenchod','chutiya','bitch','ass']
gamespot_web = search.Gamespot()
no_result_message = "Sorry, we can't find what you are searching for"

@bot.event
async def on_ready():
    print("Bot is ready!!")

@bot.command(name='hello',help = "Bot greets you!")
async def hello(ctx):
    await ctx.send("Hello")

@bot.command(name="math",help = "calculates the maths expression ")
async def math(ctx,*,message):
    res = maths.query(message)
    em = discord.Embed(title= message , description = next(res.results).text)
    await ctx.send(embed=em)

@bot.command(name = 'game',help = 'searches the website and sends relevant links')
async def game(ctx,message):
    key_words= gamespot_web.key_words_search_words(message)
    result_links = gamespot_web.search(key_words)
    links = gamespot_web.send_link(result_links, key_words)
    
    if len(links) > 0:
      for link in links:
       await ctx.send(link)
    else:
      await ctx.send(no_result_message)

@bot.command(name='ban',help='bans the user')
async def ban(ctx,user: discord.User = None, *, reason = None):
    if (user == None or user == ctx.message.author):
      await ctx.send("**Why ban yourself when u can ban others??!!**")
      return
    if (reason == None):
      reason = "**No reason given**"
    message = f"**You have been banned from {ctx.guild.name} for following reason: {reason}**"
    await user.send(message)
    await ctx.guild.ban(user, reason=reason)
    await ctx.send(f"**<@{user}> has been banned for the following reason: {reason}**")


@bot.command(name = 'timeout', help = 'The user is timed out from the server')
async def timeout(ctx, member: discord.Member = None, time:int = None):
  if (member == None or member == ctx.message.author):
    await ctx.send("**You timed out yourself, wait you can't!!**")
    return
  duration = datetime.timedelta(minutes=time)
  user_id = member.id
  await member.timeout_for(duration)
  await ctx.send(f"**<@{user_id}> is successfully timed out for {time} minutes!!**")
        

@bot.listen('on_message')
async def blacklist(message):
    userid = message.author.id
    for word in list:
        if word in message.content:
         await message.delete()
         await message.channel.send("**Blacklisted word detected!!...deleting msg..User <@{}> has been warned!!**".format(userid))


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'audioformat': 'mp3',
    'outtmpl': '/music_files/%(title)s.mp3',
    'preferredquality': '320',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' 
    
}

ffmpeg_options = {
    
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


queue=[]

@tasks.loop(seconds=5)
async def not_playing(ctx):
    voice_client = ctx.message.guild.voice_client
    server = ctx.message.guild
    voice_channel = server.voice_client
    if voice_client and voice_client.is_playing():
        pass
    else:
        if voice_client and voice_client.is_paused():
            pass
        else:
            async with ctx.typing():
                player_queue = await YTDLSource.from_url(queue[0], loop=client.loop)
                voice_channel.play(player_queue, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send('**Now playing: {}**'.format(player_queue.title)+' **\nRequested By: **'+format(ctx.author.mention))
            os.remove(player_queue.title)
            del queue[0]


@bot.command(name='join' ,help='This command will connect me')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.author.mention))
        return
    else:
        channel = ctx.message.author.voice.channel
        
    await channel.connect()


@bot.command(name='play', help='This command plays music')
async def play(ctx,url,*args):
      voice_client = ctx.message.guild.voice_client
      server = ctx.message.guild
      voice_channel = server.voice_client
      

      for word in args:
        url += ' '
        url += word
      if voice_client and voice_client.is_playing():
        queue.append(url)
        print(queue)
        await ctx.send('**Added:** {}'.format(url)+' **Requested By: **'+format(ctx.author.mention))
        if not not_playing.is_running():
          not_playing.start(ctx)
      else:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=client.loop)
                voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send('**Now Playing:** {}'.format(player.title)+'** \nRequested By: **'+format(ctx.author.mention))
   


@bot.command(name='disconnect', help='This command stops the music and makes the bot leave the voice channel')
async def disconnect(ctx):
    voice_client = ctx.message.guild.voice_client
    await ctx.send('**Disconnected...Sayonara!!**')
    queue.clear()
    ctx.voice_client.stop()
    await voice_client.disconnect()
    

@bot.command(name='stop', help='Stops the music')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await ctx.send('**Stopped**')
    await voice_client.stop()

@bot.command(name='queue', help='Displays the queue')
async def queue_(ctx):
    await ctx.send('**Queue: ** ```{\n}```'.format(queue))

@bot.command(name='pause' , help='Pauses the music')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("**Paused**")
    else:
        await ctx.send("**I am not playing anything!!!**")

@bot.command(name='resume', help='Resumes the music')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("**Resumed**")
    else:
        await ctx.send("**It's playing**")

@bot.command(name='skip' , help='Skips the song')
async def skip(ctx):
        server = ctx.message.guild
        voice_channel = server.voice_client
        voice_client = ctx.message.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            async with ctx.typing():
                player_queue = await YTDLSource.from_url(queue[0], loop=client.loop)
                voice_channel.play(player_queue, after=lambda e: print('Player error: %s' % e) if e else None)
            await ctx.send("**Song Skipped**")
            await ctx.send('**Now playing:** {}'.format(player_queue.title))
            del queue[0]  


bot.run(os.getenv("TOKEN"))

