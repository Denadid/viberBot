from Setting import TOKEN, WEBHOOK
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration

bot_configuration = BotConfiguration(
                    name='FeaR',
                    avatar='https://viber.com/avatar/jpg',
                    auth_token=TOKEN
)


viber = Api(bot_configuration)
viber.set_webhook(WEBHOOK)
