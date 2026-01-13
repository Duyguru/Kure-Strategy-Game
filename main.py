import pygame
import sys
import random
import asyncio # Web uyumluluğu için

# --- MODERN RENK PALETİ (Flat UI) ---
RENK_ARKA_PLAN = (236, 240, 241)  
RENK_YAN_PANEL = (44, 62, 80)     
RENK_TAHTA_ZEMIN = (52, 73, 94)   
RENK_KART_ZEMIN = (52, 67, 85)    
RENK_KUYU = (40, 55, 70)          

RENK_MOR_TAS = (142, 68, 173)     
RENK_MOR_PARLAK = (187, 143, 206)
RENK_TURUNCU_TAS = (230, 126, 34) 
RENK_TURUNCU_PARLAK = (245, 176, 65)

RENK_YAZI_BEYAZ = (236, 240, 241)
RENK_YAZI_GRI = (189, 195, 199)   
RENK_SECIM = (46, 204, 113)       
RENK_HAMLE_IZI = (241, 196, 15)   
RENK_UYARI = (231, 76, 60)        

BTN_NORMAL = (52, 152, 219)       
BTN_HOVER = (41, 128, 185)        
BTN_CIKIS_NORMAL = (192, 57, 43)  
BTN_CIKIS_HOVER = (150, 40, 27)

# --- AYARLAR ---
GENISLIK, YUKSEKLIK = 1200, 800  
OFSET_X = 40
OFSET_Y = 40
TAHTA_BOYUT = 700
SATIR = 7
KARE = TAHTA_BOYUT // SATIR

# --- TAZOF 2025 KURALLAR METNİ ---
KURALLAR_SAYFA_1 = [
    "1. Oyun İsviçre sistemine göre tek set üzerinden oynanır.",
    "2. Mor oyuncu başlar.",
    "3. Başlangıç taşları yalnızca ileriye ya da çapraza hareket edebilir.",
    "4. Başlangıç sırasından ayrılan taşlar bir daha oraya dönemez.",
    "5. DİKKAT: Taşlar ileri, geri veya çapraz gidebilir. YATAY (SAĞ-SOL) HAREKET YASAKTIR! (Madde 7)",
    "6. Dikey, yatay ya da çaprazda 4'lü dizilim yasaktır.",
    "7. Rakip taşını iki taşının arasına sıkıştıran oyuncu o taşı yer.",
    "8. Kendi isteğiyle araya giren taş yenmez (Güvenli giriş).",
    "9. Hem mor hem turuncu arada kalıyorsa, hamleyi yapan yer."
]

KURALLAR_SAYFA_2 = [
    "10. DİKKAT: Rakibin başlangıç sırasında aynı anda EN FAZLA 1 taşınız bulunabilir. (Madde 12)",
    "11. Rakibinin 4 taşını yiyen oyunu kazanır.",
    "12. Dokunulan taş oynanmak zorundadır.",
    "13. Hatalı hamle, 4'lü yapma veya kural dışı hareket UYARI cezası alır.",
    "14. Toplam 3 uyarı alan oyuncu maçı kaybeder.",
    "15. Oyun TEK SETTİR. Set skoru yoktur, maçı kazanan 1 puan alır.",
    "Revizyon Tarihi: 25.09.2025"
]

