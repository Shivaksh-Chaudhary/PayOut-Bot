import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ui
import requests
from PIL import Image
from io import BytesIO
import json
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID'))
ROLE_IDS = [int(role_id) for role_id in os.getenv('ROLE_IDS').split(',')]

intents = nextcord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(status=nextcord.Status.dnd, activity=nextcord.Activity(type=nextcord.ActivityType.playing, name="with accounts"))

def get_player_skin(gametag):
    response = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{gametag}')
    if response.status_code == 200:
        uuid = response.json().get('id')
        if uuid:
            skin_url = f'https://crafatar.com/skins/{uuid}'
            return skin_url
    return None

def extract_and_flatten_head(skin_url):
    response = requests.get(skin_url)
    if response.status_code == 200:
        skin = Image.open(BytesIO(response.content))
        head = skin.crop((8, 8, 16, 16))
        head = head.resize((128, 128), Image.NEAREST)
        return head
    return None

async def upload_head_image(head_image):
    with BytesIO() as image_binary:
        head_image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return nextcord.File(fp=image_binary, filename='head.png')

class AccountDetailsModal(ui.Modal):
    def __init__(self, user):
        super().__init__(title="Enter Account Details")
        self.user = user
        self.email = ui.TextInput(label="Email", required=True)
        self.password = ui.TextInput(label="Password", required=True)
        self.gametag = ui.TextInput(label="GameTag (Minecraft Username)", required=True)
        self.add_item(self.email)
        self.add_item(self.password)
        self.add_item(self.gametag)

    async def callback(self, interaction: Interaction):
        email = self.email.value
        password = self.password.value
        gametag = self.gametag.value
        skin_url = get_player_skin(gametag)
        if skin_url:
            head_image = extract_and_flatten_head(skin_url)
            if head_image:
                head_file = await upload_head_image(head_image)
                embed = nextcord.Embed(title="IMPACT GAMING PAYOUT", color=0x00ff00)
                embed.set_thumbnail(url="attachment://head.png")
                embed.add_field(name="Email", value=email, inline=False)
                embed.add_field(name="Password", value=password, inline=False)
                embed.add_field(name="GameTag", value=gametag, inline=False)
                embed.add_field(name="First Login", value="N/A", inline=False)
                embed.add_field(name="Last Login", value="N/A", inline=False)
                embed.add_field(name="Optifine Cape", value="No", inline=False)
                embed.add_field(name="Capes", value="None", inline=False)
                embed.add_field(name="Skyblock Coins", value="N/A", inline=False)
                embed.add_field(name="Bedwars Stars", value="N/A", inline=False)
                embed.add_field(name="Banned", value="No", inline=False)
                embed.add_field(name="Can Change Name", value="Yes", inline=False)

                await self.user.send(embed=embed, file=head_file)
                await self.user.send("<a:Special_heart:1327612249485086720>  VOUCH <@1305505649018277908> IN https://discord.com/channels/1166060075882913883/1313429397696413706 OR GET BAN <:ban_pan:1327612292807917578>")
                await interaction.response.send_message(f'Credentials sent to {self.user.mention}.', ephemeral=True)

                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"Payout sent to {self.user.mention} for GameTag: {gametag}")
            else:
                await interaction.response.send_message(f'Could not process the head image for {gametag}.', ephemeral=True)
        else:
            await interaction.response.send_message(f'Could not fetch the skin for {gametag}.', ephemeral=True)

@bot.slash_command(guild_ids=[GUILD_ID], description="Send account details to a user via a form")
async def send_credentials(interaction: Interaction, user: nextcord.Member):
    if not any(role.id in ROLE_IDS for role in interaction.user.roles):
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    modal = AccountDetailsModal(user)
    await interaction.response.send_modal(modal)

bot.run(TOKEN)
