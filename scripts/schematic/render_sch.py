"""Render a region of the schematic to PNG: render_sch.py OUT.png x0 y0 x1 y1 [px_per_mm]"""
import subprocess, sys, os, tempfile, glob
import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Rsvg
import cairo
from sch import SCH
out = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6]); ppm = float(sys.argv[6]) if len(sys.argv) > 6 else 4
d = tempfile.mkdtemp()
subprocess.run(['kicad-cli', 'sch', 'export', 'svg', '-o', d, SCH], check=True, capture_output=True)
h = Rsvg.Handle.new_from_file(glob.glob(d + '/*.svg')[0])
ok, w, hh = h.get_intrinsic_size_in_pixels()
sx = w / 841.0
s = cairo.ImageSurface(cairo.FORMAT_RGB24, int((x1 - x0) * ppm), int((y1 - y0) * ppm)); c = cairo.Context(s)
c.set_source_rgb(1, 1, 1); c.paint(); c.scale(ppm / sx, ppm / sx); c.translate(-x0 * sx, -y0 * sx)
vp = Rsvg.Rectangle(); vp.x, vp.y, vp.width, vp.height = 0, 0, w, hh
h.render_document(c, vp); s.write_to_png(out); print(out)