class KureOyunu:
    def __init__(self, mod):
        self.mod = mod 
        self.tahta = self.tahta_olustur()
        self.sira = "M" 
        self.secili = None 
        self.son_hamle = None 
        self.son_hamle_goster = False 
        self.yenen_mor = 0  
        self.yenen_turuncu = 0 
        self.uyari_m = 0
        self.uyari_t = 0
        self.mesaj = "Oyun Başladı! Hamle sırası Mor oyuncuda."
        self.oyun_bitti = False
        self.kazanan_kim = None
    
    def tahta_olustur(self):
        t = [["." for _ in range(SATIR)] for _ in range(SATIR)]
        for i in range(SATIR):
            t[0][i] = "M"
            t[6][i] = "T"
        return t

    def reset_oyun(self):
        # Madde 20: Oyun tek set, o yüzden resetlenince her şey sıfırlanır
        self.tahta = self.tahta_olustur()
        self.sira = "M"
        self.secili = None
        self.son_hamle = None 
        self.son_hamle_goster = False
        self.yenen_mor = 0
        self.yenen_turuncu = 0
        self.uyari_m = 0
        self.uyari_t = 0
        self.oyun_bitti = False
        self.kazanan_kim = None
        self.mesaj = "Yeni Oyun Başladı! Başarılar."

    def dortlu_kontrol(self, tahta_sim, oyuncu):
        for i in range(SATIR):
            baslangic_satiri_mi = (oyuncu == "M" and i == 0) or (oyuncu == "T" and i == 6)
            if not baslangic_satiri_mi:
                if tahta_sim[i].count(oyuncu) >= 4: return True
        for i in range(SATIR):
            sutun_sayisi = 0
            for j in range(SATIR):
                if tahta_sim[j][i] == oyuncu: sutun_sayisi += 1
            if sutun_sayisi >= 4: return True
        for d in range(-SATIR + 1, SATIR):
            count = 0
            for r in range(SATIR):
                c = r - d
                if 0 <= c < SATIR:
                    if tahta_sim[r][c] == oyuncu: count += 1
            if count >= 4: return True
        for d in range(2 * SATIR - 1):
            count = 0
            for r in range(SATIR):
                c = d - r
                if 0 <= c < SATIR:
                    if tahta_sim[r][c] == oyuncu: count += 1
            if count >= 4: return True     
        return False

    def hamle_gecerli_mi(self, y1, x1, y2, x2, oyuncu):
        if not (0 <= y2 < SATIR and 0 <= x2 < SATIR): return False, "Sınır dışı hamle."
        hedef = self.tahta[y2][x2]
        if hedef != ".": return False, "Hedef kare dolu."
        
        dy, dx = y2 - y1, x2 - x1
        
        # --- YENİ KURAL (Madde 7): YATAY HAREKET YASAK ---
        # dy (dikey değişim) 0 ise, sadece yatay gidiyor demektir. Yasak.
        if dy == 0: return False, "Yatay hareket yasaktır! (Madde 7)"
        
        if abs(dy) > 1 or abs(dx) > 1: return False, "Taşlar sadece 1 birim ilerleyebilir."
        
        # Başlangıç satırı kuralları (Madde 5)
        if oyuncu == "M" and y1 == 0 and dy != 1: return False, "Başlangıç taşları sadece ileri oynanabilir."
        if oyuncu == "T" and y1 == 6 and dy != -1: return False, "Başlangıç taşları sadece ileri oynanabilir."
        
        # Geri Dönüş Yasağı (Madde 6)
        if (oyuncu == "M" and y2 == 0) or (oyuncu == "T" and y2 == 6): return False, "Başlangıç çizgisine geri dönülemez."
        
        # --- YENİ KURAL (Madde 12): RAKİP SAHADA TAŞ LİMİTİ ---
        # Eğer Mor oyuncu, Turuncu'nun sahasına (6. satır) giriyorsa:
        if oyuncu == "M" and y2 == 6:
            mevcut_tas_sayisi = self.tahta[6].count("M")
            if mevcut_tas_sayisi >= 1:
                return False, "Rakip başlangıç sırasında en fazla 1 taşınız olabilir! (Madde 12)"
        
        # Eğer Turuncu oyuncu, Mor'un sahasına (0. satır) giriyorsa:
        if oyuncu == "T" and y2 == 0:
            mevcut_tas_sayisi = self.tahta[0].count("T")
            if mevcut_tas_sayisi >= 1:
                return False, "Rakip başlangıç sırasında en fazla 1 taşınız olabilir! (Madde 12)"
        
        # 4'lü Kontrolü
        kopya_tahta = [row[:] for row in self.tahta]
        kopya_tahta[y1][x1] = "."
        kopya_tahta[y2][x2] = oyuncu
        if self.dortlu_kontrol(kopya_tahta, oyuncu): return False, "4'lü KURAL İHLALİ! (Madde 8)"
        
        return True, "OK"

    def tas_yeme_kontrol(self, r, c, oyuncu):
        rakip = "T" if oyuncu == "M" else "M"
        yenenler = []
        yonler = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dy, dx in yonler:
            komsu_r, komsu_c = r + dy, c + dx
            uzak_r, uzak_c = r + (dy*2), c + (dx*2)
            if 0 <= uzak_r < SATIR and 0 <= uzak_c < SATIR:
                if self.tahta[komsu_r][komsu_c] == rakip and self.tahta[uzak_r][uzak_c] == oyuncu:
                    yenenler.append((komsu_r, komsu_c))
        return yenenler

    def hamle_yap(self, y1, x1, y2, x2):
        if self.oyun_bitti: return
        durum, aciklama = self.hamle_gecerli_mi(y1, x1, y2, x2, self.sira)
        
        if not durum:
            if self.sira == "M": self.uyari_m += 1
            else: self.uyari_t += 1
            self.mesaj = f"HATALI HAMLE! {aciklama} (Uyarı +1)"
            self.uyari_kontrol()
            self.secili = None 
            return

        self.tahta[y1][x1] = "."
        self.tahta[y2][x2] = self.sira
        self.son_hamle = ((y1, x1), (y2, x2))

        yenenler = self.tas_yeme_kontrol(y2, x2, self.sira)
        if yenenler:
            for yr, yc in yenenler:
                self.tahta[yr][yc] = "." 
                if self.sira == "M": self.yenen_turuncu += 1
                else: self.yenen_mor += 1
            self.mesaj = f"{'Mor' if self.sira=='M' else 'Turuncu'} rakip taşı yedi!"
        else: self.mesaj = f"{'Mor' if self.sira=='M' else 'Turuncu'} hamlesini yaptı."

        self.kazanma_kontrol()
        if not self.oyun_bitti:
            self.sira = "T" if self.sira == "M" else "M"
        self.secili = None

    def yapay_zeka_hamlesi(self):
        oyuncu = "T"
        olasi_hamleler = []
        yeme_hamleleri = []

        for r in range(SATIR):
            for c in range(SATIR):
                if self.tahta[r][c] == oyuncu:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0: continue
                            hedef_r, hedef_c = r + dr, c + dc
                            gecerli, _ = self.hamle_gecerli_mi(r, c, hedef_r, hedef_c, oyuncu)
                            if gecerli:
                                eski_tas = self.tahta[hedef_r][hedef_c]
                                self.tahta[r][c] = "."
                                self.tahta[hedef_r][hedef_c] = oyuncu
                                yenen = self.tas_yeme_kontrol(hedef_r, hedef_c, oyuncu)
                                self.tahta[r][c] = oyuncu
                                self.tahta[hedef_r][hedef_c] = eski_tas

                                hamle_verisi = ((r, c), (hedef_r, hedef_c))
                                if len(yenen) > 0: yeme_hamleleri.append(hamle_verisi)
                                else: olasi_hamleler.append(hamle_verisi)

        secilen_hamle = None
        if yeme_hamleleri:
            secilen_hamle = random.choice(yeme_hamleleri)
        elif olasi_hamleler:
            # Öncelik: İleri gitmek (dr = -1)
            ileri_hamleler = [h for h in olasi_hamleler if h[1][0] < h[0][0]]
            if ileri_hamleler and random.random() > 0.3: 
                secilen_hamle = random.choice(ileri_hamleler)
            else:
                secilen_hamle = random.choice(olasi_hamleler)
        
        if secilen_hamle:
            baslangic, bitis = secilen_hamle
            self.hamle_yap(baslangic[0], baslangic[1], bitis[0], bitis[1])
        else:
            self.sira = "M" 
            self.mesaj = "Bilgisayar hamle yapamadı (Pas)."

    def uyari_kontrol(self):
        # Madde 18: 3. uyarıyı alan turu kaybeder.
        if self.uyari_m >= 3: self.oyunu_bitir("T")
        elif self.uyari_t >= 3: self.oyunu_bitir("M")

    def kazanma_kontrol(self):
        # Madde 13: 4 taş yiyen kazanır.
        if self.yenen_turuncu >= 4: self.oyunu_bitir("M")
        elif self.yenen_mor >= 4: self.oyunu_bitir("T")

    def oyunu_bitir(self, kazanan):
        self.kazanan_kim = kazanan
        kazanan_isim = "MOR" if kazanan == "M" else "TURUNCU"
        self.mesaj = f"TEBRİKLER! OYUNU {kazanan_isim} KAZANDI!"
        self.oyun_bitti = True

