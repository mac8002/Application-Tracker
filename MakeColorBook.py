from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
import math

PAGE_SIZE = (8.5 * inch, 8.5 * inch)
W, H = PAGE_SIZE

def new_canvas(filename):
    c = canvas.Canvas(filename, pagesize=PAGE_SIZE)
    c.setTitle("Magical Unicorns & Fairies Coloring Book")
    return c

def draw_star(c, cx, cy, r_out, r_in, points=5):
    path = c.beginPath()
    for i in range(points * 2):
        angle = math.radians(i * 180 / points - 90)
        r = r_out if i % 2 == 0 else r_in
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0: path.moveTo(x, y)
        else: path.lineTo(x, y)
    path.close()
    c.drawPath(path, fill=1, stroke=1)

def page_bg(c, color="#FFF0F5"):
    c.setFillColor(HexColor(color))
    c.rect(0, 0, W, H, fill=1, stroke=0)

def page_border(c, color1="#CE93D8", color2="#F48FB1"):
    c.setStrokeColor(HexColor(color1)); c.setLineWidth(8)
    c.rect(18, 18, W-36, H-36, fill=0, stroke=1)
    c.setStrokeColor(HexColor(color2)); c.setLineWidth(3)
    c.rect(30, 30, W-60, H-60, fill=0, stroke=1)

def page_header(c, title, page_num):
    page_bg(c)
    page_border(c)
    c.setFillColor(HexColor("#9C27B0")); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W/2, H-58, title)
    c.setFillColor(HexColor("#90A4AE")); c.setFont("Helvetica", 12)
    c.drawCentredString(W/2, 35, f"Page {page_num}")

def draw_sparkles(c, positions):
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(0.8)
    for sx, sy, sr in positions:
        draw_star(c, sx, sy, sr, sr*0.4, 4)

def draw_cover(c):
    page_bg(c, "#F3E5F5")
    page_border(c, "#AB47BC", "#CE93D8")

    # Title banner
    c.setFillColor(HexColor("#9C27B0"))
    c.roundRect(50, H-210, W-100, 150, 25, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(W/2, H-125, "Magical Unicorns")
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W/2, H-170, "& Fairies")

    # Big unicorn head
    cx, cy = W/2, H/2 - 20

    # Body
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-110, cy-140, cx+110, cy+60, fill=1, stroke=1)

    # Neck
    p = c.beginPath()
    p.moveTo(cx-40, cy+55)
    p.lineTo(cx-50, cy+130)
    p.lineTo(cx+50, cy+130)
    p.lineTo(cx+40, cy+55)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Head
    c.ellipse(cx-75, cy+100, cx+75, cy+230, fill=1, stroke=1)

    # Horn
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, cy+280)
    p.lineTo(cx-15, cy+230)
    p.lineTo(cx+15, cy+230)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Horn stripes
    c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(1.5)
    for hy in [cy+243, cy+255, cy+267]:
        c.line(cx-10*(1-(hy-cy-230)/50), hy, cx+10*(1-(hy-cy-230)/50), hy)

    # Mane (flowing)
    mane_colors = ["#F48FB1", "#CE93D8", "#81D4FA", "#A5D6A7", "#FFD54F"]
    for i, mc in enumerate(mane_colors):
        c.setFillColor(HexColor(mc)); c.setStrokeColor(black); c.setLineWidth(1)
        offset = i * 8
        p = c.beginPath()
        p.moveTo(cx-60+offset, cy+230)
        p.curveTo(cx-90+offset, cy+200, cx-100+offset, cy+150, cx-80+offset, cy+80)
        p.curveTo(cx-70+offset, cy+50, cx-55+offset, cy+30, cx-45+offset+10, cy-10)
        p.lineTo(cx-35+offset+10, cy-10)
        p.curveTo(cx-50+offset+10, cy+35, cx-60+offset+10, cy+55, cx-70+offset+10, cy+85)
        p.curveTo(cx-88+offset+10, cy+155, cx-78+offset+10, cy+205, cx-48+offset+10, cy+230)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Ears
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx-60, cy+218)
    p.lineTo(cx-80, cy+265)
    p.lineTo(cx-35, cy+235)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(HexColor("#F8BBD0"))
    p = c.beginPath()
    p.moveTo(cx-58, cy+219)
    p.lineTo(cx-74, cy+257)
    p.lineTo(cx-40, cy+234)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Eyes (big sparkly)
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx+10, cy+155, cx+55, cy+195, fill=1, stroke=1)
    c.setFillColor(HexColor("#CE93D8"))
    c.ellipse(cx+15, cy+158, cx+50, cy+192, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx+20, cy+162, cx+45, cy+188, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx+28, cy+180, 5, fill=1, stroke=0)
    c.circle(cx+40, cy+170, 3, fill=1, stroke=0)

    # Eyelashes
    c.setStrokeColor(black); c.setLineWidth(1.5)
    for ex, ey, ex2, ey2 in [(cx+15,cy+193,cx+10,cy+202),(cx+25,cy+195,cx+22,cy+205),(cx+35,cy+194,cx+35,cy+204),(cx+45,cy+191,cx+48,cy+200)]:
        c.line(ex, ey, ex2, ey2)

    # Nose
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(black); c.setLineWidth(1)
    c.ellipse(cx+15, cy+120, cx+45, cy+135, fill=1, stroke=1)
    c.setFillColor(HexColor("#F48FB1"))
    c.ellipse(cx+20, cy+122, cx+30, cy+130, fill=1, stroke=0)
    c.ellipse(cx+32, cy+122, cx+42, cy+130, fill=1, stroke=0)

    # Rainbow tail
    tail_colors = ["#F44336","#FF9800","#FFEB3B","#4CAF50","#2196F3","#9C27B0"]
    for i, tc in enumerate(tail_colors):
        c.setFillColor(HexColor(tc)); c.setStrokeColor(black); c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(cx+105, cy-30+i*5)
        p.curveTo(cx+145, cy-20+i*5, cx+165, cy-60+i*5, cx+150, cy-100+i*5)
        p.curveTo(cx+145, cy-115+i*5, cx+135, cy-120+i*5, cx+128, cy-112+i*5)
        p.curveTo(cx+140, cy-72+i*5, cx+125, cy-38+i*5, cx+88, cy-44+i*5)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Sparkles
    draw_sparkles(c, [(80,H-270,12),(W-80,H-270,10),(70,200,14),(W-70,200,11),(W/2-160,H/2+20,9),(W/2+160,H/2+20,9)])

    # Subtitle
    c.setFillColor(HexColor("#6A1B9A")); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, 100, "For Toddlers & Young Kids")
    c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 14)
    c.drawCentredString(W/2, 72, "Ages 2–7  •  10 Magical Pages")
    c.showPage()

