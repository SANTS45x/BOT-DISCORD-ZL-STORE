import discord
from discord.ext import commands
from discord.ui import Button, View

TOKEN = "MTMzMjQ5MTY4ODg3NDA4MjM5NQ.GhGxpG.6O9gw7YLfLIb_Idt9xZdwnTC__7FrtkALIUWYU"
GUILD_ID = 1306222797068046416
SUB_FUNDADORES_ID = 1306223901805907969
FUNDADOR_ID = 1306223900950007879
TICKET_CHANNEL_ID = 1309703980179525824  # Categoria onde o ticket será criado
CLIENT_ROLE_ID = 1307147233019559967  # ID do cargo "🎉Cliente"
EVALUATION_CHANNEL_ID = 1310987625150283816  # Canal onde a avaliação será enviada
LOG_CHANNEL_ID = 1332371378694918147  # Canal de log para eventos

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def log_event(message):
    """Função para logar eventos no canal de logs"""
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(message)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒COMPRAR", style=discord.ButtonStyle.green)
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category_channel = bot.get_channel(TICKET_CHANNEL_ID)  # Categoria onde o ticket será criado
        
        # Verifique se a categoria existe
        if isinstance(category_channel, discord.CategoryChannel):
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),  # Todos os membros não podem ver o canal
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),  # O criador do ticket pode
                guild.get_role(SUB_FUNDADORES_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),  # Sub-fundadores podem ver
                guild.get_role(FUNDADOR_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),  # Fundadores podem ver
                guild.get_role(1306223900950007879): discord.PermissionOverwrite(view_channel=True, send_messages=True),  # Novo cargo com permissão
                guild.get_member(1248299566516666429): discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)  # Permissão total para o usuário específico
            }
            # Crie o canal de texto dentro da categoria
            ticket = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites, category=category_channel)
            
            # Crie um embed com a imagem do QR code
            embed = discord.Embed(
                title="QR Code de Pagamento",
                description="Aqui está o QR Code para realizar o pagamento. Depois do pagamento fale o nome do produto que comprou",
                color=discord.Color.blue()
            )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1346171101646164000/1346171504404070454/qrcode-pix_3.png?ex=67c73769&is=67c5e5e9&hm=d7637aea52392abb41751cb64f349e87eb49b097307677f9be17bc5423a97ed0&")
            
            # Menciona o usuário que criou o ticket
            await ticket.send(f"{interaction.user.mention}, aqui está o QR Code para o pagamento.", embed=embed, view=ApproveCloseView())
            try:
                await interaction.response.send_message(f"Ticket criado: {ticket.mention}", ephemeral=True)  # Mostra o canal de ticket criado para o usuário
            except discord.errors.NotFound:
                print("Erro: A interação já expirou ou foi deletada antes da resposta.")
                
            # Log da ação
            await log_event(f"Ticket criado por {interaction.user.mention} no canal {ticket.mention}")

        else:
            await interaction.response.send_message("A categoria de tickets não foi encontrada.", ephemeral=True)

class ApproveCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.blurple)
    async def approve(self, interaction: discord.Interaction, button: Button):
        # Verifica se o usuário tem o cargo necessário para aprovar
        if any(role.id in [SUB_FUNDADORES_ID, FUNDADOR_ID, 1306223900950007879] for role in interaction.user.roles):
            # Adiciona o cargo @🎉Cliente ao criador do ticket somente após a aprovação
            member = interaction.guild.get_member_named(interaction.channel.name.split("-")[1])  # Pegando o usuário pelo nome
            client_role = interaction.guild.get_role(CLIENT_ROLE_ID)
            if member and client_role:
                await member.add_roles(client_role)  # Adiciona o cargo
                await interaction.response.send_message(f"Compra aprovada por {interaction.user.mention}!", ephemeral=True)
                await interaction.channel.send(f"Compra aprovada por {interaction.user.mention}! {member.mention}, você agora tem o cargo {client_role.name}.")
                
                # Envia uma mensagem em embed para o usuário em DM
                embed = discord.Embed(
                    title="Compra Aprovada",
                    description=f"Sua compra foi aprovada! Você agora possui o cargo '🎉Cliente'.",
                    color=discord.Color.green()
                )
                embed.set_image(url="https://cdn.discordapp.com/attachments/845429243697430548/1339737970286002228/4617bdbb13507ab1085e69c1355bb6e3.gif?ex=67c6e1f7&is=67c59077&hm=0e1e19d93ff3361b27cffd4ff333ea6108046d438f47c8d303f679a24475cfe1&")
                
                # Envia o embed e os botões de avaliação para o usuário via DM
                await member.send(embed=embed, view=EvaluationView())
                
                # Log da aprovação
                await log_event(f"Compra aprovada por {interaction.user.mention} para {member.mention} no canal {interaction.channel.mention}")
        else:
            await interaction.response.send_message("Você não tem permissão para aprovar.", ephemeral=True)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # Verifica se o usuário tem o cargo necessário para fechar o ticket
        if any(role.id in [SUB_FUNDADORES_ID, FUNDADOR_ID, 1306223900950007879] for role in interaction.user.roles):
            await interaction.channel.delete()

            # Log do fechamento do ticket
            await log_event(f"Ticket fechado por {interaction.user.mention} no canal {interaction.channel.mention}")
        else:
            await interaction.response.send_message("Você não tem permissão para fechar este ticket.", ephemeral=True)

class EvaluationView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="1 ⭐", style=discord.ButtonStyle.secondary, custom_id="1_star")
    async def rate_1(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 1)

    @discord.ui.button(label="2 ⭐⭐", style=discord.ButtonStyle.secondary, custom_id="2_stars")
    async def rate_2(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 2)

    @discord.ui.button(label="3 ⭐⭐⭐", style=discord.ButtonStyle.secondary, custom_id="3_stars")
    async def rate_3(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 3)

    @discord.ui.button(label="4 ⭐⭐⭐⭐", style=discord.ButtonStyle.secondary, custom_id="4_stars")
    async def rate_4(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 4)

    @discord.ui.button(label="5 ⭐⭐⭐⭐⭐", style=discord.ButtonStyle.secondary, custom_id="5_stars")
    async def rate_5(self, interaction: discord.Interaction, button: Button):
        await self.handle_rating(interaction, 5)

    async def handle_rating(self, interaction: discord.Interaction, rating: int):
        # Envia a avaliação do usuário para o canal de avaliação
        evaluation_channel = bot.get_channel(EVALUATION_CHANNEL_ID)
        embed = discord.Embed(
            title="Avaliação de Compra",
            description=f"O usuário {interaction.user.mention} avaliou a compra com {rating} estrelas.",
            color=discord.Color.gold()
        )
        await evaluation_channel.send(embed=embed)

        # Envia mensagem de confirmação para o usuário
        await interaction.response.send_message(f"Obrigado pela sua avaliação de {rating} estrelas!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.command()
async def setup(ctx):
    view = TicketView()
    await ctx.send("", view=view)

bot.run(TOKEN)
