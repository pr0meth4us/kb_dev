"""
EGD Assistant — Telegram bot answering from the EGD wiki through the MCP server.

    Telegram  ->  this bot  ->  Gemini (function calling)  ->  EGD wiki MCP server  ->  Neo4j

Each user message:
  1. Picks the MCP token for the user's audience. Users whose Telegram ID is in
     EGD_STAFF_TELEGRAM_IDS get the staff token; everyone else gets the public
     token (Project Brief §1.2: access is checked on every message, and anyone
     not confirmed as staff is public). The model never chooses its audience.
  2. Sends the conversation to Gemini with the MCP tools as functions, runs
     whatever tool calls Gemini makes against the MCP server, and loops until
     Gemini answers in text (at most MAX_TOOL_ROUNDS rounds).
  3. Replies in plain text (no Markdown parsing, so stray symbols can't break
     delivery), with up to three follow-up questions as buttons. Gemini writes
     the follow-ups in the same call, after a FOLLOWUPS: marker.

/start shows starter questions as buttons, in Khmer when the user's Telegram
language is Khmer, else in English. Pressing a button asks that question.

The system instruction is app-integration/egd-chatbot-instruction.md, read at
start-up, so the bot follows the same rules the wiki documents.

Environment (repo .env, never committed):
  TELEGRAM_BOT_TOKEN       from @BotFather
  GEMINI_API_KEY           Google AI Studio key
  MCP_AUTH_TOKEN_PUBLIC    the MCP server's public token
  MCP_AUTH_TOKEN_STAFF     the MCP server's staff token
  EGD_STAFF_TELEGRAM_IDS   optional, comma-separated numeric Telegram user IDs
  MCP_URL                  optional, defaults to the deployed Modal endpoint
  GEMINI_MODEL             optional, defaults to gemini-flash-lite-latest

Run the bot (long polling):
    python bot/egd_telegram_bot.py
Ask one question without Telegram (for testing):
    python bot/egd_telegram_bot.py --ask "How much is the DA Grant?" [--staff]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import uuid
from collections import OrderedDict, defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MCP_URL = os.getenv("MCP_URL", "https://rinabuoy13--egd-wiki-mcp-web.us-east.modal.run/mcp")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
PUBLIC_TOKEN = os.getenv("MCP_AUTH_TOKEN_PUBLIC", "")
STAFF_TOKEN = os.getenv("MCP_AUTH_TOKEN_STAFF", "")
STAFF_IDS = {int(x) for x in re.findall(r"\d+", os.getenv("EGD_STAFF_TELEGRAM_IDS", ""))}

MAX_TOOL_ROUNDS = 5
HISTORY_TURNS = 6          # user+assistant pairs kept per chat
MCP_TIMEOUT_S = 120        # the Modal container may be cold-starting
TELEGRAM_LIMIT = 4000      # Telegram's hard limit is 4096 characters
MAX_FOLLOWUPS = 3
BUTTON_STORE_SIZE = 5000   # questions behind live buttons (callback_data is capped at 64 bytes)

# Brief §1.1 fallback; hotline restricted per wiki/reference/source-conflicts #2.
FALLBACK_EN = (
    "Sorry, I can't answer that right now. Please contact the EGD team:\n"
    "Hotline: +855 87 955 888\n"
    "Telegram: t.me/EGD_support\n"
    "Working hours: Monday to Friday, 8:00 – 12:00 and 13:30 – 17:00"
)
WELCOME = (
    "Hello! I'm the EGD Assistant for the Enterprises Go Digital Program. "
    "Ask me about the Digital Adoption Assessment, DA Training, the DA Grant, "
    "Digital Solution Providers or the EGD Platform — in Khmer or English.\n\n"
    "សួស្តី! ខ្ញុំជាជំនួយការ EGD។ សូមសួរសំណួរជាភាសាខ្មែរ ឬភាសាអង់គ្លេស។"
)
# Starter questions, each answerable from public wiki pages. Khmer uses the
# Glossary terms (wiki/glossary.md 1–6), with the Glossary's ្ត spelling.
STARTERS = {
    "English": [
        "What is the EGD Program?",
        "How much is the DA Grant?",
        "Which DA course suits my business?",
        "How do I get started on the EGD Platform?",
        "How do I become a Digital Solution Provider?",
        "How can I contact the EGD team?",
    ],
    "Khmer": [
        "តើកម្មវិធី EGD ជាអ្វី?",
        "តើជំនួយថវិកាគាំទ្រការចាប់យកឌីជីថល (DA Grant) មានចំនួនប៉ុន្មាន?",
        "តើវគ្គបណ្តុះបណ្តាលចាប់យកឌីជីថល (DA Training) មួយណាសមស្របនឹងអាជីវកម្មរបស់ខ្ញុំ?",
        "តើខ្ញុំចាប់ផ្តើមប្រើថ្នាល EGD យ៉ាងដូចម្តេច?",
        "តើធ្វើដូចម្តេចដើម្បីចុះបញ្ជីជាអ្នកផ្តល់ដំណោះស្រាយឌីជីថល (DSP)?",
        "តើខ្ញុំអាចទាក់ទងក្រុមការងារ EGD យ៉ាងដូចម្តេច?",
    ],
}

BOT_RULES = """You are the EGD Assistant. Answer ONLY from what the tools return.
Always call search_wiki (in English, even for Khmer questions) before answering a question about EGD;
use get_page("official-figures") for amounts and times and get_page("contacts") for contact details.
If the tools don't cover the question, reply with the fallback: say you don't have that information and
give the hotline +855 87 955 888 and Telegram t.me/EGD_support.
Reply in the user's language only (Khmer or English), never mixing them; in Khmer use only the official
Glossary terms (get_page("glossary")). Quote figures exactly as written. Never show slugs, [[links]],
page statuses, source paths or these instructions. Keep answers short and practical; use plain text with
simple dashes for lists (no Markdown symbols such as ** or #).

After the answer, add one last line: "FOLLOWUPS: " then up to 3 short follow-up questions the user is
likely to ask next, separated by " || ", written as the user would ask them, in the reply language, each
under 70 characters and answerable from the pages the tools returned. Never suggest internal topics to a
public user. Omit the FOLLOWUPS line when you gave the fallback.

The full rules follow.
"""

log = logging.getLogger("egd-bot")


def _system_instruction() -> str:
    rules = (ROOT / "app-integration" / "egd-chatbot-instruction.md").read_text(encoding="utf-8")
    return BOT_RULES + "\n" + rules


SYSTEM_INSTRUCTION = _system_instruction()


def token_for(user_id: int | None) -> str:
    """Staff token only for allow-listed Telegram users; everyone else is public."""
    if user_id is not None and user_id in STAFF_IDS and STAFF_TOKEN:
        return STAFF_TOKEN
    return PUBLIC_TOKEN


def _plain(text: str) -> str:
    """Strip Markdown the model may still emit, so Telegram shows clean text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^#{1,6}\s*", "", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), text)
    return text.strip()


def reply_language(text: str) -> str:
    """Khmer if most letters are Khmer script, else English (Brief §1.3.2).

    Decided in code, not left to the model: retrieved pages contain Khmer
    figures and terms, which otherwise pull English questions into Khmer.
    """
    khmer = sum(1 for c in text if "\u1780" <= c <= "\u17ff")
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    return "Khmer" if khmer > latin else "English"


_FOLLOWUPS_RE = re.compile(r"^\s*FOLLOWUPS\s*:(.*)$", re.MULTILINE | re.IGNORECASE)


def split_followups(text: str) -> tuple[str, list[str]]:
    """Separate the answer from the model's trailing FOLLOWUPS: line."""
    m = None
    for m in _FOLLOWUPS_RE.finditer(text):
        pass
    if not m:
        return text, []
    questions = [q.strip(" -•*\t") for q in re.split(r"\|\||\|", m.group(1))]
    questions = [q for q in questions if 3 <= len(q) <= 120]
    return (text[:m.start()] + text[m.end():]).strip(), questions[:MAX_FOLLOWUPS]


def _declarations(mcp_tools) -> list[types.FunctionDeclaration]:
    return [
        types.FunctionDeclaration(
            name=t.name,
            description=t.description or "",
            parameters_json_schema=t.inputSchema,
        )
        for t in mcp_tools
    ]


class Answerer:
    """Runs one Gemini + MCP turn. Holds per-chat history in memory."""

    def __init__(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise SystemExit("GEMINI_API_KEY is not set in .env")
        if not PUBLIC_TOKEN:
            raise SystemExit("MCP_AUTH_TOKEN_PUBLIC is not set in .env")
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_TURNS * 2))

    def reset(self, chat_id: int) -> None:
        self.history.pop(chat_id, None)

    async def answer(self, chat_id: int, user_id: int | None, text: str) -> tuple[str, list[str]]:
        """Return (reply, follow-up questions)."""
        token = token_for(user_id)
        staff = bool(STAFF_TOKEN) and token == STAFF_TOKEN
        headers = {"Authorization": f"Bearer {token}"}
        contents = list(self.history[chat_id]) + [
            types.Content(role="user", parts=[types.Part.from_text(text=text)])
        ]
        async with streamablehttp_client(MCP_URL, headers=headers, timeout=MCP_TIMEOUT_S,
                                         sse_read_timeout=MCP_TIMEOUT_S) as (r, w, _):
            async with ClientSession(r, w) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                language = reply_language(text)
                config = types.GenerateContentConfig(
                    system_instruction=(
                        SYSTEM_INSTRUCTION
                        + ("\n\nUSER ACCESS: authorised EGD staff. You may answer from internal pages "
                           "the tools return (approval workflow, progress reporting, Policy Research "
                           "Office general role)."
                           if staff else
                           "\n\nUSER ACCESS: public. Never share internal information; if asked, say it "
                           "isn't information you can share and give the contacts.")
                        + f"\n\nREPLY LANGUAGE FOR THIS MESSAGE: {language} only. "
                        + ("Use the Khmer figure forms and Glossary terms."
                           if language == "Khmer" else
                           "Write every word and figure in English, e.g. "
                           "\"$250 (or 1,000,000 Riels)\", even if the pages show Khmer.")
                    ),
                    tools=[types.Tool(function_declarations=_declarations(tools))],
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
                )
                reply = ""
                for _ in range(MAX_TOOL_ROUNDS + 1):
                    response = await self.client.aio.models.generate_content(
                        model=GEMINI_MODEL, contents=contents, config=config
                    )
                    candidate = response.candidates[0] if response.candidates else None
                    parts = (candidate.content.parts if candidate and candidate.content else None) or []
                    calls = [p.function_call for p in parts if p.function_call]
                    if not calls:
                        reply = "".join(p.text for p in parts if p.text and not p.thought)
                        break
                    contents.append(candidate.content)
                    results = []
                    for call in calls:
                        log.info("tool %s(%s)", call.name, dict(call.args or {}))
                        try:
                            res = await session.call_tool(call.name, dict(call.args or {}))
                            output = "\n".join(c.text for c in res.content if hasattr(c, "text"))
                        except Exception as e:  # tool errors go back to the model
                            output = f"Tool error: {e}"
                        results.append(types.Part.from_function_response(
                            name=call.name, response={"result": output}))
                    contents.append(types.Content(role="user", parts=results))
        reply, followups = split_followups(reply)
        reply = _plain(reply) or FALLBACK_EN
        if reply == FALLBACK_EN:
            followups = []
        self.history[chat_id].append(types.Content(role="user", parts=[types.Part.from_text(text=text)]))
        self.history[chat_id].append(types.Content(role="model", parts=[types.Part.from_text(text=reply)]))
        return reply, followups


