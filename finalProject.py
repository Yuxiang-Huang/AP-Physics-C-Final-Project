import vpython

# set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1

#constants (don't ask me when k is so low, I will change it later!!!)
K = 9E-7
# I will figure it out so I don't need to divide by 1000 later !!!
vectorAxisFactor = 500

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
        if (charge > 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.red)
        if (charge < 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.blue)
        if (charge == 0):
            self.display = vpython.sphere(pos=spawnPos, radius=0.05, color = vpython.color.black)
        self.velVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
        self.forceVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
        
        # electric field
        # possibly sliders for more variables
        self.numOfLine = 8
        self.steps = 10
        # initialize all the arrows
        self.electricFieldArrows = [ [0]*self.steps for i in range(self.numOfLine)]
        for i in range(self.numOfLine):
            for j in range(self.steps):
                self.electricFieldArrows[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
    
    def applyForce(self):
        # calculate force from every other charge
        force = vpython.vec(0, 0, 0)
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
                self.vel = vpython.vec(0, 0, 0)
                chargedObj.vel = vpython.vec(0, 0, 0)

    def displayElectricField(self):
        if (displayElectricField):
            size = vpython.scene.range / 10
            for i in range(self.numOfLine):
                theta = i * 2 * vpython.pi / self.numOfLine
                curPos = self.pos + vpython.vec(vpython.cos(theta), vpython.sin(theta), 0) * self.display.radius * 2
                for j in range(self.steps):
                    electricField = vpython.norm(calculateElectricField(curPos)) * size
                    self.electricFieldArrows[i][j].visible = True
                    self.electricFieldArrows[i][j].pos = curPos
                    self.electricFieldArrows[i][j].axis = electricField
                    curPos += electricField * self.charge / abs(self.charge)
        else: 
            for i in range(self.numOfLine):   
                for j in range(self.steps):
                    self.electricFieldArrows[i][j].visible = False

# Coulomb's Law for force of q2 on q1
def calculateForce(q1, q2):
    r12 = q1.pos - q2.pos
    return vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

####################################################################################################

# Electric Field
    
def calculateElectricField(pos):
    electricField = vpython.vec(0, 0, 0)
    for chargedObj in allChargedObjs:
        r = pos - chargedObj.pos
        # just check for now before I figure out what to do in this case
        if (vpython.mag(r) != 0):
            electricField += vpython.norm(r) * K * chargedObj.charge / (vpython.mag(r)**2)
    return electricField

####################################################################################################

# Clicks
chargedObjSelected = None

def clicked():
    if (clickMode == "Spawn"):
        makeChargeObj()
    elif (clickMode == "Select"):
        selectCharge()

vpython.scene.bind('click', clicked)

def makeChargeObj():
    allChargedObjs.append(ChargedObj(1, spawnCharge, getMousePos(), vpython.vec(0, 0, 0)))

def selectCharge():
    global chargedObjSelected
    chargedObjSelected = chargedObjOnMouse()

def chargedObjOnMouse():
    mousePos = getMousePos()
    for chargedObj in allChargedObjs:
        if (vpython.mag(mousePos - chargedObj.pos) <= chargedObj.display.radius):
            return chargedObj
        
def getMousePos():
    return vpython.scene.mouse.project(normal=vpython.vec(0, 0, 1))

# dragging
chargedObjToDrag = None

def on_mouse_down():
    global chargedObjToDrag
    chargedObjToDrag = chargedObjOnMouse()

def on_mouse_up():
    global chargedObjToDrag
    # apply force vector if necessary
    if (chargedObjToDrag != None):
        if (chargedObjToDrag.forceVec.axis != vpython.vec(0, 0, 0)):
            chargedObjToDrag.vel += chargedObjToDrag.forceVec.axis / vectorAxisFactor / chargedObjToDrag.mass 
            chargedObjToDrag.forceVec.axis = vpython.vec(0, 0, 0)
    chargedObjToDrag = None

def on_mouse_move():
    if (clickMode == "Spawn"):
        # set position
        if chargedObjToDrag != None:
            chargedObjToDrag.pos = getMousePos()
            chargedObjToDrag.display.pos = chargedObjToDrag.pos
            chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
    else:
        if chargedObjToDrag != None:
            # force vector
            if (playing):
                chargedObjToDrag.forceVec.pos = chargedObjToDrag.pos
                chargedObjToDrag.forceVec.axis = getMousePos() - chargedObjToDrag.pos 
            # velocity vector
            else:
                chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
                chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
                chargedObjToDrag.vel = chargedObjToDrag.velVec.axis / vectorAxisFactor

# Bind event handlers to the box
vpython.scene.bind('mousedown', on_mouse_down)
vpython.scene.bind('mouseup', on_mouse_up)

####################################################################################################

# Button and Sliders

# mode button
clickMode = "Spawn"

def changeClickMode():
    global clickMode, clickModeButton
    if clickMode == "Spawn":
        clickMode = "Select"
    else:
        clickMode = "Spawn"
    clickModeButton.text = "Mode: " + clickMode

vpython.scene.append_to_caption("   ")
clickModeButton = vpython.button(text="Mode: Spawn", bind=changeClickMode)

# spawn slider
spawnCharge = 1

def spawnChargeShift():
    global spawnCharge, spawnChargeText
    spawnCharge = s.value
    spawnChargeText.text = 'Charge:'+'{:1.2f}'.format(s.value)

s = vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = 1)
spawnChargeText = vpython.wtext(text = 'Charge:'+'{:1.2f}'.format(s.value))

# delete button
def deleteChargedObj():
    if (chargedObjSelected != None):
        chargedObjSelected.display.visible = False
        chargedObjSelected.velVec.visible = False
        chargedObjSelected.forceVec.visible = False
        allChargedObjs.remove(chargedObjSelected)

vpython.scene.append_to_caption("   ")
deleteButton = vpython.button(text="Delete", bind=deleteChargedObj)

# delete button
displayElectricField = True

def changeElectricField():
    global displayElectricField, electricFieldButton
    displayElectricField = not displayElectricField
    if displayElectricField:
        electricFieldButton.text = "Electric Field: On"
    else:
        electricFieldButton.text = "Electric Field: Off"

vpython.scene.append_to_caption("   ")
electricFieldButton = vpython.button(text="Electric Field: On", bind=changeElectricField)

# playing button
playing = False

def changePlay():
    global playing, playButton
    playing = not playing
    if playing:
        playButton.text = "Stop"
    else:
        playButton.text = "Play"
    #set velocity vector visibilities
    if (playing):
        for co in allChargedObjs:
            co.velVec.axis = vpython.vec(0, 0, 0)
    else:
        for co in allChargedObjs:
            co.velVec.pos = co.pos
            co.velVec.axis = co.vel * vectorAxisFactor

vpython.scene.append_to_caption("   ")
playButton = vpython.button(text="Play", bind=changePlay)

while True:
    vpython.rate(1000)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    for chargedObj in allChargedObjs:
        chargedObj.displayElectricField()
    # for charge in allChargedObjs:
    #     charge.checkCollision()

    # need to call mouse move any frame since for force vector mouse could have been not moving
    on_mouse_move()
        
