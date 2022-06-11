from discord.ext import commands
import discord
from discord.utils import get
import re, os, random, json
import meta_wallet_checker as checker
from meta_db import MetaDB

BEAN = 523139396044587009
bot = commands.Bot("+", help_command=None)
db = MetaDB()

with open('numbered-assets.json') as f:
    numbered = json.loads(f.read())

def get_display_element(element):
    num = '#'+ numbered[element]
    return f'{num} {element}'

@bot.command(name='register', pass_context = True)
async def register_wallet(ctx, wallet):
    if 'shuffle' not in ctx.channel.name: return
    if not re.match(r'[A-Z0-9]{58}', wallet):
        await ctx.author.send('That is not a valid wallet address')
        return
    member = ctx.author
    user_id = str(member.id)
    if db.user_is_registered(user_id):
        await member.send(f'You have already registered a wallet. If you would like to register a new one, please use +unregister first.')
    elif db.is_registered(wallet):
        if db.check_registration(user_id, wallet):
            await member.send(f'Wallet already registered to {member.display_name}')
        else:
            await member.send(f'Wallet registered to a different user')
    else:
        tickets = checker.get_tickets(wallet)
        db.add_registration(user_id, wallet)
        await ctx.author.send(f'Wallet Registered for {member.display_name} with {tickets} tickets')
        

@bot.command(name='unregister', pass_context = True)
async def register_wallet(ctx):
    if 'shuffle' not in ctx.channel.name: return  
    member = ctx.author
    db.remove_registrations(member.id)
    await member.send(f'{member.display_name} has been removed from the shuffle')

@bot.command(name='status')
async def check_status(ctx):
    if 'shuffle' not in ctx.channel.name: return
    member = ctx.author
    if member.id == BEAN:
        stats = await get_stats_string()
        await member.send(stats)
    else:
        user_id = str(member.id)
        wallet = db.get_wallet_by_user(user_id)
        print(wallet)
        if wallet != None:
            tickets = checker.get_tickets(wallet) 
            await member.send(f'You have {tickets} ticket' + 's'*(tickets > 1))
        else:
            await member.send(f'You are not registered for the shuffle')


@bot.command(name='shuffle')
@commands.has_role('ADMIN')
async def get_shuffle_winner(ctx, num_winners = 1):
    if 'shuffle' not in ctx.channel.name: return
    winners = await get_winners(int(num_winners))
    winner_string = ' '.join([f'<@{winner}>' for winner in winners])
    await ctx.channel.send(f'Congratulations to ' + winner_string)

@bot.command(name='testshuffle')
@commands.has_role('ADMIN')
async def get_shuffle_winner(ctx, num_winners = 1):
    if 'shuffle' not in ctx.channel.name: return
    winners = await get_winners(int(num_winners))
    message = await get_stats_string()
    await ctx.author.send(message)
    winner_string = ' '.join([f'<@{winner}>' for winner in winners])
    
    await ctx.author.send(f'Congratulations to ' + winner_string)


@bot.command(name='clear')
@commands.has_role('ADMIN')
async def clear_recent_winners(ctx):
    if 'shuffle' not in ctx.channel.name: return
    db.clear_recent_winners()

@bot.command(name='tickets')
@commands.has_role('ADMIN')
async def get_tickets_for_user(ctx, user):
    if 'shuffle' not in ctx.channel.name: return
    pattern = r'<@(\d+)>'
    if re.match(pattern, user):
        user_id = re.search(pattern, user).group(1)
    wallet = db.get_wallet_by_user(user_id)
    if wallet != None:
        tickets = checker.get_tickets(wallet)
        await ctx.channel.send(f'User has {tickets} tickets')
    else:
        await ctx.channel.send('User is not registered')

@bot.command(name='stackers')
@commands.has_role('ADMIN')
async def get_stackers(ctx):
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    stackers = []
    for user_id, wallet, stacks, num in tickets:
        if num > 1:
            stackers.append(user_id)

    await ctx.channel.send('All stackers: ' + ', '.join([f'<@{stacker}>' for stacker in stackers]))
    

@bot.command(name='stackersdm')
@commands.has_role('ADMIN')
async def get_stackers_dm(ctx):
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    stackers = []
    for user_id, wallet, stacks, num in tickets:
        if num > 1:
            stackers.append(user_id)

    await ctx.author.send('All stackers: ' + ', '.join([f'<@{stacker}>' for stacker in stackers]))

