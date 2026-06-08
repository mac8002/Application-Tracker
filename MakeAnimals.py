from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white
import math

PAGE_SIZE = (8.5 * inch, 8.5 * inch)
W, H = PAGE_SIZE

def new_canvas(filename):
    c = canvas.Canvas(filename, pagesize=PAGE_SIZE)
    c.setTitle("Cute Animals Coloring Book")
    c.setAuthor("My Coloring Books")
    return c

def draw_cover(c):
    # Background
    c.setFillColor(HexColor("#FFF9C4"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Decorative border
    c.setStrokeColor(HexColor("#F48FB1"))
    c.setLineWidth(8)
    c.rect(18, 18, W-36, H-36, fill=0, stroke=1)
    c.setStrokeColor(HexColor("#81D4FA"))
    c.setLineWidth(4)
    c.rect(28, 28, W-56, H-56, fill=0, stroke=1)

    # Title box
    c.setFillColor(HexColor("#F48FB1"))
    c.roundRect(60, H-220, W-120, 140, 20, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 48)
    c.drawCentredString(W/2, H-130, "Cute Animals")
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W/2, H-175, "Coloring Book")

    # Big cute cat face (center)
    cx, cy = W/2, H/2 - 30

    # Cat body
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(3)
    c.ellipse(cx-90, cy-110, cx+90, cy+60, fill=1, stroke=1)

    # Cat head
    c.ellipse(cx-80, cy+30, cx+80, cy+170, fill=1, stroke=1)

    # Ears
    c.setFillColor(white)
    # Left ear
    p = c.beginPath()
    p.moveTo(cx-70, cy+150)
    p.lineTo(cx-110, cy+210)
    p.lineTo(cx-30, cy+175)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Right ear
    p = c.beginPath()
    p.moveTo(cx+70, cy+150)
    p.lineTo(cx+110, cy+210)
    p.lineTo(cx+30, cy+175)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Inner ears
    c.setFillColor(HexColor("#F8BBD0"))
    p = c.beginPath()
    p.moveTo(cx-68, cy+152)
    p.lineTo(cx-100, cy+200)
    p.lineTo(cx-38, cy+172)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx+68, cy+152)
    p.lineTo(cx+100, cy+200)
    p.lineTo(cx+38, cy+172)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

    # Eyes
    c.setFillColor(HexColor("#A5D6A7"))
    c.ellipse(cx-35, cy+95, cx-5, cy+130, fill=1, stroke=1)
    c.ellipse(cx+5, cy+95, cx+35, cy+130, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx-28, cy+100, cx-12, cy+125, fill=1, stroke=0)
    c.ellipse(cx+12, cy+100, cx+28, cy+125, fill=1, stroke=0)
    c.setFillColor(white)
    c.ellipse(cx-25, cy+115, cx-18, cy+122, fill=1, stroke=0)
    c.ellipse(cx+15, cy+115, cx+22, cy+122, fill=1, stroke=0)

    # Nose
    c.setFillColor(HexColor("#F48FB1"))
    p = c.beginPath()
    p.moveTo(cx, cy+93)
    p.lineTo(cx-10, cy+80)
    p.lineTo(cx+10, cy+80)
    p.close()
    c.drawPath(p, fill=1, stroke=1)

    # Mouth
    c.setStrokeColor(black)
    c.setLineWidth(2)
    c.arc(cx-18, cy+62, cx, cy+84, startAng=0, extent=180)
    c.arc(cx, cy+62, cx+18, cy+84, startAng=0, extent=180)

    # Whiskers
    c.setLineWidth(1.5)
    for i in range(3):
        y_off = cy + 75 + i*8
        c.line(cx-80, y_off, cx-20, cy+83-i*3)
        c.line(cx+80, y_off, cx+20, cy+83-i*3)

    # Paws
    c.setFillColor(white)
    c.setStrokeColor(black)
    c.setLineWidth(3)
    c.ellipse(cx-75, cy-130, cx-25, cy-80, fill=1, stroke=1)
    c.ellipse(cx+25, cy-130, cx+75, cy-80, fill=1, stroke=1)
    # Toe lines
    c.setLineWidth(1.5)
    for dx in [-60, -45]:
        c.line(cx+dx, cy-130, cx+dx, cy-110)
    for dx in [35, 50]:
        c.line(cx+dx, cy-130, cx+dx, cy-110)

    # Stars around
    c.setFillColor(HexColor("#FFD54F"))
    c.setStrokeColor(HexColor("#FF8F00"))
    c.setLineWidth(1)
    star_positions = [(80,H-270),(W-80,H-270),(60,cy),(W-60,cy),(90,200),(W-90,200)]
    for sx, sy in star_positions:
        draw_star(c, sx, sy, 18, 8)

    # Subtitle
    c.setFillColor(HexColor("#6A1B9A"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, 100, "For Toddlers & Young Kids")
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#37474F"))
    c.drawCentredString(W/2, 72, "Ages 2–7  •  20 Fun Pages")
    c.showPage()

def draw_star(c, cx, cy, r_out, r_in, points=5):
    path = c.beginPath()
    for i in range(points * 2):
        angle = math.radians(i * 180 / points - 90)
        r = r_out if i % 2 == 0 else r_in
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.close()
    c.drawPath(path, fill=1, stroke=1)

def page_header(c, title, page_num):
    c.setFillColor(HexColor("#FFF9C4"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#F48FB1"))
    c.setLineWidth(5)
    c.rect(15, 15, W-30, H-30, fill=0, stroke=1)
    c.setFillColor(HexColor("#F48FB1"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W/2, H-55, title)
    c.setFillColor(HexColor("#90A4AE"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(W/2, 35, f"Page {page_num}")

def draw_bunny_page(c):
    page_header(c, "Happy Bunny 🐰", 1)
    cx, cy = W/2, H/2 - 20
    lw = 3
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(lw)
    # Body
    c.ellipse(cx-100, cy-130, cx+100, cy+60, fill=1, stroke=1)
    # Head
    c.ellipse(cx-75, cy+40, cx+75, cy+170, fill=1, stroke=1)
    # Ears (long)
    c.ellipse(cx-55, cy+130, cx-20, cy+280, fill=1, stroke=1)
    c.ellipse(cx+20, cy+130, cx+55, cy+280, fill=1, stroke=1)
    c.setFillColor(HexColor("#F8BBD0")); c.setStrokeColor(HexColor("#F8BBD0"))
    c.ellipse(cx-50, cy+135, cx-25, cy+270, fill=1, stroke=0)
    c.ellipse(cx+25, cy+135, cx+50, cy+270, fill=1, stroke=0)
    c.setFillColor(white); c.setStrokeColor(black)
    # Eyes
    c.ellipse(cx-35, cy+105, cx-10, cy+130, fill=1, stroke=1)
    c.ellipse(cx+10, cy+105, cx+35, cy+130, fill=1, stroke=1)
    c.setFillColor(HexColor("#4FC3F7"))
    c.ellipse(cx-30, cy+108, cx-15, cy+127, fill=1, stroke=0)
    c.ellipse(cx+15, cy+108, cx+30, cy+127, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-26, cy+112, cx-18, cy+123, fill=1, stroke=0)
    c.ellipse(cx+18, cy+112, cx+26, cy+123, fill=1, stroke=0)
    # Nose
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black)
    c.ellipse(cx-8, cy+82, cx+8, cy+96, fill=1, stroke=1)
    # Mouth
    c.setLineWidth(2)
    c.arc(cx-20, cy+58, cx, cy+80, startAng=0, extent=180)
    c.arc(cx, cy+58, cx+20, cy+80, startAng=0, extent=180)
    # Paws
    c.setFillColor(white); c.setLineWidth(3)
    c.ellipse(cx-120, cy-60, cx-70, cy-20, fill=1, stroke=1)
    c.ellipse(cx+70, cy-60, cx+120, cy-20, fill=1, stroke=1)
    # Feet
    c.ellipse(cx-90, cy-155, cx-30, cy-110, fill=1, stroke=1)
    c.ellipse(cx+30, cy-155, cx+90, cy-110, fill=1, stroke=1)
    # Tail
    c.ellipse(cx+80, cy-30, cx+120, cy+10, fill=1, stroke=1)
    # Tummy circle
    c.setFillColor(HexColor("#FFF9C4"))
    c.ellipse(cx-40, cy-70, cx+40, cy+30, fill=1, stroke=1)
    # Flowers
    for fx, fy in [(100, 130), (W-100, 130), (100, H-200), (W-100, H-200)]:
        draw_flower(c, fx, fy, 25)
    c.showPage()

def draw_flower(c, cx, cy, r):
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1.5)
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        c.ellipse(px-r*0.5, py-r*0.5, px+r*0.5, py+r*0.5, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD54F"))
    c.ellipse(cx-r*0.4, cy-r*0.4, cx+r*0.4, cy+r*0.4, fill=1, stroke=1)

def draw_elephant_page(c):
    page_header(c, "Ellie the Elephant 🐘", 2)
    cx, cy = W/2, H/2 - 40
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-120, cy-100, cx+120, cy+100, fill=1, stroke=1)
    # Head
    c.ellipse(cx-90, cy+70, cx+90, cy+220, fill=1, stroke=1)
    # Ears (big)
    c.ellipse(cx-180, cy+60, cx-60, cy+200, fill=1, stroke=1)
    c.ellipse(cx+60, cy+60, cx+180, cy+200, fill=1, stroke=1)
    c.setFillColor(HexColor("#F8BBD0"))
    c.ellipse(cx-165, cy+75, cx-75, cy+185, fill=1, stroke=0)
    c.ellipse(cx+75, cy+75, cx+165, cy+185, fill=1, stroke=0)
    c.setFillColor(white); c.setStrokeColor(black)
    # Trunk
    p = c.beginPath()
    p.moveTo(cx-30, cy+80)
    p.curveTo(cx-60, cy+30, cx-80, cy-20, cx-50, cy-60)
    p.curveTo(cx-30, cy-80, cx+10, cy-70, cx+20, cy-50)
    p.curveTo(cx+40, cy-30, cx+30, cy+20, cx+20, cy+70)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Eyes
    c.ellipse(cx-45, cy+155, cx-15, cy+185, fill=1, stroke=1)
    c.ellipse(cx+15, cy+155, cx+45, cy+185, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx-38, cy+161, cx-22, cy+179, fill=1, stroke=0)
    c.ellipse(cx+22, cy+161, cx+38, cy+179, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-30, cy+174, 4, fill=1, stroke=0)
    c.circle(cx+26, cy+174, 4, fill=1, stroke=0)
    # Legs
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    for lx in [cx-80, cx-30, cx+30, cx+80]:
        c.rect(lx-18, cy-185, 36, 90, fill=1, stroke=1)
        c.ellipse(lx-22, cy-200, lx+22, cy-170, fill=1, stroke=1)
    # Tail
    c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx+115, cy+10)
    p.curveTo(cx+145, cy+30, cx+155, cy+0, cx+140, cy-20)
    c.drawPath(p, fill=0, stroke=1)
    # Stars
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(HexColor("#FF8F00")); c.setLineWidth(1)
    for sx, sy in [(70, 200), (W-70, 200), (70, H-200), (W-70, H-200)]:
        draw_star(c, sx, sy, 16, 7)
    c.showPage()

def draw_duck_page(c):
    page_header(c, "Daffy the Duck 🦆", 3)
    cx, cy = W/2, H/2 - 20
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-110, cy-80, cx+110, cy+100, fill=1, stroke=1)
    # Wing
    c.ellipse(cx-90, cy-30, cx+20, cy+60, fill=1, stroke=1)
    # Head
    c.ellipse(cx-60, cy+80, cx+60, cy+200, fill=1, stroke=1)
    # Bill
    c.setFillColor(HexColor("#FFF176"))
    p = c.beginPath()
    p.moveTo(cx-20, cy+115)
    p.lineTo(cx-70, cy+100)
    p.lineTo(cx-65, cy+130)
    p.lineTo(cx-20, cy+140)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Eye
    c.setFillColor(white); c.setStrokeColor(black)
    c.ellipse(cx+5, cy+145, cx+35, cy+175, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx+12, cy+152, cx+28, cy+168, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx+20, cy+163, 4, fill=1, stroke=0)
    # Feet
    c.setFillColor(HexColor("#FFF176")); c.setStrokeColor(black)
    # left foot
    p = c.beginPath()
    p.moveTo(cx-40, cy-85)
    p.lineTo(cx-80, cy-120)
    p.lineTo(cx-50, cy-118)
    p.lineTo(cx-40, cy-140)
    p.lineTo(cx-20, cy-118)
    p.lineTo(cx+5, cy-120)
    p.lineTo(cx, cy-85)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # right foot
    p = c.beginPath()
    p.moveTo(cx+30, cy-85)
    p.lineTo(cx-10, cy-120)
    p.lineTo(cx+20, cy-118)
    p.lineTo(cx+30, cy-140)
    p.lineTo(cx+50, cy-118)
    p.lineTo(cx+75, cy-120)
    p.lineTo(cx+70, cy-85)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Water ripples
    c.setStrokeColor(HexColor("#81D4FA")); c.setLineWidth(2); c.setFillColor(HexColor("#E1F5FE"))
    c.ellipse(cx-140, cy-150, cx+140, cy-80, fill=1, stroke=1)
    c.setStrokeColor(HexColor("#29B6F6")); c.setLineWidth(1.5)
    for rx in [0.6, 0.85]:
        c.ellipse(cx-140*rx, cy-148, cx+140*rx, cy-100, fill=0, stroke=1)
    # Bubbles
    c.setFillColor(white); c.setStrokeColor(HexColor("#81D4FA")); c.setLineWidth(1)
    for bx, by, br in [(cx-160,cy-110,8),(cx+150,cy-100,6),(cx-130,cy-90,5)]:
        c.circle(bx, by, br, fill=1, stroke=1)
    c.showPage()

def draw_dog_page(c):
    page_header(c, "Buddy the Dog 🐶", 4)
    cx, cy = W/2, H/2 - 30
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-100, cy-90, cx+100, cy+80, fill=1, stroke=1)
    # Head
    c.ellipse(cx-80, cy+60, cx+80, cy+190, fill=1, stroke=1)
    # Floppy ears
    c.ellipse(cx-120, cy+60, cx-55, cy+175, fill=1, stroke=1)
    c.ellipse(cx+55, cy+60, cx+120, cy+175, fill=1, stroke=1)
    # Snout
    c.setFillColor(HexColor("#FFCCBC"))
    c.ellipse(cx-40, cy+75, cx+40, cy+120, fill=1, stroke=1)
    # Nose
    c.setFillColor(black)
    c.ellipse(cx-18, cy+108, cx+18, cy+130, fill=1, stroke=0)
    c.setFillColor(white)
    c.ellipse(cx-12, cy+118, cx-4, cy+126, fill=1, stroke=0)
    # Mouth
    c.setStrokeColor(black); c.setLineWidth(2); c.setFillColor(white)
    c.arc(cx-25, cy+62, cx, cy+88, startAng=0, extent=180)
    c.arc(cx, cy+62, cx+25, cy+88, startAng=0, extent=180)
    # Tongue
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.ellipse(cx-15, cy+48, cx+15, cy+78, fill=1, stroke=1)
    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-50, cy+140, cx-18, cy+172, fill=1, stroke=1)
    c.ellipse(cx+18, cy+140, cx+50, cy+172, fill=1, stroke=1)
    c.setFillColor(HexColor("#795548"))
    c.ellipse(cx-46, cy+144, cx-22, cy+168, fill=1, stroke=0)
    c.ellipse(cx+22, cy+144, cx+46, cy+168, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-41, cy+149, cx-27, cy+163, fill=1, stroke=0)
    c.ellipse(cx+27, cy+149, cx+41, cy+163, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-34, cy+159, 3, fill=1, stroke=0)
    c.circle(cx+30, cy+159, 3, fill=1, stroke=0)
    # Legs
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    for lx in [cx-70, cx-25, cx+25, cx+70]:
        c.rect(lx-15, cy-185, 30, 100, fill=1, stroke=1)
        c.ellipse(lx-20, cy-200, lx+20, cy-168, fill=1, stroke=1)
    # Tail
    c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(cx+98, cy+20)
    p.curveTo(cx+140, cy+60, cx+155, cy+20, cx+130, cy-10)
    c.drawPath(p, fill=0, stroke=1)
    # Collar
    c.setFillColor(HexColor("#EF5350")); c.setStrokeColor(black); c.setLineWidth(2)
    c.rect(cx-55, cy+55, 110, 18, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFD54F"))
    c.circle(cx, cy+55, 8, fill=1, stroke=1)
    # Paw prints
    c.setFillColor(HexColor("#BCAAA4")); c.setStrokeColor(HexColor("#8D6E63")); c.setLineWidth(1)
    for px, py in [(90, 110), (W-90, 110)]:
        c.circle(px, py, 12, fill=1, stroke=1)
        for dpx, dpy in [(-10,12),(0,14),(10,12),(-14,2),(14,2)]:
            c.circle(px+dpx, py+dpy, 5, fill=1, stroke=1)
    c.showPage()

def draw_penguin_page(c):
    page_header(c, "Pete the Penguin 🐧", 5)
    cx, cy = W/2, H/2 - 20
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body (dark)
    c.setFillColor(HexColor("#37474F"))
    c.ellipse(cx-90, cy-130, cx+90, cy+100, fill=1, stroke=1)
    # White tummy
    c.setFillColor(white)
    c.ellipse(cx-55, cy-110, cx+55, cy+80, fill=1, stroke=1)
    # Head
    c.setFillColor(HexColor("#37474F")); c.setStrokeColor(black)
    c.ellipse(cx-70, cy+70, cx+70, cy+200, fill=1, stroke=1)
    # White face
    c.setFillColor(white)
    c.ellipse(cx-50, cy+80, cx+50, cy+180, fill=1, stroke=0)
    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-40, cy+145, cx-12, cy+175, fill=1, stroke=1)
    c.ellipse(cx+12, cy+145, cx+40, cy+175, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx-35, cy+150, cx-17, cy+170, fill=1, stroke=0)
    c.ellipse(cx+17, cy+150, cx+35, cy+170, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-28, cy+163, 4, fill=1, stroke=0)
    c.circle(cx+22, cy+163, 4, fill=1, stroke=0)
    # Beak
    c.setFillColor(HexColor("#FFB300")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, cy+143)
    p.lineTo(cx-18, cy+120)
    p.lineTo(cx+18, cy+120)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Wings
    c.setFillColor(HexColor("#37474F")); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-140, cy-60, cx-70, cy+60, fill=1, stroke=1)
    c.ellipse(cx+70, cy-60, cx+140, cy+60, fill=1, stroke=1)
    # Feet
    c.setFillColor(HexColor("#FFB300")); c.setStrokeColor(black); c.setLineWidth(2)
    for fx in [cx-40, cx+10]:
        p = c.beginPath()
        p.moveTo(fx, cy-130)
        p.lineTo(fx-25, cy-165)
        p.lineTo(fx-10, cy-162)
        p.lineTo(fx, cy-185)
        p.lineTo(fx+10, cy-162)
        p.lineTo(fx+25, cy-165)
        p.lineTo(fx+30, cy-130)
        p.close()
        c.drawPath(p, fill=1, stroke=1)
    # Snowflakes
    c.setStrokeColor(HexColor("#81D4FA")); c.setLineWidth(1.5)
    for sx, sy in [(80,250),(W-80,250),(80,H-210),(W-80,H-210),(W/2-140,H/2),(W/2+140,H/2)]:
        draw_snowflake(c, sx, sy, 18)
    c.showPage()