def draw_unicorn_page(c):
    page_header(c, "Beautiful Unicorn ✨", 1)
    cx, cy = W/2, H/2 - 30

    # Body
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-130, cy-80, cx+130, cy+80, fill=1, stroke=1)

    # Legs
    for lx in [cx-90, cx-40, cx+40, cx+90]:
        c.rect(lx-16, cy-170, 32, 95, fill=1, stroke=1)
        c.ellipse(lx-20, cy-185, lx+20, cy-155, fill=1, stroke=1)

    # Neck
    p = c.beginPath()
    p.moveTo(cx+50, cy+65)
    p.lineTo(cx+30, cy+150)
    p.lineTo(cx+100, cy+150)
    p.lineTo(cx+115, cy+65)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Head
    c.ellipse(cx+20, cy+130, cx+130, cy+240, fill=1, stroke=1)

    # Horn
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx+75, cy+295)
    p.lineTo(cx+60, cy+240)
    p.lineTo(cx+90, cy+240)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Horn rings
    c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(1.5)
    for hy in [cy+250, cy+262, cy+274, cy+285]:
        frac = (hy - (cy+240)) / 55
        hw = 14*(1-frac)
        c.line(cx+75-hw, hy, cx+75+hw, hy)

    # Ear
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx+30, cy+230)
    p.lineTo(cx+15, cy+270)
    p.lineTo(cx+50, cy+245)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(HexColor("#F8BBD0"))
    p = c.beginPath()
    p.moveTo(cx+32, cy+232)
    p.lineTo(cx+20, cy+263)
    p.lineTo(cx+47, cy+244)
    p.close()
    c.drawPath(p, fill=0, stroke=0); c.drawPath(p, fill=1, stroke=0)

    # Eye
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx+95, cy+190, cx+128, cy+218, fill=1, stroke=1)
    c.setFillColor(HexColor("#CE93D8"))
    c.ellipse(cx+99, cy+193, cx+124, cy+215, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx+104, cy+197, cx+119, cy+211, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx+109, cy+207, 4, fill=1, stroke=0)

    # Nostril
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(black); c.setLineWidth(1)
    c.ellipse(cx+92, cy+155, cx+108, cy+165, fill=1, stroke=1)

    # Mane
    mane_colors = ["#F48FB1","#CE93D8","#81D4FA","#FFD54F","#A5D6A7"]
    for i, mc in enumerate(mane_colors):
        c.setFillColor(HexColor(mc)); c.setStrokeColor(black); c.setLineWidth(1)
        off = i * 9
        p = c.beginPath()
        p.moveTo(cx+30+off, cy+240)
        p.curveTo(cx+5+off, cy+200, cx-5+off, cy+140, cx+20+off, cy+80)
        p.curveTo(cx+30+off, cy+50, cx+45+off, cy+30, cx+50+off, cy-10)
        p.lineTo(cx+60+off, cy-10)
        p.curveTo(cx+58+off, cy+35, cx+42+off, cy+55, cx+32+off, cy+85)
        p.curveTo(cx+18+off, cy+145, cx+25+off, cy+208, cx+48+off, cy+240)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Tail
    tail_colors = ["#F44336","#FF9800","#FFEB3B","#4CAF50","#2196F3","#9C27B0"]
    for i, tc in enumerate(tail_colors):
        c.setFillColor(HexColor(tc)); c.setStrokeColor(black); c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(cx-125, cy+i*5)
        p.curveTo(cx-165, cy+20+i*5, cx-175, cy-40+i*5, cx-155, cy-80+i*5)
        p.curveTo(cx-150, cy-92+i*5, cx-140, cy-95+i*5, cx-135, cy-90+i*5)
        p.curveTo(cx-148, cy-55+i*5, cx-140, cy-20+i*5, cx-105, cy-28+i*5)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Hooves
    c.setFillColor(HexColor("#CE93D8")); c.setStrokeColor(black); c.setLineWidth(2)
    for lx in [cx-90, cx-40, cx+40, cx+90]:
        c.rect(lx-18, cy-195, 36, 18, fill=1, stroke=1)

    # Stars & flowers
    draw_sparkles(c, [(70,180,12),(W-70,180,12),(70,H-200,10),(W-70,H-200,10)])
    c.showPage()