# --- YARDIMCI UI FONKSİYONLARI ---
def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_card(surface, x, y, w, h, title, lines, title_color=RENK_TURUNCU_TAS):
    rect = pygame.Rect(x, y, w, h)
    draw_rounded_rect(surface, (30, 40, 50), (x+2, y+2, w, h), 10)
    draw_rounded_rect(surface, RENK_KART_ZEMIN, rect, 10)
    
    font_baslik = pygame.font.SysFont("Arial", 16, bold=True)
    text = font_baslik.render(title, True, title_color)
    surface.blit(text, (x + 15, y + 10))
    
    pygame.draw.line(surface, RENK_YAN_PANEL, (x+10, y+30), (x+w-10, y+30), 2)
    
    font_icerik = pygame.font.SysFont("Arial", 14)
    y_offset = 40
    for line in lines:
        t = font_icerik.render(line, True, RENK_YAZI_GRI)
        surface.blit(t, (x + 15, y + y_offset))
        y_offset += 20

def draw_button(surface, rect, text, hover=False, color=BTN_NORMAL, hover_color=BTN_HOVER):
    c = hover_color if hover else color
    draw_rounded_rect(surface, (30, 30, 30), (rect.x+2, rect.y+3, rect.width, rect.height), 8)
    draw_rounded_rect(surface, c, rect, 8)
    font = pygame.font.SysFont("Arial", 14, bold=True)
    txt = font.render(text, True, RENK_YAZI_BEYAZ)
    txt_rect = txt.get_rect(center=rect.center)
    surface.blit(txt, txt_rect)