def draw_snowflake(c, cx, cy, r):
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        c.line(cx, cy, cx+r*math.cos(rad), cy+r*math.sin(rad))

def draw_frog_page(c):
    page_header(c, "Freddy the Frog 🐸", 6)
    cx, cy = W/2, H/2 - 20
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-110, cy-100, cx+110, cy+80, fill=1, stroke=1)
    # Head
    c.ellipse(cx-90, cy+50, cx+90, cy+190, fill=1, stroke=1)
    # Eye bumps
    c.ellipse(cx-80, cy+175, cx-30, cy+225, fill=1, stroke=1)
    c.ellipse(cx+30, cy+175, cx+80, cy+225, fill=1, stroke=1)
    # Eyes
    c.setFillColor(HexColor("#A5D6A7"))
    c.ellipse(cx-75, cy+180, cx-35, cy+220, fill=1, stroke=1)
    c.ellipse(cx+35, cy+180, cx+75, cy+220, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx-67, cy+188, cx-43, cy+212, fill=1, stroke=0)
    c.ellipse(cx+43, cy+188, cx+67, cy+212, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-58, cy+205, 5, fill=1, stroke=0)
    c.circle(cx+50, cy+205, 5, fill=1, stroke=0)
    # Mouth (big smile)
    c.setStrokeColor(black); c.setLineWidth(3); c.setFillColor(HexColor("#EF9A9A"))
    c.arc(cx-70, cy+70, cx+70, cy+140, startAng=200, extent=140)
    # Nostrils
    c.setFillColor(black); c.setLineWidth(1)
    c.ellipse(cx-18, cy+158, cx-6, cy+168, fill=1, stroke=0)
    c.ellipse(cx+6, cy+158, cx+18, cy+168, fill=1, stroke=0)
    # Front legs
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-160, cy-30, cx-90, cy+40, fill=1, stroke=1)
    c.ellipse(cx+90, cy-30, cx+160, cy+40, fill=1, stroke=1)
    # Back legs
    c.ellipse(cx-150, cy-120, cx-60, cy-50, fill=1, stroke=1)
    c.ellipse(cx+60, cy-120, cx+150, cy-50, fill=1, stroke=1)
    # Webbed feet
    c.setFillColor(HexColor("#C8E6C9"))
    for fx, fy, flip in [(-155, cy-120, -1), (155, cy-120, 1)]:
        for toe_angle in [-30, 0, 30]:
            rad = math.radians(90 + toe_angle)
            c.ellipse(fx+flip*15*math.cos(rad)-12, fy-35, fx+flip*15*math.cos(rad)+12, fy, fill=1, stroke=1)
    # Lily pad
    c.setFillColor(HexColor("#A5D6A7")); c.setStrokeColor(HexColor("#388E3C")); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, cy-105)
    for angle in range(0, 360, 20):
        if 80 < angle < 100:
            continue
        rad = math.radians(angle)
        r = 140
        p.lineTo(cx+r*math.cos(rad), cy-105+r*0.3*math.sin(rad))
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(white)
    c.ellipse(cx-110, cy-80, cx+110, cy+80+20, fill=1, stroke=0)
    # Re-draw body on top of lily pad
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-110, cy-100, cx+110, cy+80, fill=1, stroke=1)
    # Water lines
    c.setStrokeColor(HexColor("#81D4FA")); c.setLineWidth(1.5)
    for wy in [cy-165, cy-185]:
        c.line(50, wy, W-50, wy)
    c.showPage()