def draw_fairy_page(c):
    page_header(c, "Flora the Fairy 🧚", 2)
    cx, cy = W/2, H/2

    # Wings (4 petals)
    wing_colors = [("#E1BEE7","#CE93D8"),("#BBDEFB","#90CAF9")]
    for i, (wfill, wstroke) in enumerate(wing_colors):
        # Upper wings
        c.setFillColor(HexColor(wfill)); c.setStrokeColor(HexColor(wstroke)); c.setLineWidth(2)
        flip = -1 if i == 0 else 1
        p = c.beginPath()
        p.moveTo(cx, cy+60)
        p.curveTo(cx+flip*20, cy+120, cx+flip*130, cy+150, cx+flip*140, cy+70)
        p.curveTo(cx+flip*145, cy+10, cx+flip*70, cy-20, cx, cy+60)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        # Lower wings
        p = c.beginPath()
        p.moveTo(cx, cy+60)
        p.curveTo(cx+flip*20, cy+20, cx+flip*100, cy-30, cx+flip*90, cy-90)
        p.curveTo(cx+flip*82, cy-130, cx+flip*30, cy-110, cx, cy+60)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Wing details (veins)
    c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(0.8)
    c.line(cx, cy+60, cx+100, cy+110)
    c.line(cx, cy+60, cx-100, cy+110)
    c.line(cx, cy+60, cx+65, cy-60)
    c.line(cx, cy+60, cx-65, cy-60)

    # Body
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx-18, cy-30, cx+18, cy+80, fill=1, stroke=1)

    # Dress
    c.setFillColor(HexColor("#CE93D8")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx-18, cy+10)
    p.lineTo(cx-50, cy-80)
    p.lineTo(cx+50, cy-80)
    p.lineTo(cx+18, cy+10)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Dress trim
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(black); c.setLineWidth(1)
    p = c.beginPath()
    p.moveTo(cx-50, cy-80)
    p.curveTo(cx-30, cy-65, cx, cy-60, cx+30, cy-65)
    p.curveTo(cx+40, cy-68, cx+50, cy-80, cx+50, cy-80)
    p.lineTo(cx+58, cy-95)
    p.curveTo(cx+30, cy-78, cx, cy-73, cx-30, cy-78)
    p.lineTo(cx-58, cy-95)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Head
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    c.circle(cx, cy+115, 45, fill=1, stroke=1)

    # Hair
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.ellipse(cx-45, cy+100, cx+45, cy+165, fill=1, stroke=1)
    # Hair details
    c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(1)
    for hx in [-30,-15,0,15,30]:
        c.line(cx+hx, cy+162, cx+hx, cy+180)

    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.ellipse(cx-22, cy+108, cx-4, cy+128, fill=1, stroke=1)
    c.ellipse(cx+4, cy+108, cx+22, cy+128, fill=1, stroke=1)
    c.setFillColor(HexColor("#7986CB"))
    c.ellipse(cx-19, cy+111, cx-7, cy+125, fill=1, stroke=0)
    c.ellipse(cx+7, cy+111, cx+19, cy+125, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-17, cy+113, cx-9, cy+123, fill=1, stroke=0)
    c.ellipse(cx+9, cy+113, cx+17, cy+123, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-14, cy+120, 3, fill=1, stroke=0)
    c.circle(cx+10, cy+120, 3, fill=1, stroke=0)
    # Eyelashes
    c.setStrokeColor(black); c.setLineWidth(1)
    for ex, ey, ex2, ey2 in [(cx-20,cy+128,cx-22,cy+134),(cx-13,cy+129,cx-13,cy+135),(cx-6,cy+128,cx-4,cy+134)]:
        c.line(ex, ey, ex2, ey2)
    for ex, ey, ex2, ey2 in [(cx+6,cy+128,cx+4,cy+134),(cx+13,cy+129,cx+13,cy+135),(cx+20,cy+128,cx+22,cy+134)]:
        c.line(ex, ey, ex2, ey2)

    # Smile
    c.setStrokeColor(HexColor("#F06292")); c.setLineWidth(2)
    c.arc(cx-15, cy+95, cx+15, cy+115, startAng=0, extent=180)

    # Cheeks
    c.setFillColor(HexColor("#FFCDD2")); c.setStrokeColor(HexColor("#EF9A9A")); c.setLineWidth(0.5)
    c.ellipse(cx-38, cy+102, cx-18, cy+113, fill=1, stroke=1)
    c.ellipse(cx+18, cy+102, cx+38, cy+113, fill=1, stroke=1)

    # Arms
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    # Left arm
    p = c.beginPath()
    p.moveTo(cx-18, cy+50)
    p.curveTo(cx-60, cy+60, cx-80, cy+20, cx-70, cy-10)
    p.lineTo(cx-60, cy-5)
    p.curveTo(cx-68, cy+15, cx-52, cy+48, cx-10, cy+40)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Right arm
    p = c.beginPath()
    p.moveTo(cx+18, cy+50)
    p.curveTo(cx+60, cy+60, cx+80, cy+20, cx+70, cy-10)
    p.lineTo(cx+60, cy-5)
    p.curveTo(cx+68, cy+15, cx+52, cy+48, cx+10, cy+40)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Wand
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(3)
    c.line(cx+68, cy-12, cx+110, cy+40)
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(1.5)
    draw_star(c, cx+115, cy+45, 18, 7)

    # Legs
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx-20, cy-95, cx-2, cy-60, fill=1, stroke=1)
    c.ellipse(cx+2, cy-95, cx+20, cy-60, fill=1, stroke=1)
    # Shoes
    c.setFillColor(HexColor("#CE93D8"))
    c.ellipse(cx-26, cy-108, cx+0, cy-88, fill=1, stroke=1)
    c.ellipse(cx+0, cy-108, cx+26, cy-88, fill=1, stroke=1)

    # Magic sparkles
    draw_sparkles(c, [(cx+130,cy+80,14),(cx+115,cy+20,10),(cx-140,cy+80,12),(W/2-160,100,10),(W/2+160,100,10),(80,H-180,12),(W-80,H-180,12)])
    c.showPage()

def draw_rainbow_unicorn_page(c):
    page_header(c, "Rainbow Unicorn 🌈", 3)
    cx, cy = W/2, H/2 - 20

    # Rainbow arch
    rainbow_colors = ["#F44336","#FF9800","#FFEB3B","#4CAF50","#2196F3","#9C27B0"]
    for i, rc in enumerate(rainbow_colors):
        c.setStrokeColor(HexColor(rc)); c.setLineWidth(18)
        c.setFillColor(HexColor(rc))
        r = 220 - i*18
        c.arc(cx-r, cy-180, cx+r, cy-180+r*2, startAng=0, extent=180)

    # Clouds at rainbow ends
    for cloud_cx in [cx-215, cx+215]:
        c.setFillColor(white); c.setStrokeColor(HexColor("#90A4AE")); c.setLineWidth(2)
        for cbx, cby, cbr in [(0,-180,25),(20,-168,22),(-20,-168,22),(0,-158,20)]:
            c.circle(cloud_cx+cbx, cy+cby, cbr, fill=1, stroke=1)

    # Unicorn body
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-120, cy-60, cx+120, cy+80, fill=1, stroke=1)

    # Legs
    for lx in [cx-85, cx-35, cx+35, cx+85]:
        c.rect(lx-15, cy-155, 30, 100, fill=1, stroke=1)
        c.ellipse(lx-18, cy-168, lx+18, cy-142, fill=1, stroke=1)

    # Neck
    p = c.beginPath()
    p.moveTo(cx+45, cy+72)
    p.lineTo(cx+25, cy+155)
    p.lineTo(cx+95, cy+155)
    p.lineTo(cx+110, cy+72)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Head
    c.ellipse(cx+15, cy+130, cx+130, cy+240, fill=1, stroke=1)

    # Horn
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx+72, cy+296)
    p.lineTo(cx+58, cy+240)
    p.lineTo(cx+86, cy+240)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Eye
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx+92, cy+190, cx+124, cy+216, fill=1, stroke=1)
    c.setFillColor(HexColor("#81D4FA"))
    c.ellipse(cx+96, cy+193, cx+120, cy+213, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx+100, cy+196, cx+116, cy+210, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx+106, cy+205, 4, fill=1, stroke=0)

    # Mane
    mane_colors = ["#F44336","#FF9800","#FFEB3B","#4CAF50","#2196F3","#9C27B0"]
    for i, mc in enumerate(mane_colors):
        c.setFillColor(HexColor(mc)); c.setStrokeColor(black); c.setLineWidth(1)
        off = i * 7
        p = c.beginPath()
        p.moveTo(cx+25+off, cy+240)
        p.curveTo(cx+5+off, cy+195, cx+10+off, cy+140, cx+25+off, cy+80)
        p.curveTo(cx+35+off, cy+50, cx+45+off, cy+20, cx+48+off, cy-10)
        p.lineTo(cx+58+off, cy-10)
        p.curveTo(cx+56+off, cy+25, cx+46+off, cy+56, cx+36+off, cy+86)
        p.curveTo(cx+22+off, cy+145, cx+18+off, cy+200, cx+40+off, cy+240)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Tail
    for i, tc in enumerate(mane_colors):
        c.setFillColor(HexColor(tc)); c.setStrokeColor(black); c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(cx-118, cy+i*5)
        p.curveTo(cx-160, cy+20+i*5, cx-170, cy-30+i*5, cx-155, cy-75+i*5)
        p.curveTo(cx-148, cy-92+i*5, cx-138, cy-96+i*5, cx-132, cy-90+i*5)
        p.curveTo(cx-145, cy-56+i*5, cx-136, cy-20+i*5, cx-100, cy-28+i*5)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Stars
    draw_sparkles(c, [(70,H-230,12),(W-70,H-230,12),(70,100,10),(W-70,100,10)])
    c.showPage()

