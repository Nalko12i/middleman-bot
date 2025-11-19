import os
import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

# -------- CONFIG --------
GUILD_ID = 1439330695490179144
TICKET_CHANNEL_ID = 1440432450495971490
TICKET_CATEGORY_ID = 1440432209596252260
MIDDLEMAN_ROLE_ID = 1440387845624827924
OWNER_ROLE_ID = 1440386159414083594
COOWNER_ROLE_ID = 1440386315832131654
MANAGER_ROLE_ID = 1440390070484865094

# -------- INTENTS --------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ========== TICKET VIEW ==========
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Request a Middleman", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        # Check if user already has a ticket
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message("You already have an open ticket!", ephemeral=True)
            return

        # Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(MIDDLEMAN_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(COOWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(MANAGER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        # Create channel
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        # Embed + buttons
        ticket_embed = discord.Embed(
            title="Ticket Created",
            description=f"Ticket opened by {interaction.user.mention}",
            color=discord.Color.green()
        )

        claim_button = Button(
            label="Claim Ticket",
            style=discord.ButtonStyle.success,
            custom_id=f"claim_ticket_{interaction.user.id}"
        )

        close_button = Button(
            label="Close Ticket",
            style=discord.ButtonStyle.danger,
            custom_id=f"close_ticket_{interaction.user.id}"
        )

        ticket_view = View()
        ticket_view.add_item(claim_button)
        ticket_view.add_item(close_button)

        # CALLBACK: CLAIM
        async def claim_callback(i: discord.Interaction):
            member = i.user
            mm_role = guild.get_role(MIDDLEMAN_ROLE_ID)

            if mm_role not in member.roles:
                await i.response.send_message("Only Middleman role can claim tickets!", ephemeral=True)
                return

            await ticket_channel.set_permissions(member, view_channel=True, send_messages=True)
            await i.response.send_message(f"{member.mention} claimed this ticket!", ephemeral=False)

        # CALLBACK: CLOSE
        async def close_callback(i: discord.Interaction):
            await i.response.send_message("Closing ticket in 5 seconds...", ephemeral=False)
            await asyncio.sleep(5)
            await ticket_channel.delete()

        claim_button.callback = claim_callback
        close_button.callback = close_callback

        await ticket_channel.send(
            content=interaction.user.mention,
            embed=ticket_embed,
            view=ticket_view
        )

        await interaction.response.send_message(
            f"Your ticket has been created: {ticket_channel.mention}",
            ephemeral=True
        )


# ========== ON READY ==========
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")

    # Keep buttons active after restart
    bot.add_view(TicketView())

    # Auto-send embed if not already sent
    channel = bot.get_channel(TICKET_CHANNEL_ID)

    already_exists = False
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and len(msg.components) > 0:
            already_exists = True
            break

    if not already_exists:
        embed = discord.Embed(
            title="Request a Middleman",
            description="Click the button below to open a ticket.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=TicketView())


# -------- RUN BOT --------
TOKEN = os.getenv("TOKEN")  # TOKEN PRIDE IZ RAILWAY (VARIABLES)
bot.run(TOKEN)