def draw_owl_page(c):
    page_header(c, "Ollie the Owl 🦉", 7)
    cx, cy = W/2, H/2 - 10
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-90, cy-130, cx+90, cy+90, fill=1, stroke=1)
    # Head (round)
    c.ellipse(cx-80, cy+60, cx+80, cy+210, fill=1, stroke=1)
    # Ear tufts
    p = c.beginPath()
    p.moveTo(cx-60, cy+195)
    p.lineTo(cx-80, cy+250)
    p.lineTo(cx-30, cy+210)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx+60, cy+195)
    p.lineTo(cx+80, cy+250)
    p.lineTo(cx+30, cy+210)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Big eyes (owls have big eyes)
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-65, cy+110, cx-5, cy+180, fill=1, stroke=1)
    c.ellipse(cx+5, cy+110, cx+65, cy+180, fill=1, stroke=1)
    c.setFillColor(HexColor("#FF8F00"))
    c.ellipse(cx-58, cy+118, cx-12, cy+172, fill=1, stroke=0)
    c.ellipse(cx+12, cy+118, cx+58, cy+172, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-50, cy+126, cx-20, cy+164, fill=1, stroke=0)
    c.ellipse(cx+20, cy+126, cx+50, cy+164, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-40, cy+153, 6, fill=1, stroke=0)
    c.circle(cx+26, cy+153, 6, fill=1, stroke=0)
    # Beak
    c.setFillColor(HexColor("#FFB300")); c.setStrokeColor(black); c.setLineWidth(2)
    p = c.beginPath()
    p.moveTo(cx, cy+145)
    p.lineTo(cx-14, cy+108)
    p.lineTo(cx+14, cy+108)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Wings
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(cx-85, cy+60)
    p.curveTo(cx-160, cy+30, cx-155, cy-60, cx-85, cy-80)
    p.lineTo(cx-85, cy+60)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx+85, cy+60)
    p.curveTo(cx+160, cy+30, cx+155, cy-60, cx+85, cy-80)
    p.lineTo(cx+85, cy+60)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Wing feather lines
    c.setLineWidth(1.5)
    for i in range(4):
        y = cy - 60 + i * 35
        c.arc(cx-160, y-15, cx-85, y+15, startAng=60, extent=60)
        c.arc(cx+85, y-15, cx+160, y+15, startAng=60, extent=60)
    # Feet / talons
    c.setFillColor(HexColor("#FFB300")); c.setStrokeColor(black); c.setLineWidth(2)
    for fx in [cx-35, cx+10]:
        c.rect(fx, cy-145, 20, 40, fill=1, stroke=1)
        for toe in [-20, 0, 20, 40]:
            c.line(fx+10, cy-145, fx+toe, cy-175)
    # Branch
    c.setFillColor(HexColor("#8D6E63")); c.setStrokeColor(HexColor("#5D4037")); c.setLineWidth(5)
    c.rect(30, cy-175, W-60, 30, fill=1, stroke=1)
    # Stars / moon
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(HexColor("#FF8F00")); c.setLineWidth(1)
    for sx, sy in [(80,H-180),(W-80,H-180),(80,H-250),(W-80,H-250)]:
        draw_star(c, sx, sy, 15, 6)
    # Moon
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(HexColor("#FFD54F")); c.setLineWidth(2)
    c.circle(W/2, H-210, 28, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFF9C4"))
    c.circle(W/2+12, H-210, 22, fill=1, stroke=0)
    c.showPage()

def draw_bear_page(c):
    page_header(c, "Beary the Bear 🐻", 8)
    cx, cy = W/2, H/2 - 20
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Body
    c.ellipse(cx-105, cy-115, cx+105, cy+90, fill=1, stroke=1)
    # Tummy
    c.setFillColor(HexColor("#FFF9C4"))
    c.ellipse(cx-60, cy-80, cx+60, cy+65, fill=1, stroke=1)
    c.setFillColor(white); c.setStrokeColor(black)
    # Head
    c.ellipse(cx-85, cy+60, cx+85, cy+205, fill=1, stroke=1)
    # Ears
    c.ellipse(cx-100, cy+170, cx-48, cy+225, fill=1, stroke=1)
    c.ellipse(cx+48, cy+170, cx+100, cy+225, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFCCBC"))
    c.ellipse(cx-93, cy+175, cx-55, cy+218, fill=1, stroke=0)
    c.ellipse(cx+55, cy+175, cx+93, cy+218, fill=1, stroke=0)
    # Snout
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black)
    c.ellipse(cx-45, cy+80, cx+45, cy+130, fill=1, stroke=1)
    # Nose
    c.setFillColor(black)
    c.ellipse(cx-18, cy+115, cx+18, cy+138, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-8, cy+127, 5, fill=1, stroke=0)
    # Mouth
    c.setStrokeColor(black); c.setLineWidth(2)
    c.arc(cx-25, cy+65, cx, cy+88, startAng=0, extent=180)
    c.arc(cx, cy+65, cx+25, cy+88, startAng=0, extent=180)
    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-50, cy+150, cx-18, cy+182, fill=1, stroke=1)
    c.ellipse(cx+18, cy+150, cx+50, cy+182, fill=1, stroke=1)
    c.setFillColor(black)
    c.ellipse(cx-44, cy+156, cx-24, cy+176, fill=1, stroke=0)
    c.ellipse(cx+24, cy+156, cx+44, cy+176, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-36, cy+169, 4, fill=1, stroke=0)
    c.circle(cx+28, cy+169, 4, fill=1, stroke=0)
    # Arms
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-165, cy-30, cx-85, cy+50, fill=1, stroke=1)
    c.ellipse(cx+85, cy-30, cx+165, cy+50, fill=1, stroke=1)
    # Legs
    c.ellipse(cx-80, cy-185, cx-20, cy-100, fill=1, stroke=1)
    c.ellipse(cx+20, cy-185, cx+80, cy-100, fill=1, stroke=1)
    # Honey pot
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(HexColor("#FF8F00")); c.setLineWidth(2)
    c.rect(cx+100, cy-80, 55, 55, fill=1, stroke=1)
    c.ellipse(cx+97, cy-25, cx+158, cy-5, fill=1, stroke=1)
    c.rect(cx+112, cy-95, 30, 18, fill=1, stroke=1)
    c.setFillColor(HexColor("#FF8F00"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(cx+128, cy-58, "YUM")
    # Honey drips
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(HexColor("#FF8F00")); c.setLineWidth(1)
    for dx in [5, 20, 38]:
        c.roundRect(cx+100+dx, cy-90, 8, 20, 4, fill=1, stroke=1)
    # Bees
    draw_bee(c, cx-160, cy+180)
    draw_bee(c, cx+160, cy+180)
    c.showPage()

def draw_bee(c, cx, cy):
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.ellipse(cx-18, cy-8, cx+18, cy+8, fill=1, stroke=1)
    c.setFillColor(black)
    for bx in [-8, 2]:
        c.rect(cx+bx, cy-8, 8, 16, fill=1, stroke=0)
    c.setFillColor(HexColor("#E1F5FE"))
    c.ellipse(cx-12, cy+4, cx+2, cy+18, fill=1, stroke=1)
    c.ellipse(cx-2, cy+4, cx+12, cy+18, fill=1, stroke=1)
    c.setFillColor(black)
    c.circle(cx+10, cy+2, 3, fill=1, stroke=0)

def draw_lion_page(c):
    page_header(c, "Leo the Lion 🦁", 9)
    cx, cy = W/2, H/2 - 10
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Mane (big circle)
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(3)
    c.circle(cx, cy+130, 110, fill=1, stroke=1)
    # Mane texture (rays)
    c.setLineWidth(8); c.setStrokeColor(HexColor("#FFD54F"))
    for angle in range(0, 360, 30):
        rad = math.radians(angle)
        c.line(cx+85*math.cos(rad), cy+130+85*math.sin(rad),
               cx+108*math.cos(rad), cy+130+108*math.sin(rad))
    # Head
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-80, cy+65, cx+80, cy+205, fill=1, stroke=1)
    # Ears
    c.ellipse(cx-90, cy+185, cx-45, cy+225, fill=1, stroke=1)
    c.ellipse(cx+45, cy+185, cx+90, cy+225, fill=1, stroke=1)
    c.setFillColor(HexColor("#FFCCBC"))
    c.ellipse(cx-84, cy+190, cx-51, cy+218, fill=1, stroke=0)
    c.ellipse(cx+51, cy+190, cx+84, cy+218, fill=1, stroke=0)
    # Snout
    c.setFillColor(HexColor("#FFCCBC")); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-50, cy+88, cx+50, cy+140, fill=1, stroke=1)
    # Nose
    c.setFillColor(HexColor("#F48FB1"))
    p = c.beginPath()
    p.moveTo(cx, cy+135)
    p.lineTo(cx-14, cy+118)
    p.lineTo(cx+14, cy+118)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Mouth
    c.setStrokeColor(black); c.setLineWidth(2)
    c.arc(cx-30, cy+72, cx+2, cy+100, startAng=0, extent=180)
    c.arc(cx-2, cy+72, cx+30, cy+100, startAng=0, extent=180)
    # Whiskers
    c.setLineWidth(1.5)
    for i in range(3):
        c.line(cx-100, cy+102+i*10, cx-52, cy+112+i*3)
        c.line(cx+100, cy+102+i*10, cx+52, cy+112+i*3)
    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-52, cy+158, cx-18, cy+192, fill=1, stroke=1)
    c.ellipse(cx+18, cy+158, cx+52, cy+192, fill=1, stroke=1)
    c.setFillColor(HexColor("#A5D6A7"))
    c.ellipse(cx-47, cy+163, cx-23, cy+187, fill=1, stroke=0)
    c.ellipse(cx+23, cy+163, cx+47, cy+187, fill=1, stroke=0)
    c.setFillColor(black)
    c.ellipse(cx-42, cy+168, cx-28, cy+182, fill=1, stroke=0)
    c.ellipse(cx+28, cy+168, cx+42, cy+182, fill=1, stroke=0)
    c.setFillColor(white)
    c.circle(cx-36, cy+178, 4, fill=1, stroke=0)
    c.circle(cx+30, cy+178, 4, fill=1, stroke=0)
    # Body
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    c.ellipse(cx-100, cy-130, cx+100, cy+80, fill=1, stroke=1)
    # Legs
    for lx in [cx-65, cx-20, cx+20, cx+65]:
        c.rect(lx-18, cy-220, 36, 100, fill=1, stroke=1)
        c.ellipse(lx-22, cy-235, lx+22, cy-205, fill=1, stroke=1)
    # Tail with tuft
    c.setLineWidth(3)
    p = c.beginPath()
    p.moveTo(cx+98, cy+20)
    p.curveTo(cx+150, cy+50, cx+168, cy-20, cx+140, cy-60)
    c.drawPath(p, fill=0, stroke=1)
    c.setFillColor(HexColor("#FFD54F")); c.setStrokeColor(black); c.setLineWidth(2)
    c.circle(cx+138, cy-65, 18, fill=1, stroke=1)
    # Savanna grass
    c.setStrokeColor(HexColor("#A5D6A7")); c.setLineWidth(2)
    for gx in range(50, int(W)-50, 30):
        h_grass = 20 + (gx % 3) * 10
        c.line(gx, cy-240, gx-5, cy-240-h_grass)
    c.showPage()