def draw_magic_castle_page(c):
    page_header(c, "The Magic Castle 🏰", 4)
    cx, cy = W/2, H/2

    # Sky with stars
    draw_sparkles(c, [(80,H-180,10),(130,H-210,8),(W-80,H-180,10),(W-130,H-210,8),(W/2,H-190,12),(W/2-100,H-160,7),(W/2+100,H-160,7)])

    # Moon
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(HexColor("#FFD54F")); c.setLineWidth(2)
    c.circle(W-100, H-200, 35, fill=1, stroke=1)

    # Ground
    c.setFillColor(HexColor("#C8E6C9")); c.setStrokeColor(HexColor("#A5D6A7")); c.setLineWidth(2)
    c.rect(40, 60, W-80, 120, fill=1, stroke=1)

    # Castle base
    base_x, base_y, base_w, base_h = cx-150, 160, 300, 250
    c.setFillColor(HexColor("#E1BEE7")); c.setStrokeColor(black); c.setLineWidth(3)
    c.rect(base_x, base_y, base_w, base_h, fill=1, stroke=1)

    # Battlements on top
    for bx in range(int(base_x), int(base_x+base_w), 30):
        c.rect(bx, base_y+base_h, 20, 25, fill=1, stroke=1)

    # Windows
    window_positions = [(cx-80, 280), (cx, 280), (cx+80, 280),(cx-80, 360), (cx+80, 360)]
    for wx, wy in window_positions:
        c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(2)
        c.roundRect(wx-18, wy, 36, 45, 18, fill=1, stroke=1)
        c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
        c.line(wx, wy, wx, wy+45)
        c.line(wx-18, wy+22, wx+18, wy+22)

    # Main door
    c.setFillColor(HexColor("#8D6E63")); c.setStrokeColor(black); c.setLineWidth(2)
    c.roundRect(cx-30, 160, 60, 90, 30, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD700"))
    c.circle(cx+15, 210, 5, fill=1, stroke=1)

    # Towers
    for tx in [cx-165, cx+165]:
        c.setFillColor(HexColor("#CE93D8")); c.setStrokeColor(black); c.setLineWidth(3)
        c.rect(tx-35, 200, 70, 230, fill=1, stroke=1)
        # Tower battlements
        for tbx in range(int(tx-35), int(tx+35), 20):
            c.rect(tbx, 430, 15, 20, fill=1, stroke=1)
        # Tower roof (cone)
        c.setFillColor(HexColor("#9C27B0"))
        p = c.beginPath()
        p.moveTo(tx, 510)
        p.lineTo(tx-40, 430)
        p.lineTo(tx+40, 430)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        # Tower window
        c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(2)
        c.roundRect(tx-16, 310, 32, 45, 16, fill=1, stroke=1)
        # Flag
        c.setStrokeColor(HexColor("#9C27B0")); c.setLineWidth(2)
        c.line(tx, 510, tx, 545)
        c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(tx, 545)
        p.lineTo(tx+25, 537)
        p.lineTo(tx, 530)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Main roof
    c.setFillColor(HexColor("#9C27B0")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, 460)
    p.lineTo(cx-160, 410)
    p.lineTo(cx+160, 410)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Flag on main roof
    c.setStrokeColor(HexColor("#9C27B0")); c.setLineWidth(2)
    c.line(cx, 460, cx, 495)
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(black); c.setLineWidth(1)
    draw_star(c, cx+15, 490, 12, 5)

    # Clouds
    for cloud_cx, cloud_cy in [(100, H-180), (W-100, H-180)]:
        c.setFillColor(white); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1.5)
        for cbx, cby, cbr in [(0,0,20),(18,10,17),(-18,10,17),(0,18,15)]:
            c.circle(cloud_cx+cbx, cloud_cy+cby, cbr, fill=1, stroke=1)

    # Rainbow
    rainbow_colors = ["#F44336","#FF9800","#FFEB3B","#4CAF50","#2196F3","#9C27B0"]
    for i, rc in enumerate(rainbow_colors):
        c.setStrokeColor(HexColor(rc)); c.setLineWidth(10)
        r = 160 - i*13
        c.arc(80-r, H-320, 80+r, H-320+r*2, startAng=0, extent=90)

    c.showPage()

