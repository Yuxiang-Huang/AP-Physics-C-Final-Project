import vpython

# set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 1
# Use it to make it seem 2D
# vpython.scene.fov = vpython.pi / 6

#constants
K = 9E9
vectorAxisFactor = 300
spawnDensity = 2500 
steps = 10
epsilon = 0.01

# electric field stuff
electricFieldOpacitySetter = 1E4
precision = 10

# Test place

# Initilization

electricFieldArrowsAll = [ [0]*precision for i in range(precision)]
for i in range(precision):
    for j in range(precision):
        electricFieldArrowsAll[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.orange)

def setElectricFieldArrowsAll():
    for i in range(precision):
        for j in range(precision):
            electricFieldArrowsAll[i][j].visible = True
            # assume height > width
            electricFieldArrowsAll[i][j].pos = vpython.vec(
                        (i - precision / 2) * 2 * vpython.scene.width / vpython.scene.height * vpython.scene.range / precision, 
                        (j - precision / 2) * 2 * vpython.scene.range / precision, 0)
            electricFieldArrowsAll[i][j].pos += vpython.vec(
                        vpython.scene.width / vpython.scene.height * vpython.scene.range / precision, 
                        vpython.scene.range / precision, 0)
            
setElectricFieldArrowsAll()

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
        self.fixed = False
        # Displays
        spawnRadius = ((spawnMass) / (((4/3)* vpython.pi*spawnDensity)))**(1/3)
        # spheres for now
        if (charge > 0):
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, color = vpython.color.red)
        if (charge < 0):
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, color = vpython.color.blue)
        if (charge == 0):
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, color = vpython.color.black)
        self.velVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
        self.forceVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
        
        # electric field
        # possibly sliders for more variables
        self.numOfLine = 8
        # initialize all the arrows
        self.electricFieldArrows = [ [0]*precision for i in range(self.numOfLine)]
        for i in range(self.numOfLine):
            for j in range(precision):
                self.electricFieldArrows[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = self.display.color)
        
        # select display
        self.selectDisplay = []
        self.createSelectDisplay()

    def createSelectDisplay(self):
        # Math with a circle to create arcs
        thetaRange = vpython.pi / 4
        for x in range(4):
            arc = vpython.curve()
            initialTheta = x * vpython.pi / 2 + vpython.pi / 4
            for i in range(steps):
                theta = i * thetaRange / steps + initialTheta - thetaRange / 2 
                arc.append(vpython.vec(vpython.cos(theta) * (self.display.radius + epsilon), 
                                    vpython.sin(theta) * (self.display.radius + epsilon), 0) + self.pos
                                    , color = vpython.color.yellow) 
            
            self.selectDisplay.append(arc)
        for arc in self.selectDisplay:
            arc.visible = False
    
    def displaySelect(self):
        thetaRange = vpython.pi / 4
        for x in range(4):
            arc = self.selectDisplay[x]
            initialTheta = x * vpython.pi / 2 + vpython.pi / 4
            for i in range(steps):
                theta = i * thetaRange / steps + initialTheta - thetaRange / 2 
                arc.modify(i, pos = vpython.vec(vpython.cos(theta) * (self.display.radius + epsilon), 
                                    vpython.sin(theta) * (self.display.radius + epsilon), 0) + self.pos
                                    , color = vpython.color.yellow)
            arc.visible = True
    
    def hideSelect(self):
        for x in range(4):
            arc = self.selectDisplay[x]
            arc.visible = False
                    
    def applyForce(self):
        # calculate force from every other charge
        if (not self.fixed):
            force = vpython.vec(0, 0, 0)
            for chargedObj in allChargedObjs:
                if (chargedObj != self):
                    if (vpython.mag(self.pos - chargedObj.pos) > 2 * self.display.radius):
                        force += calculateForce(self, chargedObj)
            # apply force
            self.vel += force / self.mass

    def applyVel(self):
        if (not self.fixed):
            self.pos += self.vel
            self.display.pos = self.pos
            if (self == chargedObjSelected):
                self.displaySelect()
    
    def checkCollision(self):
        for chargedObj in allChargedObjs:
            if (vpython.mag(self.pos - chargedObj.pos) <= 2 * self.display.radius):
                self.vel = vpython.vec(0, 0, 0)
                chargedObj.vel = vpython.vec(0, 0, 0)

    def displayElectricField(self):
        if (electricFieldMode == 1):
            # determine size
            size = vpython.scene.range / 10
            # for every direction
            for i in range(self.numOfLine):
                # determine starting position
                theta = i * 2 * vpython.pi / self.numOfLine
                curPos = self.pos + vpython.vec(vpython.cos(theta), vpython.sin(theta), 0) * self.display.radius
                endForTooClose = False
                #for every step
                for j in range(precision):
                    # stop if too close to a charge
                    if (tooClose(self, curPos, size)):
                        endForTooClose = True
                    if (endForTooClose):
                        self.electricFieldArrows[i][j].visible = False
                    else:
                        # determine the arrow and the next position
                        electricField = calculateElectricField(curPos)
                        arrowLength = vpython.norm(electricField) * size
                        self.electricFieldArrows[i][j].visible = True
                        self.electricFieldArrows[i][j].pos = curPos
                        if (self.charge < 0):
                            self.electricFieldArrows[i][j].pos -= arrowLength
                        self.electricFieldArrows[i][j].axis = arrowLength
                        self.electricFieldArrows[i][j].opacity = vpython.mag(electricField) / electricFieldOpacitySetter
                        curPos += arrowLength * self.charge / abs(self.charge)
        else: 
            # hide all electric field arrows
            for i in range(self.numOfLine):   
                for j in range(precision):
                    self.electricFieldArrows[i][j].visible = False

