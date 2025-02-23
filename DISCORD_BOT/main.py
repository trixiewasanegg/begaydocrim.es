# Imports
import logging
import discord
from dotenv import load_dotenv
import os
import shutil
import pytz
from datetime import datetime
import sqlite3
import traceback
from PIL import Image

async def dotEnvUpdate():
	# Loads environment file
	load_dotenv()

	# Infrastructure Variables
	global pathDelim
	pathDelim = os.getenv('PATHDELIM')
	global botPath
	botPath = str(os.getenv('BOTPATH'))
	global tmpDir
	tmpDir = botPath + pathDelim + "tmpdir"
	global sqlLiteDB
	sqlLiteDB = botPath + pathDelim + str(os.getenv('SQLITEDB'))
	global htmlDir
	htmlDir = str(os.getenv('HTMLPATH'))
	global assetsPath
	assetsPath = htmlDir + pathDelim + "assets"
	global uploadPath
	uploadPath = assetsPath + pathDelim + "upload"

	#Channel Config
	global microChannelID
	microChannelID = int(os.getenv('MICROCHANNEL'))
	global microMD
	microMD = str(os.getenv('MDPATH')) + pathDelim + "microMessages.md"
	global postsDir
	postsDir = str(os.getenv('POSTDIR'))
	global blogChannelID
	blogChannelID = int(os.getenv('BLOGCHANNEL'))
	global aboutChannelID
	aboutChannelID = int(os.getenv('ABOUTCHANNEL'))
	global aboutMD
	aboutMD = str(os.getenv('MDPATH')) + pathDelim + "about.md"
	global logChannelID
	logChannelID = int(os.getenv('LOGCHANNEL'))
	global assetChannelID
	assetChannelID = int(os.getenv('ASSETCHANNEL'))
	global socialChannelID
	socialChannelID = int(os.getenv('SOCIALCHANNEL'))
	global socialMD
	socialMD = str(os.getenv('MDPATH')) + pathDelim + "socials.md"

	# Three Channel Types:
	# MB - Microblogging
	# BL - Blogging
	# AB - About
	# AS - Assets
	# SC - Social Media Accounts
	# List all channels to monitor here
	global channels
	channels = [microChannelID, blogChannelID, aboutChannelID, assetChannelID, socialChannelID]
	global channeltypes
	channeltypes = ['MB', 'BL', 'AB', 'AS', 'SC']
	global channelMD
	channelMD = [microMD, "", aboutMD, "", socialMD]

async def logToChannel(self, trigger, text):
	logChannel = self.get_channel(logChannelID,)
	try:
		guildID = str(trigger.guild.id)
		channelID = str(trigger.channel.id)
		messageID = str(trigger.id)
		author = str(trigger.author.id)
		message = f"Re: https://discord.com/channels/{guildID}/{channelID}/{messageID}\n <@{author}> - This message has returned an error:\n{str(text)}"
	except:
		message = f"Re: {trigger}\n {text}"
	await logChannel.send(message)

async def writeTo(path, lines):
	file = open(path,"w", encoding="UTF-8")
	for lin in lines:
		file.write(f'{lin}\n')
	file.close()

async def imgDownload(self, attachment, filename, path):
	# Gets media type
	mediaTyp = attachment.content_type.split("/")

	tmpFile = path + pathDelim + "tmp" + filename + "." + mediaTyp[1]

	# Generates final file name
	returnVal = filename + ".webp"
	finalFile = path + pathDelim + returnVal

	# Downloads to tmp file & compresses if not exists
	if not os.path.exists(finalFile):
		await attachment.save(fp=tmpFile)
		# Opens image with pillow, downsizes to 1000px high, saves as webp
		with Image.open(tmpFile) as img:
			ratio = img.size[0] / img.size[1]
			height = 1000
			width = height * ratio
			img.thumbnail([height, width])
			img.save(finalFile, 'webp')
			os.remove(tmpFile)

	return returnVal

async def microblogUpdate(self):
	try:
		# Boilerplate to get info from channel
		channelID = channels[channeltypes.index('MB')]
		channelData = self.get_channel(channelID)

		# Runs through messages found in channelData, generates markdown file as list
		markdownLines = []
		async for message in channelData.history(limit=100):
			# Gets datetime datestamp of message, converts to datestamp:
			date = message.created_at
			date = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Australia/Perth'))
			datestamp = f"\n_{date.strftime("%d %b %Y, %I:%M %p")} AWST_ <br /><br />"
			
			# Gets message  message content and embeds
			content = message.clean_content.replace("\n", "<br />")
			attached = message.attachments
			embeds = message.embeds

			# Checks if reply, gets replied message details
			if message.type == discord.MessageType.reply:
				replyMsg = message.reference.resolved
				replyContent = replyMsg.clean_content

				# Re formats content
				content = f"{content}<hr class='microgap'>\n\n_Original Message:_<br />\n > {replyContent}"
			
			# Appends markdown file with the content & context
			markdownLines.append(datestamp)
			markdownLines.append(content + "\n")

			# Works through attachments & embeds, appending to markdown
			for attachment in attached:
				if attachment.content_type.split("/")[0] == "image":
					filen = await imgDownload(self, attachment, str(message.id), assetsPath + pathDelim + "micro")
					markdownLines.append(f'<img src="/assets/micro/{filen}"><br />\n')
			for embed in embeds:
				if embed.type == "video" or embed.type == "gifv":
					markdownLines.append(f'<video controls> <source src="{embed.url}"> Your browser does not support the video tag. </video><br />\n')

			# Final horizontal line to divide posts
			markdownLines.append("---")

		# Writes markdown to path
		await writeTo(channelMD[channeltypes.index('MB')], markdownLines)
		print("Microblog Updated")
	except Exception as f:
		e = traceback.format_exc()
		await logToChannel(self,"Microblog","Microblog failed to update with the following exception\n" + e)
		print(e)		

