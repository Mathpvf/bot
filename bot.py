import logging
import aiohttp
import qrcode
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Defina o token do bot
TOKEN = "7814085194:AAFUeF0vp4m-eiW50h0XIY7e2lQoAHbw0WU"
PUSHINPAY_TOKEN = "aFgVy188xjGLDiLa5trpIRxKTm7KpwuDEI1BJMYTa8a8c400"  # Adicione o seu token PushinPay
BASE_URL = "https://api.pushinpay.com.br/api/pix/cashIn"  # URL base para a API PushinPay

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def gerar_pix(valor: float, descricao: str) -> dict:
    logger.info(f"Gerando Pix para {descricao} no valor de R${valor:.2f}...")

    # Dados para gerar o Pix
    data = {
        "value": valor,  # Envia o valor como float
        "description": descricao,  # Descrição do Pix
        "webhook_url": "http://seuservico.com/webhook"  # Substitua pelo seu webhook
    }

    # Log do payload enviado
    logger.info(f"Payload enviado: {data}")

    # Cabeçalhos para a solicitação
    headers = {
        "Authorization": f"Bearer {PUSHINPAY_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Enviar requisição POST para a API da PushInPay usando aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BASE_URL, json=data, headers=headers) as response:
                response_data = await response.json()
                logger.info(f"Resposta da API: {response_data}")

                if response.status == 200:
                    logger.info("Pix gerado com sucesso!")
                    return response_data
                else:
                    logger.error(f"Erro ao gerar Pix: {response.status} - {response_data}")
                    return None
    except Exception as e:
        logger.error(f"Erro na requisição: {str(e)}")
        return None

# Função para gerar a imagem do QR Code
def gerar_qrcode(pix_code: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(pix_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Função para lidar com os cliques nos botões
async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Define o valor e a descrição com base no plano escolhido
    if query.data == "plano_15":
        valor = 790
        descricao = "Plano de 15 Dias"
    elif query.data == "plano_30":
        valor = 1490
        descricao = "Plano de 30 Dias"
    elif query.data == "plano_vitalicio":
        valor = 59.90
        descricao = "Plano Vitalício"
    else:
        await query.edit_message_text("Opção inválida. Tente novamente.")
        return

    # Gera o Pix
    pix_response = await gerar_pix(valor, descricao)

    if pix_response:
        # Extrair o código PIX no formato "Copia e Cola"
        qr_code = pix_response.get("qr_code")

        # Gera a imagem do QR Code
        qr_code_image = gerar_qrcode(qr_code)

        # Envia a imagem do QR Code
        await context.bot.send_photo(chat_id=query.message.chat_id, photo=qr_code_image, caption="Escaneie o QR Code para efetuar o pagamento.")

        # Envia a mensagem "Copie o Pix Copia e Cola abaixo 👇"
        await context.bot.send_message(chat_id=query.message.chat_id, text="Ou copie o Pix copia e cola 👇")

        # Envia o código PIX como texto
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"```{qr_code}```", parse_mode="Markdown")
    else:
        await query.edit_message_text("Erro ao gerar o Pix. Tente novamente.")

async def start(update: Update, context: CallbackContext) -> None:
    """Envia uma mensagem de boas-vindas ao usuário."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Olá, {user.mention_html()}! Seja bem-vindo ao melhor bot de sinais do Brasil! 🎮✨"
        "Aqui, você terá acesso aos melhores sinais de Aviator, com análises detalhadas e estratégias testadas para te ajudar a maximizar seus lucros.\n\n"
        "Nosso objetivo é fornecer informações claras e precisas para que você tenha a melhor experiência possível no jogo.\n\n"
        "📊 Aqui você encontra:\n"
        "- Sinais em tempo real: Receba notificações de sinais confiáveis para melhorar sua performance.\n\n"
        "🔒 Privacidade e segurança são nossa prioridade. Todos os sinais e conteúdos são feitos com responsabilidade para garantir que você tenha uma jogabilidade mais segura e assertiva.\n\n"
        "🚀 Prepare-se para decolar com os melhores sinais de Aviator! Lembre-se: o sucesso no jogo depende de paciência, disciplina e da utilização inteligente dos sinais que você receberá por aqui.\n\n"
        "          ⬇️ESCOLHA SEU PLANO ABAIXO⬇️\n\n",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("15 Dias R$7,90", callback_data="plano_15"),
             InlineKeyboardButton("30 Dias R$14,90", callback_data="plano_30")],
            [InlineKeyboardButton("Plano Vitalício 59,90", callback_data="plano_vitalicio")]
        ])
    )

def main():
    """Inicia o bot"""
    application = Application.builder().token(TOKEN).build()

    # Adiciona os handlers para os comandos e botões
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Inicia o bot
    application.run_polling()

if __name__ == "__main__":
    main()