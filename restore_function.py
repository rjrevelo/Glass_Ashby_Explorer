import re

file_path = r"d:\Cursor_Proyectos\Glass_Ashby\web\working_glass_dashboard_2k.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# scaleXY function implementation
scale_xy_func = """
    function scaleXY() {
      return {
        sx: document.querySelector('input[name="scaleX"]:checked').value,
        sy: document.querySelector('input[name="scaleY"]:checked').value
      };
    }
"""

if "function scaleXY()" not in content:
    # Insert it before buildChart or another suitable place
    content = content.replace('function buildChart() {', scale_xy_func + '\n    function buildChart() {')
    print("Re-inserted scaleXY function.")
else:
    print("scaleXY function already exists?! (Grep might have missed it if it was slightly different)")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