async def aboutUpdate(self):
	try:
		channelID = channels[channeltypes.index('AB')]
		markdownPath = channelMD[channeltypes.index('AB')]
		channelData = self.get_channel(channelID)
		markdownLines = []
		async for message in channelData.history(limit=100):
			author = message.author.display_name
			attachment = message.attachments[0]
			filen = await imgDownload(self, attachment, author, assetsPath + pathDelim + "avatars")
			content = message.clean_content
			markdownLines.append("<div class=\"abtContainer\">")
			markdownLines.append(f'<div class="abtImage"><img src="/assets/avatars/{filen}" class="prof-img" alt="{author} display image"></div>')
			markdownLines.append(f'<div class="abtDesc">{content}</div>')
			markdownLines.append("</div>")
		await writeTo(markdownPath, markdownLines)
		print("About Updated")
	except Exception as f:
		e = traceback.format_exc()
		await logToChannel(self, "About Update", "About failed to update with the following exception\n" + e)
		print(e)

async def blogUpdate(self):
	try:
		# Connects to local SQLite DB, checks if posts table exists, creates if it doesn't.
		con = sqlite3.connect(sqlLiteDB)
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
		channelData = self.get_channel(channelID)

		# Creates temp posts directory for modification
		shutil.rmtree(tmpDir,ignore_errors=True)
		os.mkdir(tmpDir)

		slugs = set()
		async for message in channelData.history(limit=100):
			# Pulls metadata from message
			author = message.author.display_name
			msgID = message.id
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

			with open(fullPath + pathDelim + "content.md", 'r') as markdown:
				md = markdown.read()
			
			valuesToReplace = [(".png",".webp"),(".jpg",".webp"),(".jpeg",".webp")]
			for value in valuesToReplace:
				md = md.replace(value[0], value[1])
			
			await writeTo(fullPath + pathDelim + "content.md", md.split("\n"))

			# Pulls posttemplate file from assets into memory, makes changes, writes as index
			with open(assetsPath + pathDelim + "posttemplate.html", 'r') as template:
				html = template.read()
			
			valuesToReplace = [("{{title}}",title),("{{excerpt}}",excerpt),("{{author}}",author),("{{publishdate}}",published)]
			for value in valuesToReplace:
				html = html.replace (value[0],value[1])
			
			await writeTo(fullPath + pathDelim + "index.html", html.split("\n"))

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
			postbody.append(f"<a href=\"/blog/{post[0]}\">\n<div class=\"post\">") # Post's div wrapper
			postbody.append(f"<div class=\"posttitle\"><i>{publishdate}</i><h2>{post[1]}</h2></div>") # Heading info
			postbody.append(f"<div class=\"postexcerpt\"><p>{post[4]}</p></div>\n</div></a>\n") # Excerpt
			postbody.append("<div class=\"gap\"><hr></div>\n") # Gap div

		#Writes to file
		await writeTo(tmpDir + pathDelim + "index.html", html)
		await writeTo(assetsPath + pathDelim + "post-index.html", postbody)

		# Copies temp back into live folders & removes temp
		shutil.rmtree(postsDir)
		shutil.copytree(tmpDir,postsDir,symlinks=True)
		shutil.rmtree(tmpDir)

		print("Blog Updated")
	except Exception as f:
		e = traceback.format_exc()
		await logToChannel(self, "Blog Update", "Blog failed to update with the following exception\n" + e)
		print(e)

async def assetUpdate(self):
	try:
		channelID = channels[channeltypes.index('AS')]
		channelData = self.get_channel(channelID)

		uploads = []
		async for message in channelData.history():
			attachment = message.attachments[0]
			contentTyp = attachment.content_type.split("/")
			if contentTyp[0] == "image":
				fileName = await imgDownload(self, attachment, message.clean_content, uploadPath)
			else:
				fileName = message.clean_content + "." + contentTyp[1]
				fullPath = uploadPath + pathDelim + fileName
				if not os.path.exists(fullPath):
					await attachment.save(fp=fullPath)
			uploads.append(fileName)
		
		files = os.listdir(uploadPath)
		for file in files:
			if file not in uploads:
				os.remove(uploadPath + pathDelim + file)
		
		print("Assets Updated")
	except Exception as f:
		e = traceback.format_exc()
		await logToChannel(self,"Asset update", "Assets failed to update with the following exception\n" + e)
		print(e)