@bot.command(name='stackershuffle')
@commands.has_role('ADMIN')
async def get_stackers(ctx):
    
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    stackers = []
    for user_id, wallet, stacks, num in tickets:
        if num > 1:
            stackers.append(user_id)
    past_winners = set(db.get_recent_winners())
    winner = random.choice(stackers)
    while winner in past_winners:
        winner = winner = random.choice(stackers)
       
    await ctx.channel.send(f'Congratulations, <@{winner}>. You won the stacker shuffle.')

@bot.command(name='walletsearch')
async def get_stackers(ctx, start):
    if 'shuffle-giveaway' not in ctx.channel.name: return
    user_id = db.get_user_from_partial_wallet(start)
    if user_id == None:
        await ctx.channel.send('Wallet not found')
    else:
        user = await bot.fetch_user(int(user_id))
        await ctx.channel.send(f'Walllet belongs to {user.display_name}')


@bot.command(name='leaderboard')
@commands.has_role('ADMIN')
async def get_leaders(ctx):
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    stackers = []
    for user_id, wallet, stacks, num in tickets:
        if num > 1:
            stackers.append((user_id, num, stacks))

    stackers.sort(key=lambda p: p[1], reverse=True)
    leaders = ''
    for i in range(5):
        user_id, tickets, stacks = stackers[i]
        leaders += f'<@{user_id}> - {tickets} tickets`\n{", ".join(map(get_display_element, sorted(stacks)))}`\n'

    if stackers[4][1] == stackers[5][1] and stackers[5][1] != stackers[-1][1]:
        i = 5
        while stackers[i][1] == stackers[4][1]:
            user_id, tickets, stacks = stackers[i]
            leaders += f'<@{user_id}> - {tickets} tickets`\n{", ".join(map(get_display_element, sorted(stacks)))}`\n'
            i += 1

    await ctx.channel.send(leaders[:-1])

@bot.command(name='leaderboarddm')
@commands.has_role('ADMIN')
async def get_leaders(ctx):
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    stackers = []
    for user_id, wallet, stacks, num in tickets:
        if num > 1:
            stackers.append((user_id, num, stacks))

    stackers.sort(key=lambda p: p[1], reverse=True)
    leaders = ''
    for i in range(5):
        user_id, tickets, stacks = stackers[i]
        leaders += f'<@{user_id}> - {tickets} tickets\n`{", ".join(map(get_display_element, sorted(stacks)))}`\n'

    if stackers[4][1] == stackers[5][1] and stackers[5][1] != stackers[-1][1]:
        i = 5
        while stackers[i][1] == stackers[4][1]:
            user_id, tickets, stacks = stackers[i]
            leaders += f'<@{user_id}> - {tickets} tickets\n`{", ".join(map(get_display_element, sorted(stacks)))}`\n'
            i += 1

    await ctx.author.send(leaders[:-1])

@bot.command(name='remove')
@commands.has_role('ADMIN')
async def remove(ctx, user):
    if 'shuffle' not in ctx.channel.name: return
    pattern = r'<@(\d+)>'
    if re.match(pattern, user):
        user_id = re.search(pattern, user).group(1)
        print(user_id)
        db.remove_registrations(user_id)

@bot.command(name='stats')
async def get_stats(ctx):
    if 'shuffle' not in ctx.channel.name: return
    message = await get_stats_string()
    await ctx.channel.send(message)

async def get_stats_string():
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    message = f'Registrants: {len(tickets)}\n'
    entries = []
    biggest = 0
    user_stacks = 0
    total_stacks = 0
    for user_id, wallet, all_stacks, num in tickets:
        entries += [user_id] * num
        user_stacks += num > 1
        total_stacks += len(all_stacks)
        biggest = max(biggest, num)
    message += f'Tickets: {len(entries)}\n'
    message += f'Users with stacks: {user_stacks}\n'
    message += f'Metas stacked: {total_stacks}\n'
    message += f'Most tickets held: {biggest}'
    return message


async def get_winners(num_winners):
    users = db.get_all_users()
    tickets = checker.get_all_tickets(users)
    entries = []
    for user_id, wallet, stacks, num in tickets:
        entries += [user_id] * num
    past_winners = set(db.get_recent_winners())
    winners = set()
    while len(winners) < num_winners:
        winner = random.randint(0, len(entries)-1)
        if entries[winner] not in winners | past_winners:
            current_winner = entries.pop(winner)
            winners.add(current_winner)

    return winners


TOKEN = os.environ.get('META_TOKEN')
bot.run(TOKEN)