def draw_fairy_garden_page(c):
    page_header(c, "The Fairy Garden 🌸", 5)

    # Ground
    c.setFillColor(HexColor("#DCEDC8")); c.setStrokeColor(HexColor("#AED581")); c.setLineWidth(2)
    c.rect(40, 50, W-80, 130, fill=1, stroke=1)

    # Big mushroom house
    mx, my = W/2, 200
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(mx-90, my+80, mx+90, my+230, fill=1, stroke=1)
    # Mushroom spots
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1)
    for sx, sy, sr in [(-40,150,15),(20,130,12),(-10,175,10),(45,165,13),(-55,185,9)]:
        c.circle(mx+sx, my+sy, sr, fill=1, stroke=1)
    # Mushroom stem
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(2)
    c.rect(mx-40, my, 80, 90, fill=1, stroke=1)
    # Door
    c.setFillColor(HexColor("#8D6E63")); c.setStrokeColor(black); c.setLineWidth(2)
    c.roundRect(mx-20, my, 40, 60, 20, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD700"))
    c.circle(mx+12, my+35, 4, fill=1, stroke=1)
    # Window
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.circle(mx, my+110, 16, fill=1, stroke=1)
    c.line(mx, my+94, mx, my+126)
    c.line(mx-16, my+110, mx+16, my+110)

    # Flowers throughout
    flower_positions = [(100,130),(160,100),(220,120),(W-100,130),(W-160,100),(W-220,120),(100,H-180),(W-100,H-180)]
    for fx, fy in flower_positions:
        draw_flower(c, fx, fy, 22)

    # Tall grass
    c.setStrokeColor(HexColor("#66BB6A")); c.setLineWidth(2)
    for gx in range(50, int(W)-50, 25):
        if abs(gx - W/2) > 100:
            h = 20 + (gx % 5) * 8
            c.line(gx, 180, gx + (5 if gx%2==0 else -5), 180+h)

    # Two small fairies
    for fax, fay, flip in [(150, 330, 1), (W-150, 310, -1)]:
        draw_mini_fairy(c, fax, fay, flip)

    # Butterflies
    for bx, by in [(80, H-250), (W-80, H-250)]:
        draw_mini_butterfly(c, bx, by)

    # Sparkles
    draw_sparkles(c, [(W/2-160, H-180, 10), (W/2+160, H-180, 10), (W/2, H-160, 12)])
    c.showPage()

def draw_flower(c, cx, cy, r):
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1.5)
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        px = cx + r * math.cos(rad); py = cy + r * math.sin(rad)
        c.ellipse(px-r*0.5, py-r*0.5, px+r*0.5, py+r*0.5, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD54F"))
    c.ellipse(cx-r*0.4, cy-r*0.4, cx+r*0.4, cy+r*0.4, fill=1, stroke=1)

def draw_mini_fairy(c, cx, cy, flip=1):
    # Wings
    c.setFillColor(HexColor("#E1BEE7")); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx+flip*10,cy+30,cx+flip*55,cy+40,cx+flip*55,cy+10)
    p.curveTo(cx+flip*55,cy-10,cx+flip*25,cy-15,cx,cy)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx+flip*10,cy-15,cx+flip*45,cy-40,cx+flip*40,cy-65)
    p.curveTo(cx+flip*35,cy-85,cx+flip*10,cy-70,cx,cy)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Body
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(1)
    c.ellipse(cx-8, cy-30, cx+8, cy+10, fill=1, stroke=1)
    # Dress
    c.setFillColor(HexColor("#CE93D8"))
    p = c.beginPath(); p.moveTo(cx-8, cy-10); p.lineTo(cx-20, cy-50); p.lineTo(cx+20, cy-50); p.lineTo(cx+8, cy-10); p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Head
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black)
    c.circle(cx, cy+25, 18, fill=1, stroke=1)
    # Hair
    c.setFillColor(HexColor("#FFD54F"))
    c.ellipse(cx-18, cy+18, cx+18, cy+48, fill=1, stroke=1)
    # Face
    c.setFillColor(black)
    c.circle(cx-5, cy+28, 2, fill=1, stroke=0)
    c.circle(cx+5, cy+28, 2, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#F06292")); c.setLineWidth(1)
    c.arc(cx-6, cy+16, cx+6, cy+25, startAng=0, extent=180)

def draw_mini_butterfly(c, cx, cy):
    c.setFillColor(HexColor("#E1BEE7")); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
    for flip in [-1, 1]:
        p = c.beginPath()
        p.moveTo(cx, cy)
        p.curveTo(cx+flip*8,cy+20,cx+flip*40,cy+30,cx+flip*38,cy+8)
        p.curveTo(cx+flip*36,cy-5,cx+flip*15,cy-8,cx,cy)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        p = c.beginPath()
        p.moveTo(cx, cy)
        p.curveTo(cx+flip*8,cy-10,cx+flip*32,cy-25,cx+flip*28,cy-45)
        p.curveTo(cx+flip*24,cy-58,cx+flip*8,cy-48,cx,cy)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(HexColor("#37474F")); c.setStrokeColor(black); c.setLineWidth(1)
    c.ellipse(cx-4, cy-42, cx+4, cy+12, fill=1, stroke=1)

def draw_sleeping_unicorn_page(c):
    page_header(c, "Sleepy Unicorn 💤", 6)
    cx, cy = W/2, H/2 - 30

    # Moon
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(HexColor("#FFD54F")); c.setLineWidth(2)
    c.circle(W-110, H-180, 40, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(HexColor("#FFF9C4"))
    c.circle(W-90, H-180, 32, fill=1, stroke=0)

    # Stars
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(0.8)
    for sx, sy, sr in [(80,H-180,12),(160,H-210,8),(250,H-195,10),(W-200,H-215,9),(W/2,H-200,11)]:
        draw_star(c, sx, sy, sr, sr*0.4, 4)

    # Cloud pillow
    c.setFillColor(white); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(2)
    for cbx, cby, cbr in [(0,0,40),(35,10,32),(-35,10,32),(0,20,30),(35,22,25),(-35,22,25)]:
        c.circle(cx+cbx-60, cy-100+cby, cbr, fill=1, stroke=1)

    # Unicorn lying down
    # Body
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-140, cy-60, cx+140, cy+70, fill=1, stroke=1)

    # Legs folded
    c.ellipse(cx-130, cy-90, cx-50, cy-50, fill=1, stroke=1)
    c.ellipse(cx+50, cy-90, cx+130, cy-50, fill=1, stroke=1)
    c.ellipse(cx-100, cy+55, cx-20, cy+100, fill=1, stroke=1)
    c.ellipse(cx+20, cy+55, cx+100, cy+100, fill=1, stroke=1)

    # Head resting
    c.ellipse(cx+60, cy+30, cx+195, cy+150, fill=1, stroke=1)

    # Horn
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx+205, cy+95)
    p.lineTo(cx+175, cy+65)
    p.lineTo(cx+175, cy+100)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Ear
    c.setFillColor(white); c.setStrokeColor(black)
    p = c.beginPath()
    p.moveTo(cx+75, cy+145)
    p.lineTo(cx+55, cy+175)
    p.lineTo(cx+95, cy+158)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Closed eye (sleeping)
    c.setStrokeColor(black); c.setLineWidth(2.5)
    c.arc(cx+120, cy+80, cx+170, cy+110, startAng=0, extent=180)
    # Eyelashes
    for ex, ey, ex2, ey2 in [(cx+125,cy+110,cx+122,cy+118),(cx+140,cy+113,cx+138,cy+121),(cx+155,cy+110,cx+157,cy+118),(cx+165,cy+105,cx+168,cy+112)]:
        c.line(ex, ey, ex2, ey2)

    # Nostril (peaceful)
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(black); c.setLineWidth(1)
    c.ellipse(cx+162, cy+65, cx+180, cy+74, fill=1, stroke=1)

    # Mane
    mane_colors = ["#F48FB1","#CE93D8","#81D4FA","#FFD54F","#A5D6A7"]
    for i, mc in enumerate(mane_colors):
        c.setFillColor(HexColor(mc)); c.setStrokeColor(black); c.setLineWidth(1)
        off = i*7
        p = c.beginPath()
        p.moveTo(cx+68+off, cy+148)
        p.curveTo(cx+35+off, cy+120, cx+10+off, cy+80, cx+20+off, cy+30)
        p.curveTo(cx+28+off, cy+5, cx+50+off, cy-10, cx+55+off, cy-40)
        p.lineTo(cx+65+off, cy-40)
        p.curveTo(cx+62+off, cy-10, cx+42+off, cy+10, cx+35+off, cy+35)
        p.curveTo(cx+25+off, cy+85, cx+52+off, cy+125, cx+82+off, cy+148)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Tail (curled)
    for i, tc in enumerate(mane_colors):
        c.setFillColor(HexColor(tc)); c.setStrokeColor(black); c.setLineWidth(1)
        p = c.beginPath()
        p.moveTo(cx-130, cy+10+i*5)
        p.curveTo(cx-170, cy+30+i*5, cx-180, cy+80+i*5, cx-150, cy+100+i*5)
        p.curveTo(cx-130, cy+115+i*5, cx-105, cy+110+i*5, cx-105+8, cy+95+i*5)
        p.curveTo(cx-118, cy+85+i*5, cx-140, cy+68+i*5, cx-120, cy+45+i*5)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # ZZZ
    c.setFillColor(HexColor("#9C27B0")); c.setFont("Helvetica-Bold", 28)
    c.drawString(cx+195, cy+155, "z")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(cx+220, cy+178, "z")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(cx+240, cy+198, "z")

    # Ground / grass
    c.setStrokeColor(HexColor("#A5D6A7")); c.setLineWidth(2)
    for gx in range(45, int(W)-45, 20):
        c.line(gx, cy-65, gx+(5 if gx%2==0 else -5), cy-80)

    draw_sparkles(c, [(70,180,10),(W-70,180,10)])
    c.showPage()

