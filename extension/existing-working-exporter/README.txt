FC27 Club Exporter v0.4

AKIŞ
1) Players'a gir ve tüm sayfaları normal şekilde gez.
2) Squads'a gir ve aktif kadronu seç.
Squad ekranı aktif taktik export-code isteğini de tetiklerse hem "Kadro" hem "Aktif taktik + roller"
otomatik tik olur ve JSON'u İndir açılır.
Taktik otomatik gelmezse eklenti "Tactics -> aktif taktiğini bir kez aç" uyarısı gösterir.

İNDİRME
- Dosya adı artık dinamiktir:
  FC27_<squad-adı>_YYYY-MM-DD_HH-MM-SS.json
- İndirme saveAs penceresiyle açılır.
- Chrome normalde "son kullanılan indirme klasörü"nü kendisi hatırlar. Extension, güvenlik nedeniyle
  bilgisayardaki son klasör yolunu okuyup zorla seçmez; tarayıcının native Save As davranışını kullanır.

VERİ
- Tüm gezilen Players sayfaları
- Aktif FIELD ilk 11 ve SUBSTITUTE oyuncuları
- Formation / manager
- Chemistry / chemistry style
- Role+/Role++, PlayStyle/PlayStyle+
- Aktif tactic: positionRoles, roleId, positionUniqueId, focusName
- Build-up, defensive approach, line height

GÜVENLİK
- EA şifresi, cookie, Authorization header veya browser token export edilmez.
- EA Web App private API'sine otomatik istek atılmaz.
- Normal FUT.GG gezinmesi sırasında tarayıcıya gelen response'lar pasif olarak gözlemlenir.
