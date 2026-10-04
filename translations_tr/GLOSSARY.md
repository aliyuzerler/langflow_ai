# Türkçe Çeviri Sözlüğü — Langflow

Kurallar: Teknik terimler İngilizce kalır; cümle/etiket/açıklama çevrilir.
`{{placeholder}}` ifadeleri aynen korunur. Çoğul anahtarları `_one/_other` korunur.

## Kalacak (çevrilmez) terimler
| Terim | Kullanım |
|---|---|
| Flow | akış nesnesinin adı (New Flow, My Flows, Run Flow) |
| Component | bileşen nesnesinin adı |
| Chat | Chat Input, Chat Output, chat paneli |
| Prompt | Prompt bileşeni, prompt alanları |
| Agent | Agent bileşeni |
| Playground | test paneli adı |
| Knowledge Base | bilgi tabanı özelliği (KB kısaltması da olur) |
| MCP / A2A / API / SDK / CLI / JSON / CSV / URL | teknik |
| Model, Embedding, Token, Memory, Session | teknik bağlamda |
| Langflow, Store | ürün adları |
| Tool | Agent Tool bağlamında |
| Sub Flow, Webhook | bileşen adları |
| Check / Uncheck / Clear gibi API param değerleri | bağlama göre |

## Standart çeviriler
| English | Türkçe |
|---|---|
| Save | Kaydet |
| Cancel | İptal |
| Delete | Sil |
| Remove | Kaldır |
| Edit | Düzenle |
| Close | Kapat |
| Create | Oluştur |
| Add | Ekle |
| Search | Ara |
| Settings | Ayarlar |
| General | Genel |
| Update | Güncelle |
| Duplicate | Kopyala |
| Export | Dışa aktar |
| Import | İçe aktar |
| Download | İndir |
| Upload | Yükle |
| Copy | Kopyala |
| Paste | Yapıştır |
| Run | Çalıştır |
| Build | Derle |
| New Flow | Yeni Flow |
| My Collection | Koleksiyonum |
| Project | Proje |
| Folder | Klasör |
| Variable | Değişken |
| Credentials | Kimlik bilgileri |
| API Key | API anahtarı |
| User | Kullanıcı |
| Login / Sign in | Giriş yap |
| Logout / Sign out | Çıkış yap |
| Password | Şifre |
| Description | Açıklama |
| Name | Ad |
| Value | Değer |
| Error | Hata |
| Warning | Uyarı |
| Loading | Yükleniyor |
| File | Dosya |
| Preview | Önizleme |
| Search components | Bileşen ara |
| Keyboard Shortcuts | Klavye kısayolları |
| Documentation | Dokümantasyon |
| Notifications | Bildirimler |
| Message | Mesaj |
| Text | Metin |
| Input | Girdi |
| Output | Çıktı |
| Connection | Bağlantı |
| Node | Düğüm |
| Edge | Kenar |
| Canvas | Tuval |
| Zoom In / Out | Yakınlaştır / Uzaklaştır |
| Undo / Redo | Geri al / Yinele |
| Clear conversation | Sohbeti temizle |
| Knowledge | Knowledge |
| Data | Veri |
| Template | Şablon |
| Notifications & errors | Bildirimler ve hatalar |

## Üslup
- "sen" değil "siz" değil — nötr emir kipi: "Akışı silmek istediğine emin misin?" yerine
  mevcut dillerin üslubuna uygun olarak **soru formu nötr**: "...istediğinden emin misin?"
  Tutarlılık için: **sen üslubu** (Fr/Eş çok resmi değil). Kısa etiketlerde emir kipi.
- Boş bırakılmaz: bir anahtar çevrilmediyse en.json değeri kalır (raporda görünür).