# Coulomb's Law for force of q2 on q1
def calculateForce(q1, q2):
    r12 = q1.pos - q2.pos
    return vpython.norm(r12) * K * q1.charge * q2.charge / (vpython.mag(r12)**2)

####################################################################################################

# Electric Field

def displayElectricFieldAll():
    if (electricFieldMode == 2):
        size = vpython.scene.range / 20
        for i in range(precision):
            for j in range(precision):
                electricFieldArrowsAll[i][j].visible = True
                electricFieldArrowsAll[i][j].axis = vpython.norm(calculateElectricField(electricFieldArrowsAll[i][j].pos)) * size
    else:
        # hide all electric field
        for i in range(precision):
            for j in range(precision):
                electricFieldArrowsAll[i][j].visible = False
    
def calculateElectricField(pos):
    electricField = vpython.vec(0, 0, 0)
    for chargedObj in allChargedObjs:
        r = pos - chargedObj.pos
        # just check for now before I figure out what to do in this case
        if (vpython.mag(r) != 0):
            electricField += vpython.norm(r) * K * chargedObj.charge / (vpython.mag(r)**2)
    return electricField

def tooClose(owner, pos, size):
    for chargedObj in allChargedObjs:
            if (chargedObj != owner):
                if vpython.mag(pos - chargedObj.pos) < chargedObj.display.radius + size:
                    return True
    return False

####################################################################################################

# Clicks
chargedObjSelected = None

def clicked():
    global chargedObjSelected
    # only when not playing
    if (not playing):
        # When no charge is selected, try spawn or select charge 
        if (chargedObjSelected == None):
            chargedObjSelected = chargedObjOnMouse()
            if (chargedObjSelected == None):
                makeChargeObj()
            else:
                chargedObjSelected.displaySelect()
        else:
            # deselect if needed
            if (chargedObjSelected != None):
                chargedObjSelected.hideSelect()
            chargedObjSelected = chargedObjOnMouse()
            if (chargedObjSelected != None):
                chargedObjSelected.displaySelect()

vpython.scene.bind('click', clicked)

def makeChargeObj():
    allChargedObjs.append(ChargedObj(spawnMass, spawnCharge, getMousePos(), vpython.vec(0, 0, 0)))

def chargedObjOnMouse():
    mousePos = getMousePos()
    for chargedObj in allChargedObjs:
        if (vpython.mag(mousePos - chargedObj.pos) <= chargedObj.display.radius):
            return chargedObj
        
def getMousePos():
    return vpython.scene.mouse.project(normal=vpython.vec(0, 0, 1))

# dragging
chargedObjToDrag = None
mouseDown = False

def on_mouse_down():
    global chargedObjToDrag, mouseDown
    chargedObjToDrag = chargedObjOnMouse()
    mouseDown = True

def on_mouse_up():
    global chargedObjToDrag, mouseDown
    # apply force vector if necessary
    if (chargedObjSelected != None):
        if (chargedObjSelected.forceVec.axis != vpython.vec(0, 0, 0)):
            chargedObjSelected.vel += chargedObjSelected.forceVec.axis / vectorAxisFactor / chargedObjSelected.mass 
            chargedObjSelected.forceVec.axis = vpython.vec(0, 0, 0)
    chargedObjToDrag = None
    mouseDown = False

