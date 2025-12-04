# plugins\filedetect.py
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply




@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = []

        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append(
                [
                    InlineKeyboardButton("📁 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁",callback_data = "upload_document"),
                    InlineKeyboardButton("🎥 𝗩𝗶𝗱𝗲𝗼", callback_data = "upload_video")
                ]
            )
        elif file.media == MessageMediaType.AUDIO:
            button.append(
                [
                    InlineKeyboardButton("📁 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁",callback_data = "upload_document"),
                    InlineKeyboardButton("🎵 𝗔𝘂𝗱𝗶𝗼", callback_data = "upload_audio")
                ]
            )
        button.extend([
            [
                InlineKeyboardButton("🖼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗧𝗵𝘂𝗺𝗯", callback_data="getthumb"),
                InlineKeyboardButton("🖼  𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗖𝗼𝘃𝗲𝗿", callback_data="getcover")
            ],
            [
                InlineKeyboardButton("✖️ 𝗖𝗮𝗻𝗰𝗲𝗹", callback_data="cancel")
            ]
        ])


        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("^airename$"))
async def ai_rename(bot, update):
    print("🤖 AI Renamer Triggered :: ",update.message.reply_to_message.video.file_name or update)
    message = update.message
    file = message.reply_to_message
    media = getattr(file, file.media.value)

    # Create a placeholder name tag for AI
    ai_tag = "File Name will Set by :- AI_Renamer"

    button = []
    if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
        button.append(
            [
                InlineKeyboardButton("📁 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁", callback_data="upload_document"),
                InlineKeyboardButton("🎥 𝗩𝗶𝗱𝗲𝗼", callback_data="upload_video")
            ]
        )
    elif file.media == MessageMediaType.AUDIO:
        button.append(
            [
                InlineKeyboardButton("📁 𝗗𝗼𝗰𝘂𝗺𝗲𝗻𝘁", callback_data="upload_document"),
                InlineKeyboardButton("🎵 𝗔𝘂𝗱𝗶𝗼", callback_data="upload_audio")
            ]
        )

    button.extend([
        [
            InlineKeyboardButton("🖼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗧𝗵𝘂𝗺𝗯", callback_data="getthumb"),
            InlineKeyboardButton("🖼  𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗖𝗼𝘃𝗲𝗿", callback_data="getcover")
        ],
        [
            InlineKeyboardButton("✖️ 𝗖𝗮𝗻𝗰𝗲𝗹", callback_data="cancel")
        ]
    ])

    try:
        await message.delete()
        await message.reply(
            text=f"**Select The Output File Type**\n\n**{ai_tag}**",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )
    except Exception as e:
        print("Error at ai renamer send msg :",e)