def draw_unicorn_family_page(c):
    page_header(c, "Unicorn Family 💕", 7)

    # Three unicorn silhouettes (outlines to color)
    positions = [(W/2-170, H/2-20, 0.65), (W/2, H/2, 1.0), (W/2+160, H/2-20, 0.7)]
    for ux, uy, scale in positions:
        draw_simple_unicorn(c, ux, uy, scale)

    # Sun
    c.setFillColor(HexColor("#FFF176")); c.setStrokeColor(HexColor("#FFD54F")); c.setLineWidth(2)
    c.circle(80, H-170, 38, fill=1, stroke=1)
    c.setStrokeColor(HexColor("#FFD54F")); c.setLineWidth(2.5)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        c.line(80+42*math.cos(rad), H-170+42*math.sin(rad), 80+60*math.cos(rad), H-170+60*math.sin(rad))

    # Clouds
    for cloud_cx, cloud_cy in [(W-120, H-185), (W/2, H-195)]:
        c.setFillColor(white); c.setStrokeColor(HexColor("#B0BEC5")); c.setLineWidth(1.5)
        for cbx, cby, cbr in [(0,0,22),(20,8,18),(-20,8,18),(0,16,16)]:
            c.circle(cloud_cx+cbx, cloud_cy+cby, cbr, fill=1, stroke=1)

    # Flowers along ground
    c.setFillColor(HexColor("#C8E6C9")); c.setStrokeColor(HexColor("#A5D6A7")); c.setLineWidth(2)
    c.rect(40, 55, W-80, 80, fill=1, stroke=1)
    for fx in range(60, int(W)-60, 40):
        draw_flower(c, fx, 100, 14)

    c.showPage()

def draw_simple_unicorn(c, cx, cy, scale=1.0):
    def s(v): return v * scale
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(max(1.5, 2.5*scale))
    # Body
    c.ellipse(cx-s(90), cy-s(50), cx+s(90), cy+s(55), fill=1, stroke=1)
    # Legs
    for lx in [-60, -20, 20, 60]:
        c.rect(cx+s(lx)-s(12), cy-s(130), s(24), s(85), fill=1, stroke=1)
    # Neck
    p = c.beginPath()
    p.moveTo(cx+s(30), cy+s(48))
    p.lineTo(cx+s(18), cy+s(110))
    p.lineTo(cx+s(68), cy+s(110))
    p.lineTo(cx+s(78), cy+s(48))
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Head
    c.ellipse(cx+s(12), cy+s(90), cx+s(95), cy+s(180), fill=1, stroke=1)
    # Horn
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(max(1.2, 2*scale))
    p = c.beginPath()
    p.moveTo(cx+s(53), cy+s(225))
    p.lineTo(cx+s(43), cy+s(180))
    p.lineTo(cx+s(63), cy+s(180))
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Ear
    c.setFillColor(white); c.setStrokeColor(black)
    p = c.beginPath()
    p.moveTo(cx+s(20), cy+s(173))
    p.lineTo(cx+s(10), cy+s(200))
    p.lineTo(cx+s(36), cy+s(183))
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Eye
    c.ellipse(cx+s(63), cy+s(143), cx+s(88), cy+s(163), fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx+s(67), cy+s(146), cx+s(84), cy+s(160), fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx+s(72), cy+s(155), s(4), fill=1, stroke=0)
    # Mane
    mane_colors = ["#F48FB1","#CE93D8","#FFD54F"]
    for i, mc in enumerate(mane_colors):
        c.setFillColor(HexColor(mc)); c.setStrokeColor(black); c.setLineWidth(max(0.8, 1.2*scale))
        off = i*s(7)
        p = c.beginPath()
        p.moveTo(cx+s(18)+off, cy+s(178))
        p.curveTo(cx+s(5)+off, cy+s(145), cx-s(5)+off, cy+s(95), cx+s(15)+off, cy+s(50))
        p.curveTo(cx+s(25)+off, cy+s(25), cx+s(38)+off, cy+s(10), cx+s(40)+off, cy-s(8))
        p.lineTo(cx+s(50)+off, cy-s(8))
        p.curveTo(cx+s(50)+off, cy+s(15), cx+s(36)+off, cy+s(32), cx+s(27)+off, cy+s(58))
        p.curveTo(cx+s(15)+off, cy+s(100), cx+s(20)+off, cy+s(150), cx+s(40)+off, cy+s(178))
        p.close()
        c.drawPath(p, fill=1, stroke=1)
    # Tail
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(max(0.8, 1.2*scale))
    p = c.beginPath()
    p.moveTo(cx-s(88), cy+s(5))
    p.curveTo(cx-s(120), cy+s(25), cx-s(125), cy-s(20), cx-s(108), cy-s(50))
    p.curveTo(cx-s(100), cy-s(62), cx-s(90), cy-s(65), cx-s(86), cy-s(60))
    p.curveTo(cx-s(98), cy-s(35), cx-s(96), cy-s(10), cx-s(72), cy-s(15))
    p.close()
    c.drawPath(p, fill=1, stroke=1)

