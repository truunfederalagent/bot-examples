from discord.ext import commands
import discord
from discord.utils import get
import re, os
from moody_helper import MoodyHelper
from moody_db import MoodyDB

bot = commands.Bot("#", help_command=None)
helper = MoodyHelper()
db = MoodyDB()
ROLE_NAME = 'Beast-Holder'

@bot.command(name='register', pass_context = True)
async def register_wallet(ctx, wallet):
    if not re.match(r'[A-Z0-9]{58}', wallet):
        await ctx.channel.send('That is not a valid wallet address')
        return
    member = ctx.author
    user_id = str(member.id)
    if db.is_registered(wallet):
        if db.check_registration(user_id, wallet):
            await ctx.channel.send(f'Wallet already registered to {member.display_name}')
        else:
            await ctx.channel.send(f'Wallet registered to a different user')

    else:
        if helper.get_moody_asset_count(wallet) > 0:
            role = get(member.guild.roles, name = ROLE_NAME)
            db.add_registration(user_id, wallet)
            await member.add_roles(role)
            await ctx.channel.send(f'Wallet Registered for {member.display_name}')
        else:
            await ctx.channel.send(f'Wallet holds no MoodyBeasts')

@bot.command(name='unregister', pass_context = True)
async def register_wallet(ctx):  
    member = ctx.author
    db.remove_registrations(member.id)
    role = get(member.guild.roles, name = ROLE_NAME)
    await member.remove_roles(role)
    await ctx.channel.send(f'Unregistering all wallets for {member.display_name}')

@bot.command(name='status')
async def check_status(ctx):
    member = ctx.author
    user_id = str(member.id)
    wallets = db.get_registrations(user_id)
    if wallets > 0:
        await ctx.channel.send(f'{member.display_name} has {wallets} wallet{"s"*(wallets > 1)}')
    else:
        await ctx.channel.send(f'{member.display_name} has no associated wallets')

@bot.command(name='help', pass_context=True)
async def send_help(ctx):
    embed = discord.Embed(title= 'Help')
    embed.add_field(name='Register', value='#register [wallet]\nWallet must currently hold\na Moody Beast.\nUser can register multiple wallets')
    embed.add_field(name='Unegister', value='#unregister\nRemoves all wallets associated with user.')
    await ctx.channel.send(embed=embed)

TOKEN = os.environ.get('MOODY_TOKEN')
bot.run(TOKEN)