def blit_text_wrapped(surface, text, pos, font, color, max_width):
    words = [word.split(' ') for word in text.splitlines()]
    space = font.size(' ')[0]
    x, y = pos
    
    for line in words:
        for word in line:
            word_surface = font.render(word, True, color)
            word_width, word_height = word_surface.get_size()
            
            if x + word_width >= max_width:
                x = pos[0] 
                y += word_height 
            
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]
        y += word_height + 5

# --- KURALLAR EKRANI ---
def kurallari_goster(ekran):
    font_baslik = pygame.font.SysFont("Arial", 30, bold=True)
    font_kural = pygame.font.SysFont("Arial", 18)
    sayfa = 1 
    
    btn_geri_rect = pygame.Rect(40, YUKSEKLIK - 80, 180, 50)
    btn_ileri_rect = pygame.Rect(GENISLIK - 220, YUKSEKLIK - 80, 180, 50)
    
    calisiyor = True
    while calisiyor:
        ekran.fill(RENK_YAN_PANEL)
        mx, my = pygame.mouse.get_pos()
        
        baslik = font_baslik.render(f"TAZOF 2025 TURNUVA KURALLARI ({sayfa}/2)", True, RENK_TURUNCU_TAS)
        ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 40))
        
        aktif_liste = KURALLAR_SAYFA_1 if sayfa == 1 else KURALLAR_SAYFA_2
        
        start_y = 100
        for kural in aktif_liste:
            blit_text_wrapped(ekran, kural, (50, start_y), font_kural, RENK_YAZI_BEYAZ, GENISLIK - 50)
            words_len = len(kural)
            if words_len > 90: start_y += 60 
            else: start_y += 40 

        draw_button(ekran, btn_geri_rect, "ANA MENÜ" if sayfa == 1 else "ÖNCEKİ SAYFA", 
                    btn_geri_rect.collidepoint(mx, my), BTN_CIKIS_NORMAL, BTN_CIKIS_HOVER)
        
        if sayfa == 1:
            draw_button(ekran, btn_ileri_rect, "SONRAKİ SAYFA >", btn_ileri_rect.collidepoint(mx, my))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_geri_rect.collidepoint(mx, my):
                    if sayfa == 2: sayfa = 1
                    else: calisiyor = False 
                
                if sayfa == 1 and btn_ileri_rect.collidepoint(mx, my):
                    sayfa = 2
        
        pygame.display.flip()