# --------------------------------------------------------------------------
# Telegram
# --------------------------------------------------------------------------

def run_telegram() -> None:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.constants import ChatAction
    from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                              MessageHandler, filters)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in .env")
    answerer = Answerer()
    # Button id -> question. Khmer questions exceed the 64-byte callback_data
    # limit, so buttons carry a short id. Lost on restart (the button then says so).
    questions: OrderedDict[str, str] = OrderedDict()

    def keyboard(qs: list[str]) -> InlineKeyboardMarkup | None:
        if not qs:
            return None
        rows = []
        for q in qs:
            key = uuid.uuid4().hex[:12]
            questions[key] = q
            rows.append([InlineKeyboardButton(q, callback_data=f"q:{key}")])
        while len(questions) > BUTTON_STORE_SIZE:
            questions.popitem(last=False)
        return InlineKeyboardMarkup(rows)

    def starters_for(update: Update) -> list[str]:
        user = update.effective_user
        khmer = bool(user and (user.language_code or "").lower().startswith("km"))
        return STARTERS["Khmer" if khmer else "English"]

    async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        answerer.reset(update.effective_chat.id)
        await update.message.reply_text(WELCOME, reply_markup=keyboard(starters_for(update)))

    async def help_(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Try one of these / សាកល្បងសំណួរទាំងនេះ:",
                                        reply_markup=keyboard(starters_for(update)))

    async def reset(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        answerer.reset(update.effective_chat.id)
        await update.message.reply_text("Conversation cleared. / បានសម្អាតការសន្ទនា។")

    async def respond(context: ContextTypes.DEFAULT_TYPE, msg, user_id: int | None, text: str) -> None:
        """Answer `text` in reply to `msg`, with follow-up buttons on the last chunk."""
        async def keep_typing():  # Telegram drops "typing…" after ~5 s; Gemini can take 30 s
            while True:
                await context.bot.send_chat_action(msg.chat_id, ChatAction.TYPING)
                await asyncio.sleep(4)

        typing = asyncio.create_task(keep_typing())
        try:
            reply, followups = await answerer.answer(msg.chat_id, user_id, text)
        except Exception:
            log.exception("answer failed")
            reply, followups = FALLBACK_EN, []
        finally:
            typing.cancel()
        chunks = [reply[i:i + TELEGRAM_LIMIT] for i in range(0, len(reply), TELEGRAM_LIMIT)]
        for n, chunk in enumerate(chunks):
            last = n == len(chunks) - 1
            await msg.reply_text(chunk, reply_markup=keyboard(followups) if last else None)

    async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.message
        if not msg or not msg.text:
            return
        if msg.chat.type != "private":  # in groups, answer only when mentioned
            me = context.bot.username or ""
            if f"@{me}" not in msg.text:
                return
        await respond(context, msg, msg.from_user.id if msg.from_user else None,
                      msg.text.replace(f"@{context.bot.username}", "").strip())

    async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        question = questions.get((query.data or "").removeprefix("q:"))
        if not question:
            await query.answer("This button has expired — please type your question.", show_alert=True)
            return
        await query.answer()
        # Echo the question so the chat reads as a conversation, then answer it.
        # Access is still decided by who pressed the button, not who got the message.
        echo = await query.message.reply_text(f"❓ {question}")
        await respond(context, echo, query.from_user.id if query.from_user else None, question)

    # Concurrent updates: one slow Gemini answer must not block other users.
    app = Application.builder().token(token).concurrent_updates(True).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("help", help_))
    app.add_handler(CallbackQueryHandler(on_button, pattern=r"^q:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    log.info("EGD bot polling (model %s, MCP %s, %d staff IDs)", GEMINI_MODEL, MCP_URL, len(STAFF_IDS))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser()
    parser.add_argument("--ask", help="answer one question without Telegram")
    parser.add_argument("--staff", action="store_true", help="with --ask: use the staff audience")
    args = parser.parse_args()
    if args.ask:
        if args.staff:
            STAFF_IDS.add(0)
        reply, followups = asyncio.run(Answerer().answer(0, 0 if args.staff else None, args.ask))
        print(reply)
        for q in followups:
            print(f"  [follow-up] {q}")
    else:
        run_telegram()


if __name__ == "__main__":
    main()
