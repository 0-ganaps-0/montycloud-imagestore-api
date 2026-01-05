
#!/usr/bin/env python3
# Generates a tiny red PNG to stdout
from PIL import Image
import sys
img = Image.new('RGB', (16, 16), color=(255,0,0))
img.save(sys.stdout.buffer, format='PNG')
