"""Instagram gönderisi paylaşan bileşen (Meta Graph API, iki adımlı).

IG Graph API'si metin-only gönderiye izin vermez: herkese açık bir
görsel URL'si zorunludur. Adımlar: medya konteynerı oluştur → yayınla.
"""

from pydantic import BaseModel, Field

import httpx
from lfx.base.langchain_utilities.model import LCToolComponent
from lfx.field_typing import Tool
from lfx.inputs.inputs import (
    BoolInput,
    MessageTextInput,
    MultilineInput,
    SecretStrInput,
)
from lfx.io import Output
from lfx.schema.data import Data
from lfx.schema.message import Message

GRAPH = "https://graph.facebook.com/v21.0"


class InstagramPostComponent(LCToolComponent):
    display_name = "Instagram Gönderisi"
    description = (
        "Instagram iş hesabına görselli gönderi paylaşır (caption + herkese açık görsel URL'si). "
        "İki adımlı Graph API: medya konteynerı → yayınla."
    )
    icon = "instagram"
    name = "InstagramPost"

    inputs = [
        SecretStrInput(
            name="access_token",
            display_name="Erişim Anahtarı",
            info="instagram_content_publish izinli uzun ömürlü token (IG iş hesabına bağlı).",
            required=False,
        ),
        MessageTextInput(
            name="ig_user_id",
            display_name="Instagram Kullanıcı ID",
            info="IG iş hesabının Graph API kullanıcı ID'si (biçim: 1784XXXXXXXXX).",
            required=False,
        ),
        MessageTextInput(
            name="image_url",
            display_name="Görsel URL'si",
            info="Herkese açık erişilebilir görsel bağlantısı (https). IG API'sinde görsel zorunludur.",
        ),
        MultilineInput(
            name="caption",
            display_name="Açıklama (caption)",
            info="Gönderi metni + hashtag'ler (en fazla 2200 karakter).",
        ),
        BoolInput(
            name="dry_run",
            display_name="Deneme Modu (dry_run)",
            info="True ise API'ye istek atılmaz, paylaşılacak içerik önizleme olarak döner.",
            value=True,
        ),
    ]

    class InstagramPostSchema(BaseModel):
        caption: str = Field(..., description="Gönderi açıklaması ve hashtag'ler.")
        image_url: str = Field("", description="Herkese açık görsel URL'si (boşsa bileşen ayarındaki kullanılır).")

    outputs = [
        Output(name="tools", display_name="Tool'lar", method="build_tool"),
        Output(name="result", display_name="Sonuç", method="run_model"),
    ]

    def _share(self, caption: str, image_url: str = "") -> Data:
        img = image_url or self.image_url or ""
        if self.dry_run:
            return Data(data={
                "dry_run": True,
                "platform": "instagram",
                "ig_user_id": self.ig_user_id or "(boş)",
                "image_url": img or "(boş — görsel zorunlu!)",
                "caption": caption[:2200],
            })

        if not self.access_token or not self.ig_user_id:
            return Data(data={"error": "Erişim Anahtarı ve Instagram Kullanıcı ID zorunludur."})
        if not img:
            return Data(data={"error": "Instagram API'si görsel olmadan gönderiye izin vermez. Görsel URL'si girin."})
        if len(caption) > 2200:
            caption = caption[:2197] + "..."

        try:
            # 1. adım: medya konteynerı
            create = httpx.post(
                f"{GRAPH}/{self.ig_user_id}/media",
                params={"image_url": img, "caption": caption, "access_token": self.access_token},
                timeout=30,
            )
            if create.status_code == 401:
                return Data(data={"error": "401: Erişim anahtarı geçersiz veya süresi dolmuş."})
            if create.status_code == 403:
                return Data(data={
                    "error": "403: instagram_content_publish izni yok veya hesap iş hesabı değil.",
                })
            if create.status_code >= 400:
                return Data(data={"error": f"Konteyner hatası {create.status_code}: {create.text[:300]}"})
            creation_id = create.json().get("id")

            # 2. adım: yayınla
            publish = httpx.post(
                f"{GRAPH}/{self.ig_user_id}/media_publish",
                params={"creation_id": creation_id, "access_token": self.access_token},
                timeout=30,
            )
            if publish.status_code >= 400:
                return Data(data={"error": f"Yayınlama hatası {publish.status_code}: {publish.text[:300]}"})
            media_id = publish.json().get("id", "")

            # 3. adım (opsiyonel): kalıcı bağlantı
            permalink = ""
            try:
                info = httpx.get(
                    f"{GRAPH}/{media_id}",
                    params={"fields": "permalink", "access_token": self.access_token},
                    timeout=15,
                )
                if info.status_code < 400:
                    permalink = info.json().get("permalink", "")
            except httpx.HTTPError:
                pass
        except httpx.HTTPError as e:
            return Data(data={"error": f"Bağlantı hatası: {e}"})

        return Data(data={
            "platform": "instagram",
            "media_id": media_id,
            "permalink": permalink,
        })

    def _share_tool(self, caption: str, image_url: str = "") -> Data:
        return self._share(caption, image_url)

    def build_tool(self) -> Tool:
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            name="instagram_post",
            description=(
                "Instagram'a görselli gönderi paylaşır. Kullanıcı açıkça onayladıysa ve "
                "geçerli bir görsel URL'si varsa kullan. 'caption' tam açıklama + hashtag'ler."
            ),
            func=self._share_tool,
            args_schema=self.InstagramPostSchema,
        )

    def run_model(self) -> Message:
        result = self._share(self.caption or "")
        self.status = result.data
        return Message(text=str(result.data))