# --- ANA PROGRAM ---
async def main():
    pygame.init()
    ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
    pygame.display.set_caption("KÜRE Strateji Oyunu - 2025 Edition")
    
    font_menu = pygame.font.SysFont("Arial", 50, bold=True)
    font_alt = pygame.font.SysFont("Arial", 20)
    
    clock = pygame.time.Clock()
    program_calisiyor = True
    
    while program_calisiyor:
        secilen_mod = 0
        menu_aktif = True
        
        while menu_aktif and program_calisiyor:
            ekran.fill(RENK_YAN_PANEL)
            
            pygame.draw.circle(ekran, (50, 70, 90), (GENISLIK//2, YUKSEKLIK//2), 300, 2)
            pygame.draw.circle(ekran, (50, 70, 90), (GENISLIK//2, YUKSEKLIK//2), 400, 2)
            
            baslik = font_menu.render("KÜRE 2025", True, RENK_YAZI_BEYAZ)
            baslik_golge = font_menu.render("KÜRE 2025", True, (30,30,30))
            alt_baslik = font_alt.render("Resmi Turnuva Kuralları", True, RENK_TURUNCU_TAS)
            
            ekran.blit(baslik_golge, (GENISLIK//2 - baslik.get_width()//2 + 3, 103))
            ekran.blit(baslik, (GENISLIK//2 - baslik.get_width()//2, 100))
            ekran.blit(alt_baslik, (GENISLIK//2 - alt_baslik.get_width()//2, 160))
            
            btn1_rect = pygame.Rect(GENISLIK//2 - 120, 250, 240, 50)
            btn2_rect = pygame.Rect(GENISLIK//2 - 120, 320, 240, 50)
            btn_kurallar_rect = pygame.Rect(GENISLIK//2 - 120, 390, 240, 50)
            btn_exit_rect = pygame.Rect(GENISLIK//2 - 120, 500, 240, 50)
            
            mx, my = pygame.mouse.get_pos()
            
            draw_button(ekran, btn1_rect, "1. Arkadaşınla Oyna", btn1_rect.collidepoint(mx, my))
            draw_button(ekran, btn2_rect, "2. Bilgisayara Karşı", btn2_rect.collidepoint(mx, my))
            draw_button(ekran, btn_kurallar_rect, "KURALLAR", btn_kurallar_rect.collidepoint(mx, my), (142, 68, 173), (155, 89, 182))
            draw_button(ekran, btn_exit_rect, "ÇIKIŞ", btn_exit_rect.collidepoint(mx, my), BTN_CIKIS_NORMAL, BTN_CIKIS_HOVER)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    program_calisiyor = False
                    menu_aktif = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn1_rect.collidepoint(mx, my): secilen_mod = 1; menu_aktif = False
                    elif btn2_rect.collidepoint(mx, my): secilen_mod = 2; menu_aktif = False
                    elif btn_kurallar_rect.collidepoint(mx, my): 
                        kurallari_goster(ekran) 
                    elif btn_exit_rect.collidepoint(mx, my): program_calisiyor = False; menu_aktif = False
            
            pygame.display.flip()
            await asyncio.sleep(0)
        
        if not program_calisiyor: break

        oyun = KureOyunu(secilen_mod)
        ai_timer = None
        
        panel_x = OFSET_X + TAHTA_BOYUT + 40
        btn_menu_rect = pygame.Rect(panel_x, 30, 100, 35)
        btn_son_hamle_rect = pygame.Rect(panel_x + 110, 30, 180, 35)

        oyun_aktif = True
        while oyun_aktif and program_calisiyor:
            ekran.fill(RENK_ARKA_PLAN) 
            pygame.draw.rect(ekran, RENK_YAN_PANEL, (panel_x - 20, 0, GENISLIK - (panel_x - 20), YUKSEKLIK))

            if oyun.mod == 2 and oyun.sira == "T" and not oyun.oyun_bitti:
                current_time = pygame.time.get_ticks()
                if ai_timer is None: ai_timer = current_time
                if current_time - ai_timer > 600:
                    oyun.yapay_zeka_hamlesi()
                    ai_timer = None
            else:
                ai_timer = None

            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    oyun_aktif = False
                    program_calisiyor = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_menu_rect.collidepoint(mx, my):
                        oyun_aktif = False; continue

                    if oyun.oyun_bitti:
                        # Tek tıklama ile oyunu yeniden başlat
                        oyun.reset_oyun()
                        continue
                    
                    if btn_son_hamle_rect.collidepoint(mx, my):
                        oyun.son_hamle_goster = not oyun.son_hamle_goster
                        continue

                    if oyun.mod == 2 and oyun.sira == "T": continue 

                    if mx < OFSET_X or mx > OFSET_X + TAHTA_BOYUT or my < OFSET_Y or my > OFSET_Y + TAHTA_BOYUT:
                        continue
                        
                    sutun = (mx - OFSET_X) // KARE
                    satir = (my - OFSET_Y) // KARE
                    
                    if 0 <= satir < SATIR and 0 <= sutun < SATIR:
                        if oyun.secili is None:
                            tas = oyun.tahta[satir][sutun]
                            if tas == oyun.sira: oyun.secili = (satir, sutun)
                        else:
                            y1, x1 = oyun.secili
                            if (y1, x1) == (satir, sutun): oyun.secili = None
                            else: oyun.hamle_yap(y1, x1, satir, sutun)

            # --- ÇİZİM ---
            pygame.draw.rect(ekran, (180, 190, 190), (OFSET_X+5, OFSET_Y+5, TAHTA_BOYUT, TAHTA_BOYUT), border_radius=5)
            pygame.draw.rect(ekran, RENK_TAHTA_ZEMIN, (OFSET_X, OFSET_Y, TAHTA_BOYUT, TAHTA_BOYUT), border_radius=5)
            
            if oyun.son_hamle_goster and oyun.son_hamle:
                (r1, c1), (r2, c2) = oyun.son_hamle
                s_rect = (OFSET_X + c1 * KARE, OFSET_Y + r1 * KARE, KARE, KARE)
                e_rect = (OFSET_X + c2 * KARE, OFSET_Y + r2 * KARE, KARE, KARE)
                pygame.draw.rect(ekran, RENK_HAMLE_IZI, s_rect)
                pygame.draw.rect(ekran, RENK_HAMLE_IZI, e_rect)

            for r in range(SATIR):
                for c in range(SATIR):
                    x = OFSET_X + c * KARE
                    y = OFSET_Y + r * KARE
                    merkez = (x + KARE//2, y + KARE//2)
                    pygame.draw.circle(ekran, RENK_KUYU, merkez, KARE//2 - 8)
                    pygame.draw.circle(ekran, (60, 80, 100), merkez, KARE//2 - 10) 

                    tas = oyun.tahta[r][c]
                    if tas != ".":
                        color = RENK_MOR_TAS if tas == "M" else RENK_TURUNCU_TAS
                        highlight = RENK_MOR_PARLAK if tas == "M" else RENK_TURUNCU_PARLAK
                        pygame.draw.circle(ekran, color, merkez, KARE//3)
                        pygame.draw.circle(ekran, highlight, (merkez[0]-8, merkez[1]-8), KARE//10)

            if oyun.secili and not oyun.oyun_bitti:
                sr, sc = oyun.secili
                pygame.draw.rect(ekran, RENK_SECIM, (OFSET_X + sc * KARE, OFSET_Y + sr * KARE, KARE, KARE), 3, border_radius=5)
                for r in range(SATIR):
                    for c in range(SATIR):
                        gecerli, _ = oyun.hamle_gecerli_mi(sr, sc, r, c, oyun.sira)
                        if gecerli:
                            pygame.draw.circle(ekran, RENK_HAMLE_IZI, (OFSET_X+c*KARE+KARE//2, OFSET_Y+r*KARE+KARE//2), 8)

            draw_button(ekran, btn_menu_rect, "< MENÜ", btn_menu_rect.collidepoint(mx, my), (90, 100, 110))
            draw_button(ekran, btn_son_hamle_rect, "Son Hamleyi Göster", btn_son_hamle_rect.collidepoint(mx, my),
                        color=BTN_NORMAL if not oyun.son_hamle_goster else BTN_HOVER)

            card_width = 300
            sira_metni = "MOR OYUNCU" if oyun.sira == "M" else "TURUNCU OYUNCU"
            sira_renk = RENK_MOR_TAS if oyun.sira == "M" else RENK_TURUNCU_TAS
            draw_card(ekran, panel_x, 90, card_width, 100, "OYUN DURUMU", 
                      [f"Sıra Kimde: {sira_metni}", 
                       f"Mod: {'Bilgisayara Karşı' if oyun.mod==2 else 'İki Kişilik'}"], 
                      title_color=sira_renk)

            # Skor Kartı (Set sistemi kalktı, düz skor var)
            draw_card(ekran, panel_x, 210, card_width, 140, "MAÇ DURUMU (TEK SET)",
                      [f"Mor'un Yediği Taş:  {oyun.yenen_turuncu}",
                       f"Turuncu'nun Yediği: {oyun.yenen_mor}",
                       "",
                       "4 Taş yiyen oyunu kazanır."])

            draw_card(ekran, panel_x, 370, card_width, 120, "CEZA PUANLARI (Max 3)",
                      [f"Mor Uyarı:      {oyun.uyari_m} / 3",
                       f"Turuncu Uyarı:  {oyun.uyari_t} / 3",
                       "",
                       "3 Uyarı alan kaybeder!"],
                      title_color=RENK_UYARI)

            msg_rect = pygame.Rect(panel_x, 520, card_width, 80)
            draw_rounded_rect(ekran, (40, 50, 60), msg_rect, 10)
            font_msg = pygame.font.SysFont("Arial", 14)
            
            words = oyun.mesaj.split(' ')
            lines = []
            curr_line = ""
            for w in words:
                if len(curr_line) + len(w) < 35: curr_line += w + " "
                else: lines.append(curr_line); curr_line = w + " "
            lines.append(curr_line)
            
            my_off = 15
            for line in lines:
                t = font_msg.render(line, True, RENK_YAZI_BEYAZ)
                ekran.blit(t, (panel_x + 10, 520 + my_off))
                my_off += 20

            pygame.display.flip()
            await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())