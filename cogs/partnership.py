import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import Optional
from utils.database import db

class Partnership(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending = {}  # fluxo de DM em memória (temporário por natureza)

    async def get_config(self, guild_id: int) -> dict:
        row = await db.pool.fetchrow("SELECT * FROM partnership_config WHERE guild_id = $1", guild_id)
        if row:
            return dict(row)
        await db.pool.execute("INSERT INTO partnership_config (guild_id) VALUES ($1) ON CONFLICT DO NOTHING", guild_id)
        return await self.get_config(guild_id)

    async def save_config(self, guild_id: int, **kwargs):
        sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(kwargs))
        await db.pool.execute(f"UPDATE partnership_config SET {sets} WHERE guild_id = $1", guild_id, *kwargs.values())

    @app_commands.command(name="parceria", description="🤝 Inicia o processo de parceria automática")
    async def start_partnership(self, interaction: discord.Interaction):
        await interaction.response.send_message("📩 Vou te enviar as instruções no privado!", ephemeral=True)
        embed = discord.Embed(
            title="🤝 Sistema de Parcerias Automáticas",
            description="Vamos iniciar o processo de parceria **100% automático**! 🚀\n\nPreciso de algumas informações do seu servidor:",
            color=discord.Color.purple()
        )
        embed.add_field(name="📋 O que você vai precisar", value="✅ Convite permanente do seu servidor\n✅ Descrição do servidor (mínimo 50 caracteres)\n✅ Print do bot Cordyx no seu servidor\n✅ Mínimo de 50 membros", inline=False)
        try:
            dm = await interaction.user.create_dm()
            await dm.send(embed=embed)
            await dm.send("📎 **Passo 1/3:** Mande o **link de convite permanente** do seu servidor:")
        except discord.Forbidden:
            await interaction.followup.send("❌ Não consigo te enviar DM! Ativa as mensagens diretas.", ephemeral=True)
            return
        self.pending[interaction.user.id] = {"step": 1, "guild_id": interaction.guild_id, "data": {}}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild or message.author.bot:
            return
        user_id = message.author.id
        if user_id not in self.pending:
            return
        state = self.pending[user_id]
        step = state["step"]
        dm = message.channel

        if step == 1:
            invite = message.content.strip()
            if "discord.gg/" not in invite and "discord.com/invite/" not in invite:
                await dm.send("❌ Link inválido! Manda um link de convite do Discord:")
                return
            state["data"]["invite"] = invite
            state["step"] = 2
            await dm.send("✅ Link recebido!\n\n📝 **Passo 2/3:** Mande a **descrição do seu servidor** (mínimo 50 caracteres):")

        elif step == 2:
            desc = message.content.strip()
            if len(desc) < 50:
                await dm.send(f"❌ Descrição muito curta! ({len(desc)}/50). Tenta de novo:")
                return
            state["data"]["description"] = desc
            state["step"] = 3
            await dm.send("✅ Descrição recebida!\n\n🖼️ **Passo 3/3:** Mande um **print** mostrando que o bot Cordyx está no seu servidor:")

        elif step == 3:
            if not message.attachments:
                await dm.send("❌ Preciso de um print! Manda uma imagem:")
                return
            state["data"]["proof_url"] = message.attachments[0].url
            await dm.send("✅ Verificando sua solicitação... ⏳")
            await self.process_partnership_request(message.author, state, dm)

        self.pending[user_id] = state

    async def process_partnership_request(self, user: discord.User, state: dict, dm: discord.DMChannel):
        guild_id = state["guild_id"]
        guild = self.bot.get_guild(guild_id)
        if not guild:
            await dm.send("❌ Servidor não encontrado! Tente novamente.")
            del self.pending[user.id]
            return

        invite = state["data"]["invite"]
        # Verifica se já é parceiro
        existing = await db.pool.fetchrow("SELECT id FROM partners WHERE guild_id=$1 AND invite=$2", guild_id, invite)
        if existing:
            await dm.send("⚠️ Seu servidor já é parceiro!")
            del self.pending[user.id]
            return

        await db.pool.execute(
            "INSERT INTO partners (guild_id, invite, description, proof_url, added_by) VALUES ($1,$2,$3,$4,$5)",
            guild_id, invite, state["data"]["description"], state["data"]["proof_url"], user.id
        )

        config = await self.get_config(guild_id)
        channel_id = config.get("ad_channel") or config.get("partner_channel")
        if channel_id:
            channel = guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(title="🤝 Nova Parceria!", description=state["data"]["description"], color=discord.Color.purple(), timestamp=datetime.now(timezone.utc))
                embed.add_field(name="🔗 Convite", value=invite, inline=False)
                embed.set_footer(text=f"Parceria aprovada automaticamente • Solicitado por {user}")
                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="🚀 Entrar no Servidor", url=invite, style=discord.ButtonStyle.link))
                await channel.send(embed=embed, view=view)

        success_embed = discord.Embed(title="✅ Parceria Aprovada!", description=f"Seu servidor foi divulgado em **{guild.name}**! 🎉🚀✨", color=discord.Color.green())
        await dm.send(embed=success_embed)
        del self.pending[user.id]

    @app_commands.command(name="config-parceria", description="⚙️ Configura o sistema de parcerias [ADMIN]")
    @app_commands.describe(canal_parceiros="Canal onde as parcerias são divulgadas", membros_minimos="Mínimo de membros")
    @app_commands.default_permissions(administrator=True)
    async def config_partnership(self, interaction: discord.Interaction,
                                  canal_parceiros: Optional[discord.TextChannel] = None,
                                  membros_minimos: Optional[int] = None):
        await self.get_config(interaction.guild_id)
        updates = {}
        if canal_parceiros:
            updates["ad_channel"] = canal_parceiros.id
            updates["enabled"] = True
        if membros_minimos is not None:
            updates["min_members"] = membros_minimos
        if updates:
            await self.save_config(interaction.guild_id, **updates)
        config = await self.get_config(interaction.guild_id)
        embed = discord.Embed(title="✅ Parcerias Configuradas!", color=discord.Color.green())
        embed.add_field(name="Canal", value=f"<#{config['ad_channel']}>" if config.get("ad_channel") else "Não definido", inline=True)
        embed.add_field(name="Mín. Membros", value=str(config.get("min_members", 50)), inline=True)
        embed.add_field(name="Status", value="✅ Ativo" if config.get("enabled") else "❌ Inativo", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="parceiros", description="📋 Lista todos os parceiros do servidor")
    async def list_partners(self, interaction: discord.Interaction):
        rows = await db.pool.fetch(
            "SELECT invite, description, added_at FROM partners WHERE guild_id=$1 ORDER BY added_at DESC LIMIT 10",
            interaction.guild_id
        )
        if not rows:
            await interaction.response.send_message("❌ Nenhum parceiro cadastrado ainda!", ephemeral=True)
            return
        embed = discord.Embed(title=f"🤝 Parceiros de {interaction.guild.name}", description=f"Total: **{len(rows)}** parceiros", color=discord.Color.purple())
        for i, r in enumerate(rows, 1):
            embed.add_field(name=f"{i}. Parceiro", value=f"🔗 {r['invite']}\n📝 {r['description'][:80]}...", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="anunciar-parceria", description="📢 Posta o embed de parceria manualmente [ADMIN]")
    @app_commands.describe(convite="Link de convite", descricao="Descrição do servidor parceiro")
    @app_commands.default_permissions(administrator=True)
    async def announce_partnership(self, interaction: discord.Interaction, convite: str, descricao: str):
        config = await self.get_config(interaction.guild_id)
        ch_id = config.get("ad_channel") or config.get("partner_channel")
        if not ch_id:
            await interaction.response.send_message("❌ Configure o canal de parcerias primeiro!", ephemeral=True)
            return
        channel = interaction.guild.get_channel(ch_id)
        embed = discord.Embed(title="🤝 Parceria", description=descricao, color=discord.Color.purple(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="🔗 Convite", value=convite, inline=False)
        embed.set_footer(text=f"Anunciado por {interaction.user}")
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="🚀 Entrar no Servidor", url=convite, style=discord.ButtonStyle.link))
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Parceria anunciada!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Partnership(bot))
