import os

import requests

from discord.ext.commands import Bot, Context

BOT = Bot(command_prefix="~")


@BOT.command()  # type: ignore
async def osr2mp4(ctx: Context) -> None:
    # TODO: Use `ctx.reply`
    if not ctx.message.attachments:
        await ctx.channel.send("Expected an attached replay file.")
        return
    attachment = ctx.message.attachments[0]
    if attachment.size > 10_000_000:
        await ctx.channel.send("Replay file is over 10MB.")
        return
    if not attachment.filename.endswith(".osr"):
        await ctx.channel.send("Expected a `.osr` file.")
        return
    payload = {
        "trigger": "discord",
        "channel_id": ctx.channel.id,
        "message_id": ctx.message.id,
        "replay_url": attachment.url,
    }
    resp = requests.post(os.environ["ENDPOINT"], json=payload)
    if not resp.ok:
        await ctx.channel.send("Sorry, something is wrong with the server right now.")
    resp.raise_for_status()


if __name__ == "__main__":
    BOT.run(os.environ["DISCORD_TOKEN"])