def draw_magic_wand_page(c):
    page_header(c, "Magic Wands & Potions 🪄", 8)

    items = [
        # Wand 1 - star tip
        ("wand1", W/2-155, H/2+60),
        # Wand 2 - heart tip
        ("wand2", W/2+25, H/2+60),
        # Potion 1
        ("potion1", W/2-155, H/2-120),
        # Potion 2
        ("potion2", W/2+25, H/2-120),
        # Crown
        ("crown", W/2-65, H/2+100),
    ]

    # Wand 1
    c.setFillColor(HexColor("#8D6E63")); c.setStrokeColor(black); c.setLineWidth(3)
    c.roundRect(W/2-170, H/2-60, 25, 180, 8, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    draw_star(c, W/2-158, H/2+130, 28, 11)
    draw_sparkles(c, [(W/2-130,H/2+155,8),(W/2-100,H/2+135,6),(W/2-175,H/2+158,7)])

    # Wand 2 (striped candy)
    colors2 = ["#F48FB1","#CE93D8"]
    for i in range(9):
        c.setFillColor(HexColor(colors2[i%2])); c.setStrokeColor(black); c.setLineWidth(1)
        c.rect(W/2+10, H/2-60+i*20, 25, 20, fill=1, stroke=1)
    # Heart tip
    c.setFillColor(HexColor("#E91E63")); c.setStrokeColor(black); c.setLineWidth(2)
    hx, hy = W/2+22, H/2+130
    p = c.beginPath()
    p.moveTo(hx, hy-10)
    p.curveTo(hx-20, hy+10, hx-20, hy+32, hx, hy+24)
    p.curveTo(hx+20, hy+32, hx+20, hy+10, hx, hy-10)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Potion 1 (round bottle)
    px1, py1 = W/2-160, H/2-120
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    c.rect(px1-8, py1+55, 16, 18, fill=1, stroke=1)
    c.rect(px1-12, py1+70, 24, 6, fill=1, stroke=1)
    c.circle(px1, py1+40, 40, fill=1, stroke=1)
    c.setFillColor(HexColor("#E1BEE7")); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
    c.circle(px1, py1+40, 34, fill=1, stroke=0)
    c.setFillColor(white)
    c.ellipse(px1-20, py1+20, px1-5, py1+35, fill=1, stroke=0)
    # Stars on potion
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(HexColor("#FFA000")); c.setLineWidth(0.8)
    for sdx, sdy in [(0,40),(-15,55),(12,60)]:
        draw_star(c, px1+sdx, py1+sdy, 8, 3, 4)
    # Bubbles
    c.setFillColor(white); c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
    for bdx, bdy, br in [(-8,30,5),(10,20,4),(2,50,6)]:
        c.circle(px1+bdx, py1+bdy, br, fill=1, stroke=1)

    # Potion 2 (tall bottle)
    px2, py2 = W/2+30, H/2-150
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(2)
    c.rect(px2-8, py2+110, 16, 20, fill=1, stroke=1)
    c.rect(px2-14, py2+125, 28, 8, fill=1, stroke=1)
    c.roundRect(px2-28, py2, 56, 115, 20, fill=1, stroke=1)
    c.setFillColor(HexColor("#B2DFDB")); c.setStrokeColor(HexColor("#80CBC4")); c.setLineWidth(1)
    c.roundRect(px2-23, py2+5, 46, 90, 18, fill=1, stroke=0)
    c.setFillColor(white)
    c.ellipse(px2-18, py2+10, px2-5, py2+25, fill=1, stroke=0)
    # Potion fill
    c.setFillColor(HexColor("#80CBC4"))
    c.roundRect(px2-23, py2+5, 46, 48, 18, fill=1, stroke=0)
    # Lightning bolt
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(px2+5, py2+100)
    p.lineTo(px2-8, py2+72)
    p.lineTo(px2+2, py2+72)
    p.lineTo(px2-5, py2+44)
    p.lineTo(px2+12, py2+72)
    p.lineTo(px2+2, py2+72)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Crown
    crx, cry = W/2, H/2-30
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2.5)
    p = c.beginPath()
    p.moveTo(crx-70, cry)
    p.lineTo(crx-70, cry+50)
    p.lineTo(crx-38, cry+25)
    p.lineTo(crx, cry+55)
    p.lineTo(crx+38, cry+25)
    p.lineTo(crx+70, cry+50)
    p.lineTo(crx+70, cry)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Gem on crown
    c.setFillColor(HexColor("#E91E63")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.circle(crx, cry+50, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#81D4FA"))
    c.circle(crx-38, cry+22, 7, fill=1, stroke=1)
    c.circle(crx+38, cry+22, 7, fill=1, stroke=1)
    # Crown dots
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(1)
    for dx in range(-60, 70, 20):
        c.circle(crx+dx, cry+5, 5, fill=1, stroke=1)

    draw_sparkles(c, [(80,H-185,10),(W-80,H-185,10),(80,200,9),(W-80,200,9),(W/2,H-180,12)])
    c.showPage()

def draw_princess_fairy_page(c):
    page_header(c, "Princess Fairy 👑", 9)
    cx, cy = W/2, H/2

    # Wings
    for flip in [-1, 1]:
        c.setFillColor(HexColor("#E1BEE7")); c.setStrokeColor(HexColor("#AB47BC")); c.setLineWidth(2)
        p = c.beginPath()
        p.moveTo(cx, cy+20)
        p.curveTo(cx+flip*25, cy+90, cx+flip*160, cy+120, cx+flip*165, cy+40)
        p.curveTo(cx+flip*168, cy-15, cx+flip*80, cy-35, cx, cy+20)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        p = c.beginPath()
        p.moveTo(cx, cy+20)
        p.curveTo(cx+flip*25, cy-10, cx+flip*130, cy-65, cx+flip*120, cy-130)
        p.curveTo(cx+flip*112, cy-175, cx+flip*40, cy-150, cx, cy+20)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        # Vein lines
        c.setStrokeColor(HexColor("#CE93D8")); c.setLineWidth(1)
        c.line(cx, cy+20, cx+flip*120, cy+80)
        c.line(cx, cy+20, cx+flip*90, cy-100)

    # Dress (ball gown)
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx-20, cy-25)
    p.curveTo(cx-80, cy-100, cx-150, cy-200, cx-130, cy-300)
    p.curveTo(cx-115, cy-360, cx-60, cy-380, cx, cy-385)
    p.curveTo(cx+60, cy-380, cx+115, cy-360, cx+130, cy-300)
    p.curveTo(cx+150, cy-200, cx+80, cy-100, cx+20, cy-25)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Dress layers
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1.5)
    p = c.beginPath()
    p.moveTo(cx-20, cy-25)
    p.curveTo(cx-60, cy-80, cx-120, cy-160, cx-105, cy-240)
    p.curveTo(cx-92, cy-295, cx-40, cy-310, cx, cy-315)
    p.curveTo(cx+40, cy-310, cx+92, cy-295, cx+105, cy-240)
    p.curveTo(cx+120, cy-160, cx+60, cy-80, cx+20, cy-25)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Bodice
    c.setFillColor(HexColor("#CE93D8")); c.setStrokeColor(black); c.setLineWidth(2)
    c.roundRect(cx-22, cy, 44, 80, 8, fill=1, stroke=1)
    # Belt
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.rect(cx-25, cy, 50, 12, fill=1, stroke=1)
    draw_star(c, cx, cy+6, 10, 4)

    # Head
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    c.circle(cx, cy+130, 50, fill=1, stroke=1)

    # Crown
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx-45, cy+160)
    p.lineTo(cx-45, cy+185)
    p.lineTo(cx-20, cy+173)
    p.lineTo(cx, cy+188)
    p.lineTo(cx+20, cy+173)
    p.lineTo(cx+45, cy+185)
    p.lineTo(cx+45, cy+160)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(HexColor("#E91E63"))
    c.circle(cx, cy+184, 7, fill=1, stroke=1)
    c.setFillColor(HexColor("#81D4FA"))
    c.circle(cx-22, cy+171, 5, fill=1, stroke=1)
    c.circle(cx+22, cy+171, 5, fill=1, stroke=1)

    # Long hair
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(black); c.setLineWidth(1.5)
    for side, flip in [(-1, -1), (1, 1)]:
        p = c.beginPath()
        p.moveTo(cx+side*40, cy+160)
        p.curveTo(cx+side*70, cy+130, cx+side*85, cy+70, cx+side*75, cy)
        p.curveTo(cx+side*70, cy-30, cx+side*60, cy-60, cx+side*55, cy-90)
        p.lineTo(cx+side*65, cy-90)
        p.curveTo(cx+side*70, cy-60, cx+side*80, cy-30, cx+side*85, cy)
        p.curveTo(cx+side*96, cy+70, cx+side*82, cy+128, cx+side*52, cy+160)
        p.close()
        c.drawPath(p, fill=1, stroke=1)

    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.ellipse(cx-30, cy+118, cx-8, cy+138, fill=1, stroke=1)
    c.ellipse(cx+8, cy+118, cx+30, cy+138, fill=1, stroke=1)
    c.setFillColor(HexColor("#7986CB"))
    c.ellipse(cx-27, cy+121, cx-11, cy+135, fill=1, stroke=0)
    c.ellipse(cx+11, cy+121, cx+27, cy+135, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-24, cy+124, cx-14, cy+132, fill=1, stroke=0)
    c.ellipse(cx+14, cy+124, cx+24, cy+132, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-20, cy+130, 3, fill=1, stroke=0)
    c.circle(cx+16, cy+130, 3, fill=1, stroke=0)
    # Eyelashes
    c.setStrokeColor(black); c.setLineWidth(1)
    for ex, ey, ex2, ey2 in [(cx-27,cy+138,cx-29,cy+143),(cx-19,cy+139,cx-19,cy+145),(cx-11,cy+138,cx-9,cy+143)]:
        c.line(ex, ey, ex2, ey2)
    for ex, ey, ex2, ey2 in [(cx+9,cy+138,cx+7,cy+143),(cx+19,cy+139,cx+19,cy+145),(cx+27,cy+138,cx+29,cy+143)]:
        c.line(ex, ey, ex2, ey2)

    # Smile
    c.setFillColor(HexColor("#F06292")); c.setStrokeColor(HexColor("#F06292")); c.setLineWidth(2)
    c.arc(cx-14, cy+103, cx+14, cy+120, startAng=0, extent=180)

    # Cheeks
    c.setFillColor(HexColor("#FFCDD2")); c.setStrokeColor(HexColor("#EF9A9A")); c.setLineWidth(0.5)
    c.ellipse(cx-48, cy+112, cx-28, cy+124, fill=1, stroke=1)
    c.ellipse(cx+28, cy+112, cx+48, cy+124, fill=1, stroke=1)

    # Arms
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx-22, cy+60)
    p.curveTo(cx-70, cy+70, cx-90, cy+30, cx-80, cy+5)
    p.lineTo(cx-70, cy+10)
    p.curveTo(cx-78, cy+28, cx-62, cy+60, cx-14, cy+50)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx+22, cy+60)
    p.curveTo(cx+70, cy+70, cx+90, cy+30, cx+80, cy+5)
    p.lineTo(cx+70, cy+10)
    p.curveTo(cx+78, cy+28, cx+62, cy+60, cx+14, cy+50)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Wand
    c.setFillColor(HexColor("#9C27B0")); c.setStrokeColor(black); c.setLineWidth(2)
    c.line(cx+78, cy+8, cx+130, cy-60)
    c.setFillColor(HexColor("#FFD700")); c.setStrokeColor(black); c.setLineWidth(1.5)
    draw_star(c, cx+135, cy-65, 20, 8)

    # Sparkles
    draw_sparkles(c, [(cx+160, cy-80, 10),(cx+148, cy-45, 7),(cx-155, cy+80, 10),(70, H-180, 10),(W-70, H-180, 10)])
    c.showPage()

