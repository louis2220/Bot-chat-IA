import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import platform

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ajuda", description="📋 Mostra todos os comandos disponíveis")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 RevolutX: Comandos",
            description="Fala, galera! Aqui estão todos os meus comandos! 🚀✨",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="💬 Chat com IA",
            value=(
                "`/chat` — Conversa comigo!\n"
                "`/limpar-conversa` — Reseta o histórico\n"
                "`/canal-ia` — Define canal de IA automática *(Admin)*\n"
                "📌 *Me marque ou responda minhas msgs também!*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛡️ Moderação",
            value=(
                "`/ban` — Bane um usuário\n"
                "`/kick` — Expulsa um usuário\n"
                "`/mute` — Silencia temporariamente\n"
                "`/unmute` — Remove silenciamento\n"
                "`/warn` — Avisa um usuário\n"
                "`/avisos` — Ver avisos de alguém\n"
                "`/limpar-avisos` — Remove avisos\n"
                "`/purge` — Deleta mensagens em massa\n"
                "`/palavra-proibida` — Gerencia palavras banidas\n"
                "`/config-mod` — Configura moderação *(Admin)*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Anti-Raid",
            value=(
                "`/lockdown` — Ativa/desativa lockdown\n"
                "`/config-antiraid` — Configura proteção\n"
                "`/status-seguranca` — Status do servidor"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🤝 Parcerias",
            value=(
                "`/parceria` — Solicita parceria automática\n"
                "`/parceiros` — Lista parceiros\n"
                "`/anunciar-parceria` — Anuncia parceria *(Admin)*\n"
                "`/config-parceria` — Configura sistema *(Admin)*"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Utilidades",
            value=(
                "`/userinfo` — Info de um usuário\n"
                "`/serverinfo` — Info do servidor\n"
                "`/avatar` — Avatar de alguém\n"
                "`/ping` — Latência do bot\n"
                "`/ajuda` — Esta mensagem"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="RevolutX Bot • Use /chat para falar comigo! 😄")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="🏓 Mostra a latência do bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        status = "🟢 Ótimo" if latency < 100 else "🟡 Normal" if latency < 200 else "🔴 Alto"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"**Latência:** `{latency}ms` {status}",
            color=discord.Color.green() if latency < 100 else discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="👤 Mostra informações de um usuário")
    @app_commands.describe(membro="Usuário para ver informações (padrão: você)")
    async def userinfo(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        
        roles = [r.mention for r in reversed(membro.roles) if r.name != "@everyone"]
        roles_text = ", ".join(roles[:10]) if roles else "Nenhum"
        if len(roles) > 10:
            roles_text += f" e mais {len(roles) - 10}..."
        
        embed = discord.Embed(
            title=f"👤 {membro.display_name}",
            color=membro.color if membro.color != discord.Color.default() else discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        
        embed.add_field(name="🏷️ Tag", value=str(membro), inline=True)
        embed.add_field(name="🆔 ID", value=f"`{membro.id}`", inline=True)
        embed.add_field(name="🤖 Bot?", value="Sim" if membro.bot else "Não", inline=True)
        embed.add_field(
            name="📅 Conta Criada",
            value=f"<t:{int(membro.created_at.timestamp())}:D>\n<t:{int(membro.created_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(
            name="📥 Entrou no Servidor",
            value=f"<t:{int(membro.joined_at.timestamp())}:D>\n<t:{int(membro.joined_at.timestamp())}:R>",
            inline=True
        )
        embed.add_field(name="🎭 Cargos", value=roles_text, inline=False)
        
        if membro.premium_since:
            embed.add_field(
                name="💎 Boost desde",
                value=f"<t:{int(membro.premium_since.timestamp())}:D>",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="🌐 Mostra informações do servidor")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"🌐 {guild.name}",
            color=discord.Color.purple(),
            timestamp=datetime.now(timezone.utc)
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots
        
        embed.add_field(name="🆔 ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Dono", value=guild.owner.mention if guild.owner else "?", inline=True)
        embed.add_field(
            name="📅 Criado em",
            value=f"<t:{int(guild.created_at.timestamp())}:D>",
            inline=True
        )
        embed.add_field(
            name="👥 Membros",
            value=f"Total: **{guild.member_count}**\n👤 Humanos: **{humans}**\n🤖 Bots: **{bots}**",
            inline=True
        )
        embed.add_field(
            name="📊 Canais",
            value=(
                f"💬 Texto: **{len(guild.text_channels)}**\n"
                f"🔊 Voz: **{len(guild.voice_channels)}**\n"
                f"📁 Categorias: **{len(guild.categories)}**"
            ),
            inline=True
        )
        embed.add_field(name="🎭 Cargos", value=f"**{len(guild.roles)}** cargos", inline=True)
        embed.add_field(
            name="🔒 Verificação",
            value=str(guild.verification_level).replace("_", " ").title(),
            inline=True
        )
        embed.add_field(
            name="💎 Boost",
            value=f"Nível **{guild.premium_tier}** | **{guild.premium_subscription_count}** boosts",
            inline=True
        )
        
        if guild.emojis:
            embed.add_field(name="😄 Emojis", value=f"**{len(guild.emojis)}** emojis", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="🖼️ Mostra o avatar de um usuário")
    @app_commands.describe(membro="Usuário para ver o avatar (padrão: você)")
    async def avatar(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ Avatar de {membro.display_name}",
            color=discord.Color.purple()
        )
        embed.set_image(url=membro.display_avatar.url)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="🔗 Abrir em tamanho original",
            url=membro.display_avatar.url,
            style=discord.ButtonStyle.link
        ))
        
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="botinfo", description="🤖 Informações sobre o bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 Cordyx Bot",
            description="Bot brasileiro com IA, moderação avançada e muito mais! 🚀",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="🌐 Servidores", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="👥 Usuários", value=str(sum(g.member_count for g in self.bot.guilds)), inline=True)
        embed.add_field(name="🏓 Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="📚 discord.py", value=discord.__version__, inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
