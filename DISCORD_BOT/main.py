# Imports
import logging
import discord
from discord.ext import commands
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
	global uploadPath
	uploadPath = assetsPath + pathDelim + "upload"
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
	global assetChannelID
	assetChannelID = int(os.getenv('ASSETCHANNEL'))

	# Three Channel Types:
	# MB - Microblogging
	# BL - Blogging
	# AB - About
	# AS - Assets
	# List all channels to monitor here
	global channels
	channels = [microChannelID, blogChannelID, aboutChannelID, assetChannelID]
	global channeltypes
	channeltypes = ['MB', 'BL', 'AB', 'AS']
	global channelMD
	channelMD = [microMD, blogMD, aboutMD, ""]

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
	try:
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
	except:
		await logToChannel(self,"Microblog","Microblog failed to update")		

async def aboutUpdate(self):
	try:
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
			attachment = message.attachments[0]
			await attachment.save(fp=avatarPath)
			content = message.clean_content
			markdownLines.append("<tr>")
			markdownLines.append(f'<td style="width:30%"><img src="/assets/avatars/{author}.png" class="prof-img" alt="{author} display image"></td>')
			markdownLines.append(f'<td style="width:70%" class="prof-desc"><h3>{author}</h3><br />{content}</td>')
			markdownLines.append("</tr>")
		markdownLines.append("</table>")
		await writeTo(markdownPath, markdownLines)
		print("About Updated")
	except:
		logToChannel(self, "About Update", "About update failed")

async def blogUpdate(self):
	try:
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
		shutil.rmtree(tmpDir,ignore_errors=True)
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
			try:
				for line in content.split("\n"):
					pair = line.split(": ")
					key.append(pair[0])
					value.append(pair[1])
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
			
			valuesToReplace = [("{{title}}",title),("{{excerpt}}",excerpt),("{{author}}",author),("{{publishdate}}",published)]
			for value in valuesToReplace:
				html = html.replace (value[0],value[1])
			
			with open(fullPath + pathDelim + "index.html", 'w') as output:
				output.write(html)
				output.close()

			sql = f"INSERT INTO posts (ID, title, slug, author, published, excerpt) VALUES ({msgID}, \"{title}\", \"{slug}\", \"{author}\", \"{publish}\", \"{excerpt}\");"
			cur.execute(sql)
			con.commit
		
		#Selects all posts, generates html for input into file
		cur.execute("SELECT slug, title, published, author, excerpt FROM posts ORDER BY published DESC")
		allposts = cur.fetchall()

		postbody = []

		for post in allposts:
			publishdate = datetime.strptime(post[2], "%Y-%m-%d").date()
			publishdate = datetime.strftime(publishdate,"%B %d, %Y")
			postbody.append("<div class=\"post\">\n")
			postbody.append(f"<div class=\"posttitle\"><a href=\"{post[0]}\"><h2>{post[1]}</h2></a><i>Published: {publishdate} by {post[3]}</i></div>\n")
			postbody.append(f"<div class=\"postexcerpt\"><p>{post[4]}</p></div>\n</div>\n")

		# Gets template file from assets, splits into 2 arrays
		with open(assetsPath + pathDelim + "postindex.html", 'r') as postIndex:
			indexHTML = postIndex.read()
			lines = indexHTML.split("\n")
			repl = lines.index("{{REPLACE}}")
			pre = lines[0:repl]
			aft = lines[repl+1::]

		# Meges arrays around body text generated
		html = []
		html += pre 
		html += postbody
		html += aft	
		#Writes to file
		with open(tmpDir + pathDelim + "index.html", 'w', encoding="UTF-8") as postIndex:
			for lin in html:
				postIndex.write(lin + "\n")
			postIndex.close()

		# Copies temp back into live folders & removes temp
		shutil.rmtree(postsDir)
		shutil.copytree(tmpDir,postsDir,symlinks=True)
		shutil.rmtree(tmpDir)

		print("Blog Updated")
	except:
		logToChannel(self, "Blog Update", "Blog failed to update")

async def assetUpdate(self):
	try:
		channelID = channels[channeltypes.index('AS')]
		channelData = self.get_channel(channelID)

		uploads = []
		async for message in channelData.history():
			attachment = message.attachments[0]
			fileName = message.clean_content + "." + attachment.content_type.split("/")[1]
			fullPath = uploadPath + pathDelim + fileName
			if not os.path.exists(fullPath):
				await attachment.save(fp=fullPath)

			uploads.append(fileName)
		
		files = os.listdir(uploadPath)
		for file in files:
			if file not in uploads:
				os.remove(uploadPath + pathDelim + file)
		
		print("Assets Updated")
	except:
		logToChannel(self,"Asset update", "Assets failed to update")
	
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
		await assetUpdate(self)
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
	elif channeltypes[channels.index(msg.channel.id)] == "AS":
		await assetUpdate(self)
		updated = updated + 1
	print(f'Updated from {updated} channels')

class MyClient(discord.Client):
	async def on_ready(self):
		print(f'Logged on as {self.user}!')
		print(f"Bot ID {self.user.id}")
		await update(self)

	async def on_message(self, msg):
		if msg.clean_content == "!forceupdate":
			await update(self)
			await logToChannel(self, "Forced update", "Update complete")
		elif msg.author.id != self.user.id:
			await update(self, msg)
		
	async def on_raw_message_delete(self, msg):
		await update(self)

	async def on_message_edit(self,before,after):
		await update(self)

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