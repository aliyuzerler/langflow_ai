# Sosyal Medya Paylaşım Bileşenleri

Langflow'u şu şekilde başlatınca yan menüde görünürler:

```bash
python -m uv run langflow run \
  --frontend-path src/backend/base/langflow/frontend \
  --host 0.0.0.0 --port 7860 \
  --components-path custom_components \
  --no-open-browser --env-file .env
```

Tüm bileşenlerde **dry_run varsayılan `True`**dur: API'ye istek atılmaz,
paylaşılacak içerik önizleme olarak döner. Gerçek paylaşım için bileşen
düğümünde dry_run'ı kapatın.

## Token alma rehberi

### Facebook + Instagram (Meta)
1. developers.facebook.com → uygulama oluştur (tür: Business)
2. Graph API Explorer'da (developers.facebook.com/tools/explorer) token üret,
   izinlere ekle: `pages_show_list`, `pages_read_engagement`,
   `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`
3. Uzun ömürlü kullanıcı token'ı:
   `GET /oauth/access_token?grant_type=fb_exchange_token&...` (60 gün)
4. Sayfa token'ı: `GET /me/accounts?access_token={uzunToken}` →
   her sayfa için `access_token` ve `id` döner
   - Facebook bileşeni: bu `access_token` + sayfa `id`
   - Instagram bileşeni: aynı token + IG iş hesabı ID'si
     (`GET /{sayfa-id}?fields=instagram_business_account`)
5. Instagram hesabı **iş/profesyonel hesap** olmalı ve bir Facebook sayfasına
   bağlı olmalı. IG API'si **metin-only gönderiye izin vermez** — görsel şart.

### LinkedIn
1. developer.linkedin.com → uygulama oluştur, ürün olarak "Share on LinkedIn"
2. Uygulamaya `w_member_social` izni ekle, OAuth ile üye token'ı al (60 gün)
3. Kişi ID'niz: `GET /v2/userinfo` → `sub` alanı → Yazar URN:
   `urn:li:person:{sub}`; şirket sayfası için `urn:li:organization:{id}`

### X (Twitter)
1. developer.x.com → proje + uygulama oluştur
2. **Önemli:** tweet atma (yazma) erişimi **ücretli katmanlara** (Basic ve
   üzeri) aittir; ücretsiz katmanda API 403 döner
3. Uygulama anahtarlarından Bearer Token'ı alın

## Güvenlik notları
- Anahtarlar `SecretStrInput` ile maskeli; kalıcı saklamak için
  Ayarlar → Global Değişkenler → **Credential** türünü kullanın
- dry_run açıkken agent sadece önizleme döner; yanlışlıkla paylaşım olmaz
- Bu sunucu AUTO_LOGIN ile ağa açıksa token'lı akışları yalnızca güvenilen
  ağda kullanın
