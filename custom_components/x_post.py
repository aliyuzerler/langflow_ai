"""X (Twitter) gönderisi paylaşan bileşen (API v2).

Not: X API'de yazma erişimi ücretli katmanlara (Basic ve üzeri) aittir;
ücretsiz katmanda bu uç nokta 403 döner.
"""

from pydantic import BaseModel, Field

import httpx
from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import (
    BoolInput,
    MultilineInput,
    SecretStrInput,
)
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.message import Message

API = "https://api.twitter.com/2/tweets"


class XPostComponent(LCToolComponent):
    display_name = "X (Twitter) Gönderisi"
    description = "X'te 280 karaktere kadar tweet paylaşır (API v2; yazma erişimi ücretli katman gerektirir)."
    icon = "x"
    name = "XPost"

    inputs = [
        SecretStrInput(
            name="bearer_token",
            display_name="Bearer Token",
            info="X developer portalındaki uygulamanın Bearer Token'ı (yazma izinli katman).",
            required=False,
        ),
        MultilineInput(
            name="message",
            display_name="Tweet Metni",
            info="280 karaktere kadar tweet metni.",
        ),
        BoolInput(
            name="dry_run",
            display_name="Deneme Modu (dry_run)",
            info="True ise API'ye istek atılmaz, paylaşılacak içerik önizleme olarak döner.",
            value=True,
        ),
    ]

    class XPostSchema(BaseModel):
        message: str = Field(..., description="Tweet metni (en fazla 280 karakter).")

    outputs = [
        Output(name="tools", display_name="Tool'lar", method="build_tool"),
        Output(name="result", display_name="Sonuç", method="run_model"),
    ]

    def _share(self, message: str) -> Data:
        if len(message) > 280:
            message = message[:277] + "..."
        if self.dry_run:
            return Data(data={
                "dry_run": True,
                "platform": "x",
                "message": message,
                "chars": len(message),
            })

        if not self.bearer_token:
            return Data(data={"error": "Bearer Token zorunludur."})

        try:
            resp = httpx.post(
                API,
                json={"text": message},
                headers={"Authorization": f"Bearer {self.bearer_token}"},
                timeout=30,
            )
        except httpx.HTTPError as e:
            return Data(data={"error": f"Bağlantı hatası: {e}"})

        if resp.status_code == 401:
            return Data(data={"error": "401: Bearer Token geçersiz."})
        if resp.status_code == 403:
            return Data(data={
                "error": "403: Bu anahtarla yazma izni yok. X API'de tweet atmak ücretli katman (Basic+) gerektirir.",
            })
        if resp.status_code >= 400:
            return Data(data={"error": f"{resp.status_code}: {resp.text[:300]}"})

        tweet = resp.json().get("data", {})
        tweet_id = tweet.get("id", "")
        return Data(data={
            "platform": "x",
            "tweet_id": tweet_id,
            "permalink": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else "",
        })

    def build_tool(self) -> Tool:
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            name="x_post",
            description=(
                "X'te tweet paylaşır. Kullanıcı açıkça onayladıysa ve metin 280 karakteri geçmiyorsa kullan."
            ),
            func=self._share,
            args_schema=self.XPostSchema,
        )

    def run_model(self) -> Message:
        result = self._share(self.message or "")
        self.status = result.data
        return Message(text=str(result.data))
