import aiohttp
import discord
import re
import logging

from typing import Optional
from .base import BaseRule
from .config.models import InfractionInformation, EmbedField
from ..utils import transform_bool_to_emoji

log = logging.getLogger(name="red.breadcogs.automod.imagedetection")

AZURE_URL_RE = "https?://([a-z0-9-]+[.])*cognitiveservices.azure[.]com"
VISION_URL = "/vision/v3.0/analyze/?visualFeatures=Adult,Description"

# Config Constants
AZURE_KEY = "azure_key"
AZURE_ENDPOINT = "azure_endpoint"


class EndpointNotSetException(Exception):
    pass


class SecretKeyNotSetException(Exception):
    pass


class ImageDetectionRule(BaseRule):
    def __init__(
        self, config,
    ):
        super().__init__(config)
        self.name = "imagedetection"

    async def set_endpoint(self, guild: discord.Guild, endpoint: str) -> None:
        """Set the azure cognitive services endpoint"""
        if not re.match(AZURE_URL_RE, endpoint):
            raise ValueError(
                "Invalid azure endpoint, must be: `https://[name].cognitiveservices.azure.com"
            )

        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]  # strip the last / off the url

        await self.config.guild(guild).set_raw(self.rule_name, AZURE_ENDPOINT, value=endpoint)

    async def set_key(self, guild: discord.Guild, key: str):
        """Set the key associated with the endpoint"""
        await self.config.guild(guild).set_raw(self.rule_name, AZURE_KEY, value=key)

    async def get_key(self, guild: discord.Guild):
        """Get key from config, throws Key Error if not set"""
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, AZURE_KEY)
        except KeyError:
            raise SecretKeyNotSetException(
                "No endpoint secret key has been set, you can access this from the Azure Portal"
            )

    async def get_endpoint(self, guild: discord.Guild):
        try:
            base_endpoint = await self.config.guild(guild).get_raw(self.rule_name, AZURE_ENDPOINT)
            return f"{base_endpoint}{VISION_URL}"
        except KeyError:
            raise EndpointNotSetException(
                "No endpoint URL has been set, you can access this from the Azure Portal"
            )

    async def get_announcement_embed(
        self,
        message: discord.Message,
        message_has_been_deleted: bool,
        action_taken_success: bool,
        action_taken: Optional[str],
        infraction_information=None,
    ) -> discord.Embed:
        embed = await super().get_announcement_embed(
            message,
            message_has_been_deleted,
            action_taken_success,
            action_taken,
            infraction_information,
        )
        embed.description = infraction_information.message
        for field in infraction_information.extra_fields:
            embed.add_field(name=field.name, value=field.value)
        return embed

    async def is_offensive(
        self, message: discord.Message,
    ):
        if not message.attachments:
            return  # we don't care about non-image messages

        try:
            author, guild, content = message.author, message.guild, message.content
            subscription_key, url = await self.get_key(guild), await self.get_endpoint(guild)
            headers = {
                "Ocp-Apim-Subscription-Key": subscription_key,
                "Content-Type": "application/json",
            }
            data = {"url": message.attachments[0].url}

            image_details = {}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    json_response = await response.json()

                    if "error" in json_response:
                        if json_response["error"]["code"] == "429":
                            log.warning(
                                "Being rate-limited by Azure Cognitive services. Skipping image."
                            )
                        if json_response["error"]["code"] == "InvalidImageSize":
                            log.warning(f"InvalidImageSize: {json_response['error']['message']}")
                    image_details = json_response

            adult = image_details["adult"]
            adult_content, racy_content, gory_content = (
                adult["isAdultContent"],
                adult["isRacyContent"],
                adult["isGoryContent"],
            )
            if adult_content or racy_content or gory_content:
                message = ""
                if "description" in image_details:
                    caption = image_details["description"]["captions"][0]["text"]
                    message += f"**Image description:**\n`{caption}`\n\n"
                    if "tags" in image_details["description"]:
                        message += "**Tags:**\n"
                        message += ", ".join(
                            "`{0}`".format(w) for w in image_details["description"]["tags"]
                        )

                extra_fields = [
                    EmbedField("Adult Content", transform_bool_to_emoji(adult_content)),
                    EmbedField("Racy Content", transform_bool_to_emoji(racy_content)),
                    EmbedField("Gory Content", transform_bool_to_emoji(gory_content)),
                ]
                return InfractionInformation(message=message, rule=self, extra_fields=extra_fields)

        except EndpointNotSetException as e:
            log.exception(e.args[0], exc_info=e)
        except SecretKeyNotSetException as e:
            log.exception(e.args[0], exc_info=e)