def draw_butterfly_page(c):
    page_header(c, "Bella the Butterfly 🦋", 10)
    cx, cy = W/2, H/2
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(3)
    # Upper wings
    p = c.beginPath()
    p.moveTo(cx, cy+30)
    p.curveTo(cx-30, cy+120, cx-180, cy+160, cx-180, cy+60)
    p.curveTo(cx-180, cy-30, cx-80, cy-20, cx, cy+30)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx, cy+30)
    p.curveTo(cx+30, cy+120, cx+180, cy+160, cx+180, cy+60)
    p.curveTo(cx+180, cy-30, cx+80, cy-20, cx, cy+30)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Lower wings
    p = c.beginPath()
    p.moveTo(cx, cy+30)
    p.curveTo(cx-40, cy-20, cx-160, cy-80, cx-140, cy-150)
    p.curveTo(cx-120, cy-200, cx-40, cy-160, cx, cy+30)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    p = c.beginPath()
    p.moveTo(cx, cy+30)
    p.curveTo(cx+40, cy-20, cx+160, cy-80, cx+140, cy-150)
    p.curveTo(cx+120, cy-200, cx+40, cy-160, cx, cy+30)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # Wing patterns - circles
    c.setFillColor(HexColor("#FFF9C4")); c.setStrokeColor(black); c.setLineWidth(1.5)
    for px, py, pr in [(-110, cy+80, 30),(-120, cy+30, 20),(-80, cy-100, 25),(110, cy+80, 30),(120, cy+30, 20),(80, cy-100, 25)]:
        c.circle(cx+px, py, pr, fill=1, stroke=1)
    # Smaller circles
    c.setFillColor(HexColor("#F8BBD0"))
    for px, py, pr in [(-90, cy+100, 15),(-100, cy+55, 12),(90, cy+100, 15),(100, cy+55, 12)]:
        c.circle(cx+px, py, pr, fill=1, stroke=1)
    # Body
    c.setFillColor(HexColor("#37474F")); c.setStrokeColor(black); c.setLineWidth(2)
    c.ellipse(cx-10, cy-140, cx+10, cy+80, fill=1, stroke=1)
    # Head
    c.setFillColor(HexColor("#37474F"))
    c.circle(cx, cy+100, 20, fill=1, stroke=1)
    # Eyes
    c.setFillColor(white); c.setStrokeColor(black); c.setLineWidth(1.5)
    c.circle(cx-8, cy+105, 7, fill=1, stroke=1)
    c.circle(cx+8, cy+105, 7, fill=1, stroke=1)
    c.setFillColor(black)
    c.circle(cx-8, cy+105, 3, fill=1, stroke=0)
    c.circle(cx+8, cy+105, 3, fill=1, stroke=0)
    # Antennae
    c.setStrokeColor(HexColor("#37474F")); c.setLineWidth(2)
    c.line(cx-5, cy+118, cx-30, cy+160)
    c.line(cx+5, cy+118, cx+30, cy+160)
    c.setFillColor(HexColor("#F48FB1")); c.setStrokeColor(black); c.setLineWidth(1)
    c.circle(cx-30, cy+160, 7, fill=1, stroke=1)
    c.circle(cx+30, cy+160, 7, fill=1, stroke=1)
    # Flowers at bottom
    for fx, fy in [(80, 70), (W-80, 70), (W/2, 55)]:
        draw_flower(c, fx, fy, 20)
    c.showPage()