async def socialsUpdate(self):
	try: 
		# Connects to local SQLite DB, checks if socials table exists, creates if it doesn't.
		con = sqlite3.connect(sqlLiteDB)
		cur = con.cursor()
		tbl = cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='socials';")
		if len(tbl.fetchall()) == 0:
			cur.execute("CREATE TABLE socials (ID INTEGER NOT NULL PRIMARY KEY, category, rank, site, desc, usr, url, img);")
			con.commit()
			print("Created table")
		
		# Usual boilerplate to get appropriate channel, then run through messages
		channelID = channels[channeltypes.index('SC')]
		channelData = self.get_channel(channelID)
		messages = []
		async for message in channelData.history():
			# Finds the message ID, then checks the attachments. 
			# If there's only 1 attachment AND that attachment is an image, sets the attachment flag to true for later
			msgID = message.id
			messages.append(msgID)
			attach = message.attachments
			if len(attach) != 1 or attach[0].content_type.split("/")[0] != "image":
				attachment = False
			else:
				attachment = True
			msgContent = message.clean_content

			try:
				cur.execute(f"INSERT INTO socials (ID) VALUES ({msgID})")
			except:
				pass

			for meta in msgContent.split("\n"):
				typ = meta.split(": ")[0]
				content = meta.split(": ")[1]
				sqlUpd = ""
				match typ:
					# While dealing with inserting the site's data, tells the image to be downloaded.
					case "Site":
						if attachment:
							file = await imgDownload(self, attach[0], content.replace(".","_"), assetsPath + pathDelim + "avatars")
							img = f"/assets/avatars/{file}"
							sqlUpd = f"site = \"{content}\", img = \"{img}\""

						sqlCol = "site"
					
					# Below cases set the appropriate SQL column name based on message key
					case "Category":
						sqlCol = "category"
					case "Rank":
						sqlCol = "rank"
					case "Username":
						sqlCol = "usr"
					case "Link":
						sqlCol = "url"
					case "Description":
						sqlCol = "desc"
				
				if sqlUpd == "":
					sqlUpd = f"{sqlCol} = \"{content}\""
				cur.execute(f"UPDATE socials SET {sqlUpd} WHERE ID = {msgID}")

			con.commit()
		
		cur.execute("SELECT id FROM socials")
		allIDs = cur.fetchall()
		for sqlID in allIDs:
			if sqlID[0] not in messages:
				cur.execute(f"DELETE FROM socials WHERE id = {sqlID[0]}")
		con.commit()

		cur.execute("SELECT category, site, desc, usr, url, img FROM socials ORDER BY category, rank")
		allLinks = cur.fetchall()
		
		categories = []
		catCount = 0
		linkHTML = []
		for entry in allLinks:
			category = entry[0]
			site = entry[1]
			desc = entry[2]
			try:
				l = len(entry[3])
				usr = f"Username - {entry[3]}"
			except:
				usr = ""
			url = entry[4]
			img = entry[5]
			if category not in categories:
				categories.append(category)
				if catCount < len(categories) and catCount > 0:
					linkHTML.append("</div>")
				linkHTML.append(f"<hr><button type=\"button\" class=\"collapsible\">{category}</button>")
				linkHTML.append("<div class=\"collapse-content\">")
				catCount = catCount + 1
			table = f"""<hr> <a href="{url}">
<div class="fourtysixty stack">
<div class="first"> <img src="{img}" alt="{site} logo"> </div>
<div class="second"> <h2>{site}</h2> <h3><i>{usr}</i></h3> <p>{desc}</p> </div>
</div></a>
"""
			for l in table.split("\n"):
				linkHTML.append(l)
		linkHTML.append("</div>")

		with open(assetsPath + pathDelim + "socialtemplate.html", 'r') as socialIndex:
			indexHTML = socialIndex.read()
			lines = indexHTML.split("\n")
			repl = lines.index("{{REPLACE}}")
			pre = lines[0:repl]
			aft = lines[repl+1::]

		# Merges arrays around body text generated
		html = []
		html += pre 
		html += linkHTML
		html += aft
		await writeTo(htmlDir + pathDelim + "socials" + pathDelim + "index.html",html)	

		print("Socials Updated")
	
	except Exception as f:
		e = traceback.format_exc()
		await logToChannel(self,"Socials update", "Social update failed to update with the following exception\n" + e)
		print(e)

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
		await socialsUpdate(self)
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
	elif channeltypes[channels.index(msg.channel.id)] == "SC":
		await socialsUpdate(self)
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