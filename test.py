from vpython import *

# Create an object
sphere_obj = sphere(pos=vector(0, 0, 0), radius=0.5)

def handle_checkbox():
    sphere_obj.make_trail = checkbox_widget.checked

# Create a checkbox widget
checkbox_widget = checkbox(text="Enable Trail", bind = handle_checkbox)

while True:
    rate(60)  # Adjust the animation speed as needed