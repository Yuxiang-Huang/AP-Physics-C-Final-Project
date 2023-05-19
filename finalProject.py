import vpython

# set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1

#constants (don't ask me when k is so low, I will change it later!!!)
K = 9E-7

# store all spawned charges
allChargedObjs = []

# Class Charge
class ChargedObj:
    def __init__(self, mass, charge, spawnPos, spawnVel):
        # physics variables
        self.charge = charge
        self.mass = mass
        self.pos = spawnPos
        self.vel = spawnVel
        # Displays
        # spheres for now
        if (charge < 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.red)
        if (charge > 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.blue)
        if (charge == 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.black)
        self.velVec = vpython.arrow(axis = vpython.vector(0, 0, 0), color = self.display.color)
    
    def applyForce(self):
        # calculate force from  every other charge
        force = vpython.vector(0, 0, 0)
        for chargedObj in allChargedObjs:
            if (chargedObj != self):
                if (vpython.mag(self.pos - chargedObj.pos) > 2 * self.display.radius):
                    force += calculateForce(self, chargedObj)
        # apply force
        self.vel += force / self.mass

    def applyVel(self):
        self.pos += self.vel
        self.display.pos = self.pos
    
    def checkCollision(self):
        for chargedObj in allChargedObjs:
            if (vpython.mag(self.pos - chargedObj.pos) <= 2 * self.display.radius):
                self.vel = vpython.vector(0, 0, 0)
                chargedObj.vel = vpython.vector(0, 0, 0)

# Coulomb's Law
def calculateForce(q1, q2):
    r12 = q1.pos - q2.pos
    return vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

####################################################################################################

# Clicks
def clicked():
    if (clickMode == "Spawn"):
        makeChargeObj()
    # elif (clickMode == "Select"):
    #     selectCharge()

vpython.scene.bind('click', clicked)

def makeChargeObj():
    allChargedObjs.append(ChargedObj(1, spawnCharge, getMousePos(), vpython.vector(0, 0, 0)))

def chargedObjOnMouse():
    mousePos = getMousePos()
    for chargedObj in allChargedObjs:
        if (vpython.mag(mousePos - chargedObj.pos) <= chargedObj.display.radius):
            return chargedObj
        
def getMousePos():
    return vpython.scene.mouse.project(normal=vpython.vector(0, 0, 1))

# dragging
chargedObjToDrag = None

def on_mouse_down():
    global chargedObjToDrag
    chargedObjToDrag = chargedObjOnMouse()

def on_mouse_up():
    global chargedObjToDrag
    chargedObjToDrag = None

def on_mouse_move():
    # if (clickMode == "Spawn"):
    #     if chargedObjToDrag != None:
    #         chargedObjToDrag.pos = getMousePos()
    #         chargedObjToDrag.display.pos = chargedObjToDrag.pos
    # else:
    if chargedObjToDrag != None:
        chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
        chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
        chargedObjToDrag.display.vel = chargedObjToDrag.velVec.axis

# Bind event handlers to the box
vpython.scene.bind('mousedown', on_mouse_down)
vpython.scene.bind('mouseup', on_mouse_up)
vpython.scene.bind('mousemove', on_mouse_move)

####################################################################################################

# Button and Sliders

# mode button
clickMode = "Spawn"

def changeClickModeButton():
    global clickMode, clickModeButton
    if clickMode == "Spawn":
        clickMode = "Select"
    else:
        clickMode = "Spawn"
    clickModeButton.text = "Mode: " + clickMode

vpython.scene.append_to_caption("   ")
clickModeButton = vpython.button(text="Mode: Spawn", bind=changeClickModeButton)

# spawn slider
spawnCharge = -1

def spawnChargeShift():
    global spawnCharge, spawnChargeText
    spawnCharge = s.value
    spawnChargeText.text = 'Charge:'+'{:1.2f}'.format(s.value)

s = vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = -1)
spawnChargeText = vpython.wtext(text = 'Charge:'+'{:1.2f}'.format(s.value))

# playing button
playing = False

def changePlayButton():
    global playing, playButton
    playing = not playing
    if playing:
        playButton.text = "Stop"
    else:
        playButton.text = "Play"

vpython.scene.append_to_caption("   ")
playButton = vpython.button(text="Play", bind=changePlayButton)

while True:
    vpython.rate(1000)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    # for charge in allChargedObjs:
    #     charge.checkCollision()
        
