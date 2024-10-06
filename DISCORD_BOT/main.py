# Imports
import logging
import discord
from dotenv import load_dotenv
import os
import shutil
import re
import pytz
from datetime import datetime
import sqlite3

async def dotEnvUpdate():
	# Loads environment file
	load_dotenv()

	# Infrastructure Variables
	global pathDelim
	pathDelim = os.getenv('PATHDELIM')
	global assetsPath
	assetsPath = str(os.getenv('ASSETSPATH'))
	global tmpDir
	tmpDir = str(os.getenv('TMPDIR'))

	#Channel Config
	global microChannelID
	microChannelID = int(os.getenv('MICROCHANNEL'))
	global microMD
	microMD = str(os.getenv('MDPATH')) + pathDelim + "microMessages.md"
	global postsDir
	postsDir = str(os.getenv('POSTDIR'))
	global blogChannelID
	blogChannelID = int(os.getenv('BLOGCHANNEL'))
	global blogMD
	blogMD = postsDir + pathDelim + "blogMessages.md"
	global aboutChannelID
	aboutChannelID = int(os.getenv('ABOUTCHANNEL'))
	global aboutMD
	aboutMD = str(os.getenv('MDPATH')) + pathDelim + "about.md"
	global logChannelID
	logChannelID = int(os.getenv('LOGCHANNEL'))


	# Three Channel Types:
	# MB - Microblogging
	# BL - Blogging
	# AB - About
	# List all channels to monitor here, and add a tuple with the channel type and markdown page to update
	global channels
	channels = [microChannelID, blogChannelID, aboutChannelID]
	global channeltypes
	channeltypes = ['MB', 'BL', 'AB']
	global channelMD
	channelMD = [microMD, blogMD, aboutMD]

async def logToChannel(self, trigger, text):
	logChannel = self.get_channel(logChannelID,)
	try:
		guildID = str(trigger.guild.id)
		channelID = str(trigger.channel.id)
		messageID = str(trigger.id)
		author = str(trigger.author.id)
		message = f"Re: https://discord.com/channels/{guildID}/{channelID}/{messageID}\n <@{author}> - This message has returned an error:\n{str(text)}"
	except:
		message = f"Re:{trigger}\n {text}"
	await logChannel.send(message)

async def writeTo(path, lines):
	file = open(path,"w")
	for lin in lines:
		file.write(f'{lin}\n')
	file.close()

async def microblogUpdate(self):
	channelID = channels[channeltypes.index('MB')]
	markdownPath = channelMD[channeltypes.index('MB')]
	
	channelData = self.get_channel(channelID)
	markdownLines = []
	async for message in channelData.history(limit=100):
		# Gets datetime datestamp of message, converts to datestamp:
		date = message.created_at
		date = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Australia/Perth'))
		datestamp = date.strftime("%d %b %Y, %I:%M %p") + " AWST"
		
		# Gets message author, avatar, message content, and embeds
		author = message.author.display_name
		avatar = message.author.avatar.url
		content = message.clean_content
		attached = message.attachments
		embeds = message.embeds
		# Checks if reply, gets replied message details
		if message.type == discord.MessageType.reply:
			replyMsg = message.reference.resolved
			replyTo = replyMsg.author.display_name
			replyContent = replyMsg.clean_content
			content = content + "<br />\n<br />\n_Original Message:_<br />\n> " + replyContent
			context = "\n_replied to " + replyTo + " at " + datestamp + "_<br />"
		else:
			context = "\n_wrote at " + datestamp + "_<br />"

		# Appends markdown file with the content & context
		markdownLines.append("### " + author + "\n")
		markdownLines.append(context)
		markdownLines.append(content + "\n")
		for attachment in attached:
			if attachment.content_type.split("/")[0] == "image":
				markdownLines.append(f'<img src="{attachment.url}"><br />')
			if attachment.content_type.split("/")[0] == "video":
				markdownLines.append(f'<video controls> <source src="{attachment.url}" type={attachment.content_type}> Your browser does not support the video tag. </video><br />')
		for embed in embeds:
			if embed.type == "video" or embed.type == "gifv":
				markdownLines.append(f'<video controls> <source src="{embed.url}"> Your browser does not support the video tag. </video><br />')
		markdownLines.append("---")
	await writeTo(markdownPath, markdownLines)
	print("Microblog Updated")		

async def aboutUpdate(self):
	channelID = channels[channeltypes.index('AB')]
	markdownPath = channelMD[channeltypes.index('AB')]
	channelData = self.get_channel(channelID)
	markdownLines = []
	markdownLines.append(f"# Current contributors of {channelData.guild.name}")
	markdownLines.append("<br />")
	markdownLines.append('<table style="width:100%">')
	async for message in channelData.history(limit=100):
		author = message.author.display_name
		avatarPath = assetsPath + pathDelim + "avatars" + pathDelim + author + ".png"
		await message.author.avatar.save(fp=avatarPath)
		content = message.clean_content
		markdownLines.append("<tr>")
		markdownLines.append(f'<td style="width:30%"><img src="assets/avatars/{author}.png" max-width="400" alt="{author} display image"></td>')
		markdownLines.append(f'<td style="width:70%"><h3>{author}</h3><br />{content}</td>')
		markdownLines.append("</tr>")
	markdownLines.append("</table>")
	await writeTo(markdownPath, markdownLines)
	print("About Updated")