def draw_bonus_color_page(c):
    page_bg(c, "#F3E5F5")
    page_border(c, "#AB47BC", "#CE93D8")
    c.setFillColor(HexColor("#9C27B0")); c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H-78, "Color the Magic!")
    c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 17)
    c.drawCentredString(W/2, H-115, "Here are some ideas:")
    items = [
        ("✨ Unicorns", "White, Pink, Purple, Gold"),
        ("🧚 Fairies", "Any skin tone, Gold hair"),
        ("🏰 Castle", "Purple, Pink, Blue"),
        ("🌈 Rainbow", "Red, Orange, Yellow, Green, Blue, Purple"),
        ("🌸 Flowers", "Pink, Yellow, Purple"),
        ("⭐ Stars", "Gold, Yellow, Silver"),
        ("🪄 Wands", "Gold, Purple, Pink"),
        ("🌙 Moon", "White, Silver, Yellow"),
        ("💎 Gems", "Any sparkly color!"),
        ("🦋 Wings", "Pale purple, Light blue"),
    ]
    y = H - 160
    for emoji_label, hint in items:
        c.setFillColor(HexColor("#6A1B9A")); c.setFont("Helvetica-Bold", 16)
        c.drawString(70, y, emoji_label)
        c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 15)
        c.drawString(280, y, hint)
        y -= 34
    c.setFillColor(HexColor("#AB47BC")); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, 90, "✨ Be creative! Use any colors! ✨")
    c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 14)
    c.drawCentredString(W/2, 62, "Unicorns and fairies love ALL colors!")
    c.showPage()

def make_book():
    c = new_canvas("unicorns_fairies_coloring_book.pdf")
    draw_cover(c)
    draw_bonus_color_page(c)
    draw_unicorn_page(c)
    draw_fairy_page(c)
    draw_rainbow_unicorn_page(c)
    draw_magic_castle_page(c)
    draw_fairy_garden_page(c)
    draw_sleeping_unicorn_page(c)
    draw_unicorn_family_page(c)
    draw_magic_wand_page(c)
    draw_princess_fairy_page(c)
    c.save()
    print("Done: unicorns_fairies_coloring_book.pdf")

make_book()