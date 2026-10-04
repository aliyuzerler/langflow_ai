"""Facebook sayfa gönderisi paylaşan bileşen (Meta Graph API).

Tek bağımlılık: httpx. Token: uzun ömürlü Sayfa erişim anahtarı
(Graph API Explorer'dan alınan kullanıcı token'ı ile
GET /me/accounts?access_token=... çağrısından dönen page access_token).
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
from lfx.schema.data import Data
from lfx.schema.message import Message
from lfx.io import Output

GRAPH = "https://graph.facebook.com/v21.0"


class FacebookPostComponent(LCToolComponent):
    display_name = "Facebook Gönderisi"
    description = "Facebook sayfasına gönderi paylaşır (metin; isteğe bağlı bağlantı veya fotoğraf)."
    icon = "facebook"
    name = "FacebookPost"

    inputs = [
        SecretStrInput(
            name="access_token",
            display_name="Sayfa Erişim Anahtarı",
            info="Uzun ömürlü Sayfa access token'ı (pages_manage_posts izni).",
            required=False,
        ),
        MessageTextInput(
            name="page_id",
            display_name="Sayfa ID",
            info="Paylaşım yapılacak Facebook sayfasının ID'si.",
            required=False,
        ),
        MultilineInput(
            name="message",
            display_name="Gönderi Metni",
            info="Paylaşılacak metin.",
        ),
        MessageTextInput(
            name="link_url",
            display_name="Bağlantı (opsiyonel)",
            info="Gönderiye eklenecek URL.",
            advanced=True,
        ),
        MessageTextInput(
            name="photo_url",
            display_name="Fotoğraf URL'si (opsiyonel)",
            info="Herkese açık bir görsel URL'si; verilirse gönderi fotoğraf olarak paylaşılır.",
            advanced=True,
        ),
        DropdownInput(
            name="visibility",
            display_name="Görünürlük",
            options=["PUBLISHED", "STAGED"],
            value="PUBLISHED",
            advanced=True,
        ),
        BoolInput(
            name="dry_run",
            display_name="Deneme Modu (dry_run)",
            info="True ise API'ye istek atılmaz, paylaşılacak içerik önizleme olarak döner.",
            value=True,
        ),
    ]

    class FacebookPostSchema(BaseModel):
        message: str = Field(..., description="Paylaşılacak gönderi metni.")
        link_url: str = Field("", description="İsteğe bağlı bağlantı URL'si.")

    outputs = [
        Output(name="tools", display_name="Tool'lar", method="build_tool"),
        Output(name="result", display_name="Sonuç", method="run_model"),
    ]

    def _share(self, message: str, link_url: str = "") -> Data:
        if self.dry_run:
            return Data(data={
                "dry_run": True,
                "platform": "facebook",
                "page_id": self.page_id or "(boş)",
                "photo_url": self.photo_url or None,
                "message": message,
                "link_url": link_url or None,
            })

        if not self.access_token or not self.page_id:
            return Data(data={"error": "Sayfa Erişim Anahtarı ve Sayfa ID alanları zorunludur."})

        try:
            if self.photo_url:
                resp = httpx.post(
                    f"{GRAPH}/{self.page_id}/photos",
                    params={
                        "url": self.photo_url,
                        "caption": message,
                        "access_token": self.access_token,
                    },
                    timeout=30,
                )
            else:
                params = {"message": message, "access_token": self.access_token}
                if self.visibility == "STAGED":
                    params["published"] = "false"
                if link_url:
                    params["link"] = link_url
                resp = httpx.post(f"{GRAPH}/{self.page_id}/feed", params=params, timeout=30)
        except httpx.HTTPError as e:
            return Data(data={"error": f"Bağlantı hatası: {e}"})

        if resp.status_code == 401:
            return Data(data={"error": "401: Erişim anahtarı geçersiz veya süresi dolmuş."})
        if resp.status_code == 403:
            return Data(data={"error": "403: 'pages_manage_posts' izni eksik veya sayfa ID hatalı."})
        if resp.status_code >= 400:
            return Data(data={"error": f"{resp.status_code}: {resp.text[:300]}"})

        body = resp.json()
        post_id = body.get("id", "")
        return Data(data={
            "platform": "facebook",
            "post_id": post_id,
            "permalink": f"https://www.facebook.com/{self.page_id}/posts/{str(post_id).split('_')[-1]}",
        })

    def _share_tool(self, message: str, link_url: str = "") -> Data:
        return self._share(message, link_url)

    def build_tool(self) -> Tool:
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            name="facebook_post",
            description=(
                "Facebook sayfasına gönderi paylaşır. Kullanıcı açıkça onayladıysa kullan. "
                "'message' tam paylaşılacak metin olmalı."
            ),
            func=self._share_tool,
            args_schema=self.FacebookPostSchema,
        )

    def run_model(self) -> Message:
        result = self._share(self.message or "", self.link_url or "")
        self.status = result.data
        return Message(text=str(result.data))