async def blogUpdate(self):
	# Connects to local SQLite DB, checks if posts table exists, creates if it doesn't.
	con = sqlite3.connect("posts.db")
	cur = con.cursor()
	tbl = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
	if len(tbl.fetchall()) == 0:
		cur.execute("CREATE TABLE posts (ID, title, slug, author, published, excerpt);")
		con.commit()
		print("Created table")

	# Gets current list of directories in post directories
	dirs = set()
	for root, dir, files in os.walk(postsDir):
		dir = root.split(pathDelim)[6:]
		if dir != []:
			dir = pathDelim.join(dir)
			dirs.add(dir)
	
	channelID = channels[channeltypes.index('BL')]
	markdownPath = channelMD[channeltypes.index('BL')]
	channelData = self.get_channel(channelID)

	# Creates temp posts directory for modification
	os.mkdir(tmpDir)

	slugs = set()
	async for message in channelData.history(limit=100):
		# Pulls metadata from message
		author = message.author.display_name
		msgID = message.id
		avatar = message.author.avatar.url
		content = message.clean_content
		attached = message.attachments

		# Pulls contents of message to get title, slug, and publish date.
		key = []
		value = []
		for line in content.split("\n"):
			pair = line.split(": ")
			key.append(pair[0])
			value.append(pair[1])
		try:
			title = value[key.index("Title")]
			slug = value[key.index("Slug")]
			slugs.add(slug)
			publishDate = value[key.index("Published")]
			excerpt = value[key.index("Excerpt")]
		except:
			await logToChannel(self, message, "Key not found. Ensure message includes Title, Slug, PublishDate, and Tags separated by ': ' only. Tags are to be separated by commas.")
		
		fullPath = tmpDir + pathDelim + slug

		# Checks if publish date after today
		publish = datetime.strptime(publishDate, "%d/%m/%Y").date()
		now = datetime.now().date()
		if publish > now:
			continue
		published = datetime.strftime(publish,"%B %d, %Y")

		# Creates a folder for the slug
		try:
			os.mkdir(fullPath)
		except:
			await logToChannel(self, message, "Slug already used.")
			continue

		# Checks attachment is text and if markdown, saves to folder if so
		attachment = attached[0]
		if attachment.content_type.split("/")[0] != 'text':
			await logToChannel(self, message, "Invalid attachment for blog - must be a markdown file")
		elif attachment.content_type.split("; ")[0].split("/")[1] != "markdown":
			await logToChannel(self, message, "Invalid attachment for blog - must be a markdown file")
			# This tests separately to allow for expansion into potentially autoformatting plaintext
		else:
			await attachment.save(fp=fullPath + pathDelim + "content.md")

		# Pulls posttemplate file from assets into memory, makes changes, writes as index
		with open(assetsPath + pathDelim + "posttemplate.html", 'r') as template:
			html = template.read()
		
		valuesToReplace = [("{{title}}",title),("{{author}}",author),("{{publishdate}}",published)]
		for value in valuesToReplace:
			html = html.replace (value[0],value[1])
		
		with open(fullPath + pathDelim + "index.html", 'w') as output:
			output.write(html)

		sql = f"INSERT INTO posts (ID, title, slug, author, published, excerpt) VALUES ({msgID}, \"{title}\", \"{slug}\", \"{author}\", \"{publish}\", \"{excerpt}\");"
		cur.execute(sql)
		con.commit
	
	# Copies temp back into live folders & removes temp
	shutil.rmtree(postsDir)
	shutil.copytree(tmpDir,postsDir,symlinks=True)
	shutil.rmtree(tmpDir)
	cur.execute("SELECT * FROM posts ORDER BY published DESC")
	allposts = cur.fetchall()


async def update(self,msg=0):
	await dotEnvUpdate()
	updated = 0
	if msg == 0:
		await microblogUpdate(self)
		updated = updated + 1
		await aboutUpdate(self)	
		updated = updated + 1
		await blogUpdate(self)
		updated = updated + 1
	elif channeltypes[channels.index(msg.channel.id)] == "MB":
		await microblogUpdate(self)
		updated = updated + 1
	elif channeltypes[channels.index(msg.channel.id)] == "AB":
		await aboutUpdate(self)	
		updated = updated + 1
	elif channeltypes[channels.index(msg.channel.id)] == "BL":
		await blogUpdate(self)
		updated = updated + 1
	print(f'Updated {updated} channels')

class MyClient(discord.Client):
	async def on_ready(self):
		print(f'Logged on as {self.user}!')
		print(f"Bot ID {self.user.id}")
		await update(self)

	async def on_message(self, msg):
		if msg.author.id != self.user.id:
			await update(self, msg)
		
	async def on_raw_message_delete(self, msg):
		await update(self,msg)

	async def on_member_update(self,before,after):
		await update(self)

#Load token for bot from .env & define handler
load_dotenv()
token = os.getenv('TOKEN')
handler = logging.FileHandler(filename='DiscordBot.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)
client.run(token, log_handler=handler)