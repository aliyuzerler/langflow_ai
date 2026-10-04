"""LinkedIn gönderisi paylaşan bileşen (Posts API).

Token: developer.linkedin.com'dan oluşturulan uygulamaya ait
w_member_social izinli üye token'ı (60 gün ömürlü).
"""

from pydantic import BaseModel, Field

import httpx
from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import (
    BoolInput,
    DropdownInput,
    MessageTextInput,
    MultilineInput,
    SecretStrInput,
)
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.message import Message

API = "https://api.linkedin.com"
LINKEDIN_VERSION = "202506"


class LinkedInPostComponent(LCToolComponent):
    display_name = "LinkedIn Gönderisi"
    description = "LinkedIn'de kişi veya şirket sayfası adına metin gönderisi paylaşır."
    icon = "linkedin"
    name = "LinkedInPost"

    inputs = [
        SecretStrInput(
            name="access_token",
            display_name="Erişim Anahtarı",
            info="w_member_social izinli üye token'ı (60 gün ömürlü).",
            required=False,
        ),
        MessageTextInput(
            name="author",
            display_name="Yazar URN",
            info="Kişi: urn:li:person:{id} — Şirket sayfası: urn:li:organization:{id}",
            required=False,
        ),
        DropdownInput(
            name="author_type",
            display_name="Yazar Türü",
            options=["urn:li:person", "urn:li:organization"],
            value="urn:li:person",
            advanced=True,
        ),
        MessageTextInput(
            name="author_id",
            display_name="Yazar ID",
            info="Kişi veya şirket ID'si (URN yerine). Yazar URN boşsa kullanılır.",
            advanced=True,
        ),
        MultilineInput(
            name="message",
            display_name="Gönderi Metni",
            info="Paylaşılacak metin (3000 karaktere kadar).",
        ),
        BoolInput(
            name="dry_run",
            display_name="Deneme Modu (dry_run)",
            info="True ise API'ye istek atılmaz, paylaşılacak içerik önizleme olarak döner.",
            value=True,
        ),
    ]

    class LinkedInPostSchema(BaseModel):
        message: str = Field(..., description="Paylaşılacak gönderi metni.")

    outputs = [
        Output(name="tools", display_name="Tool'lar", method="build_tool"),
        Output(name="result", display_name="Sonuç", method="run_model"),
    ]

    def _author_urn(self) -> str:
        if self.author:
            return self.author
        if self.author_id:
            return f"{self.author_type}:{self.author_id}"
        return ""

    def _share(self, message: str) -> Data:
        urn = self._author_urn()
        if self.dry_run:
            return Data(data={
                "dry_run": True,
                "platform": "linkedin",
                "author": urn or "(boş)",
                "message": message[:3000],
            })

        if not self.access_token or not urn:
            return Data(data={"error": "Erişim Anahtarı ve Yazar URN (veya Yazar ID) zorunludur."})
        if len(message) > 3000:
            message = message[:2997] + "..."

        payload = {
            "author": urn,
            "commentary": message,
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_VERSION,
        }
        try:
            resp = httpx.post(f"{API}/rest/posts", json=payload, headers=headers, timeout=30)
        except httpx.HTTPError as e:
            return Data(data={"error": f"Bağlantı hatası: {e}"})

        if resp.status_code == 401:
            return Data(data={"error": "401: Token geçersiz veya süresi dolmuş (60 gün)."})
        if resp.status_code == 403:
            return Data(data={"error": "403: w_member_social izni yok veya yazar URN hatalı."})
        if resp.status_code >= 400:
            return Data(data={"error": f"{resp.status_code}: {resp.text[:300]}"})

        post_urn = resp.headers.get("x-restli-id", resp.headers.get("x-linkedin-id", ""))
        permalink = f"https://www.linkedin.com/feed/update/{post_urn}" if post_urn else ""
        return Data(data={
            "platform": "linkedin",
            "post_urn": post_urn,
            "permalink": permalink,
        })

    def build_tool(self) -> Tool:
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            name="linkedin_post",
            description=(
                "LinkedIn'de metin gönderisi paylaşır. Kullanıcı açıkça onayladıysa kullan. "
                "'message' tam paylaşılacak metin olmalı."
            ),
            func=self._share,
            args_schema=self.LinkedInPostSchema,
        )

    def run_model(self) -> Message:
        result = self._share(self.message or "")
        self.status = result.data
        return Message(text=str(result.data))
