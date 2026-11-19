"""Render the board to PNG for review.  render.py OUT.png [layers] [px_per_mm] [x0 y0 x1 y1 crop in board mm]"""
import subprocess, sys, os, tempfile
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo
from common import PCB, W, H, OX, OY
PCB = os.environ.get('PCB', PCB)

out = sys.argv[1]
layers = sys.argv[2] if len(sys.argv) > 2 else 'F.Cu,B.Cu,F.SilkS,Edge.Cuts'
ppm = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0
crop = [float(v) for v in sys.argv[4:8]] if len(sys.argv) >= 8 else [0, 0, W, H]
svg = os.path.join(tempfile.gettempdir(), 'afe_render.svg')
subprocess.run(['kicad-cli', 'pcb', 'export', 'svg', '--mode-single', '--exclude-drawing-sheet',
                '--layers', layers, '-o', svg, PCB], check=True, capture_output=True)
h = Rsvg.Handle.new_from_file(svg)
ok, w_svg, h_svg = h.get_intrinsic_size_in_pixels()
dim = h.get_intrinsic_dimensions()
sx = w_svg / 297.0          # A4 page, svg px per mm
x0, y0, x1, y1 = crop
s = ppm / sx
surf = cairo.ImageSurface(cairo.FORMAT_RGB24, int((x1 - x0) * ppm), int((y1 - y0) * ppm))
ctx = cairo.Context(surf)
ctx.set_source_rgb(1, 1, 1); ctx.paint()
ctx.scale(s, s); ctx.translate(-(x0 + OX) * sx, -(y0 + OY) * sx)
vp = Rsvg.Rectangle(); vp.x, vp.y, vp.width, vp.height = 0, 0, w_svg, h_svg
h.render_document(ctx, vp)
surf.write_to_png(out)
print(out, surf.get_width(), 'x', surf.get_height())