# ---- BONUS PAGES ----
def draw_color_guide_page(c):
    c.setFillColor(HexColor("#FFF9C4"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#F48FB1")); c.setLineWidth(5)
    c.rect(15, 15, W-30, H-30, fill=0, stroke=1)
    c.setFillColor(HexColor("#F48FB1")); c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H-80, "Color the Animals!")
    c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 18)
    c.drawCentredString(W/2, H-120, "Here are some ideas for colors to use:")
    colors = [
        ("🐰 Bunny", "White, Pink, Grey"),
        ("🐘 Elephant", "Grey, Light Purple"),
        ("🦆 Duck", "Yellow, Orange"),
        ("🐶 Dog", "Brown, Golden, White"),
        ("🐧 Penguin", "Black & White, Orange"),
        ("🐸 Frog", "Green, Bright Green"),
        ("🦉 Owl", "Brown, Orange, White"),
        ("🐻 Bear", "Brown, Tan, Gold"),
        ("🦁 Lion", "Golden Yellow, Orange"),
        ("🦋 Butterfly", "Any colors you like!"),
    ]
    y = H - 165
    c.setFont("Helvetica-Bold", 16)
    for animal, color_hint in colors:
        c.setFillColor(HexColor("#6A1B9A"))
        c.drawString(80, y, animal)
        c.setFillColor(HexColor("#37474F"))
        c.setFont("Helvetica", 15)
        c.drawString(280, y, color_hint)
        c.setFont("Helvetica-Bold", 16)
        y -= 34
    c.setFillColor(HexColor("#F48FB1")); c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(W/2, 90, "✨ Use ANY colors you want! ✨")
    c.setFillColor(HexColor("#37474F")); c.setFont("Helvetica", 14)
    c.drawCentredString(W/2, 60, "There are no wrong colors in art!")
    c.showPage()

def make_book():
    c = new_canvas("cute_animals_coloring_book.pdf")
    draw_cover(c)
    draw_color_guide_page(c)
    draw_bunny_page(c)
    draw_elephant_page(c)
    draw_duck_page(c)
    draw_dog_page(c)
    draw_penguin_page(c)
    draw_frog_page(c)
    draw_owl_page(c)
    draw_bear_page(c)
    draw_lion_page(c)
    draw_butterfly_page(c)
    c.save()
    print("Done: cute_animals_coloring_book.pdf")

make_book()