def on_mouse_move():
    if (chargedObjSelected == None):
        # set position
        if chargedObjToDrag != None:
            mousePos = getMousePos()
            chargedObjToDrag.pos = mousePos
            chargedObjToDrag.display.pos = chargedObjToDrag.pos
            chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
    else:
        if chargedObjToDrag != None:
            # velocity vector
            if (not playing):
                chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
                chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
                # too small reset
                if (vpython.mag(chargedObjToDrag.velVec.axis) < chargedObjToDrag.display.radius):
                    chargedObjToDrag.velVec.axis = vpython.vec(0, 0, 0)
                chargedObjToDrag.vel = chargedObjToDrag.velVec.axis / vectorAxisFactor

# Bind event handlers to the box
vpython.scene.bind('mousedown', on_mouse_down)
vpython.scene.bind('mouseup', on_mouse_up)
vpython.scene.bind('mousemove', on_mouse_move)

####################################################################################################

# Button and Sliders

# spawn slider
spawnCharge = 10E-9

def spawnChargeShift():
    global spawnCharge, spawnChargeText
    spawnCharge = s.value * 10E-9
    spawnChargeText.text = 'Charge (nC):'+'{:1.2f}'.format(s.value)
    
s = vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = 1, step = 0.1)
spawnChargeText = vpython.wtext(text = 'Charge (nC):'+'{:1.2f}'.format(s.value))

# mass slider

spawnMass = 1

def mShift():
    global spawnMass
    spawnMass = m.value
    mShiftText.text = 'Mass: '+'{:1.2f}'.format(m.value)
m = vpython.slider(bind=mShift, min = 1, max =2, value =1, step = 0.1) 
mShiftText = vpython.wtext(text = 'Mass: '+'{:1.2f}'.format(m.value))

# delete button
def deleteChargedObj():
    global chargedObjSelected
    if (chargedObjSelected != None):
        # hide everything, remove from list, reset chargedObjSelected
        chargedObjSelected.display.visible = False
        chargedObjSelected.velVec.visible = False
        chargedObjSelected.forceVec.visible = False
        chargedObjSelected.hideSelect()
        for i in range(chargedObjSelected.numOfLine):   
                for j in range(precision):
                    chargedObjSelected.electricFieldArrows[i][j].visible = False
        allChargedObjs.remove(chargedObjSelected)
        chargedObjSelected = None

vpython.scene.append_to_caption("   ")
deleteButton = vpython.button(text="Delete", bind=deleteChargedObj)

# fix button
def fixChargedObj():
    if (chargedObjSelected != None):
        chargedObjSelected.fixed = not chargedObjSelected.fixed

vpython.scene.append_to_caption("   ")
fixButton = vpython.button(text="Fix", bind=fixChargedObj)

# electic field button
electricFieldMode = 0

def changeElectricField():
    global electricFieldMode, electricFieldButton
    electricFieldMode += 1
    if electricFieldMode == 3:
        electricFieldMode = 0
    electricFieldButton.text = "Electric Field: Mode " + str(electricFieldMode)

vpython.scene.append_to_caption("   ")
electricFieldButton = vpython.button(text="Electric Field: Mode 0", bind=changeElectricField)

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
            co.velVec.visible = False
    else:
        for co in allChargedObjs:
            co.velVec.visible = True
            co.velVec.pos = co.pos
            co.velVec.axis = co.vel * vectorAxisFactor

vpython.scene.append_to_caption("   ")
playButton = vpython.button(text="Play", bind=changePlay)

curRange = vpython.scene.range

while True:
    vpython.rate(1000)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    for chargedObj in allChargedObjs:
        chargedObj.displayElectricField()

    # reset electric field arrows for all if user zooms
    if (curRange != vpython.scene.range):
        curRange = vpython.scene.range
        setElectricFieldArrowsAll()

    displayElectricFieldAll()
    # for charge in allChargedObjs:
    #     charge.checkCollision()

    # update force vector because it is possible that mouse is not moving
    if (playing and mouseDown and chargedObjSelected != None):
        chargedObjSelected.forceVec.pos = chargedObjSelected.pos
        chargedObjSelected.forceVec.axis = getMousePos() - chargedObjSelected.pos 

        
