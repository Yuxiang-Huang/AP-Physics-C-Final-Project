from vpython import *

####################################################################################################

# region Variables

# set scene
scene.background = color.white
scene.width = 1000
scene.height = 650
scene.range = 10
scene.userzoom = False
scene.userspin = False
scene.fov = pi / 50
scene.align = "left"

#constants
K = 9E9
spawnDensity = 2.5E-6
steps = 10
epsilon = 0.01
numOfRate = 1000
sliderLength = 450
electricFieldOpacitySetter = 1
forceScaler = 1E6

# texture links
positiveSphereTexture = "https://i.imgur.com/9c10QCm.png"
negativeSphereTexture = "https://i.imgur.com/r6loarb.png"
neutralSphereTexture = "https://i.imgur.com/eLOxvSS.png"

fixedPositiveSphereTexture = "https://i.imgur.com/ADy8l2o.png"
fixedNegativeSphereTexture = "https://i.imgur.com/ReG5wU7.png"
fixedNeutralSphereTexture = "https://i.imgur.com/b80Axoa.png"

# endregion

####################################################################################################

# region Initilization

unitWidth = None
unitHeight = None

# Math for rescaling (assume height > width)
def setUnits():
    global unitWidth, unitHeight
    unitWidth = 2 * scene.width / scene.height * scene.range / gridPrecision
    unitHeight = 2 * scene.range / gridPrecision

# region electric field for mode 2
electricFieldArrowsAll = None

# create when click start after know precision
def createElectricFieldArrowsAll():
    global electricFieldArrowsAll
    # dimension = precision by precision
    electricFieldArrowsAll = [ [0]*gridPrecision for i in range(gridPrecision)]
    for i in range(gridPrecision):
        for j in range(gridPrecision):
            electricFieldArrowsAll[i][j] = arrow(axis = vec(0, 0, 0), color = color.orange)

# method for rescaling
def setElectricFieldArrowsAll():
    for i in range(gridPrecision):
        for j in range(gridPrecision):
            electricFieldArrowsAll[i][j].visible = True
            electricFieldArrowsAll[i][j].pos = vec((i - gridPrecision / 2 + 1/2) * unitWidth,
                                                           (j - gridPrecision / 2 + 1/2) * unitHeight, 0)

# endregion

# region electric potential
potentialGridRows = []
potentialGridCols = []
electricPotentialLabels = None

# create when click start after know precision
def createPotentialGrid():
    global potentialGridRows, potentialGridCols, electricPotentialLabels
    # dimension = gridPrecision
    for i in range(gridPrecision):
        potentialGridRows.append(box(axis=vec(1, 0, 0), color = color.black, visible = False))
        potentialGridCols.append(box(axis=vec(0, 0, 1), color = color.black, visible = False))
    # dimension = (gridPrecions - 1) * (gridPrecions - 1)
    electricPotentialLabels = [ [0]* (gridPrecision - 1) for i in range(gridPrecision - 1)]
    for i in range(gridPrecision-1):
        for j in range(gridPrecision-1):
            electricPotentialLabels[i][j] = label(text = "0", visible = False, box = False)

# method for rescaling
def setElectricPotentialGrid():
    global potentialGridRows, potentialGridCols, electricPotentialLabels
    # determine thickness
    thickness = scene.range / 200
    # grids
    for i in range(gridPrecision):
        # rows
        potentialGridRows[i].size = vec(unitWidth * gridPrecision, thickness, thickness)
        potentialGridRows[i].pos = vec(0, (i - gridPrecision / 2 + 1/2) * unitHeight, 0)

        # cols
        potentialGridCols[i].size = vec(thickness, unitHeight * gridPrecision, thickness)
        potentialGridCols[i].pos = vec((i - gridPrecision / 2 + 1/2) * unitWidth, 0, 0)

    # labels
    for i in range(gridPrecision-1):
        for j in range(gridPrecision-1):
            electricPotentialLabels[i][j].pos = vec((i - gridPrecision / 2 + 1) * unitWidth, 
                                                            (j - gridPrecision / 2 + 1) * unitHeight, 0)
            electricPotentialLabels[i][j].height = 10

# endregion 

# region ruler
ruler = curve({"pos": vector(0, 0, 0), "color": color.cyan},
                      {"pos": vector(0, 0, 0), "color": color.cyan})
rulerLabel = label(text="0", visible = False, color = color.magenta)

def createRulerLabel():
    global ruler, rulerLabel

    # create new ruler label in the middle of the ruler
    rulerLabel.text = "{0:.3f}".format(mag(ruler.point(1)['pos'] - ruler.point(0)['pos'])) + "m"
    rulerLabel.pos = ruler.point(0)['pos'] + (ruler.point(1)['pos'] - ruler.point(0)['pos']) / 2
    rulerLabel.visible = True
         
# store all spawned charges
allChargedObjs = []

#endregion

# region select display
spawnPosIndicator = curve()
for i in range(steps * 8):
    theta = i * 2 * pi / steps 
    radius = scene.range / 75
    spawnPosIndicator.append({"pos": vec(cos(theta) * radius, sin(theta) * radius, 0)
                        , "color": color.yellow})
spawnPosIndicator.visible = False

#endregion

#endregion

####################################################################################################

# region Classes

# region Sphere of Charge
class ChargedObj:       
    def __init__(self, mass, charge, spawnPos, spawnVel):
        # physics variables
        self.charge = charge
        self.mass = mass
        self.pos = spawnPos
        self.vel = spawnVel
        self.fixed = False
        self.collided = []

        # force labels
        self.velLabel = label(text = "0", visible = False)
        self.forceLabel = label(text = "0", visible = False)
        self.impulseLabel = label(text = "0", visible = False)

        # radius
        spawnRadius = ((mass) / (((4/3)* pi*spawnDensity)))**(1/3)

        # possibly sliders for more variables
        self.numOfLine = 8

        # spheres for now
        if (charge > 0):
            # display and vectors
            self.display = sphere(pos = spawnPos, radius = spawnRadius, texture = positiveSphereTexture)
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.red)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.red)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.red)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.red)

            self.trail = attach_trail(self.display, color = color.red)

        elif (charge < 0):
            # display and vectors
            self.display = sphere(pos=spawnPos, radius=spawnRadius, texture = negativeSphereTexture)
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.blue)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.blue)
            
            self.trail = attach_trail(self.display, color = color.blue)
        
        else:
            # display and vectors
            self.display = sphere(pos=spawnPos, radius=spawnRadius, texture = neutralSphereTexture)
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.black)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.black)

            self.trail = attach_trail(self.display, color = color.black)

        self.trail.stop()

        # select display
        self.selectDisplay = []
        self.createSelectDisplay()

    # region select display

    def createSelectDisplay(self):
        # Math with a circle to create arcs
        thetaRange = pi / 4
        for x in range(4):
            arc = curve()
            initialTheta = x * pi / 2 + pi / 4
            for i in range(steps):
                theta = i * thetaRange / steps + initialTheta - thetaRange / 2 
                arc.append({"pos": vec(cos(theta) * (self.display.radius + epsilon * scene.range), 
                                    sin(theta) * (self.display.radius + epsilon * scene.range), 0) + self.pos
                                    , "color": color.yellow})
            
            self.selectDisplay.append(arc)
        for arc in self.selectDisplay:
            arc.visible = False
    
    def displaySelect(self):
        thetaRange = pi / 4
        for x in range(4):
            arc = self.selectDisplay[x]
            initialTheta = x * pi / 2 + pi / 4
            for i in range(steps):
                theta = i * thetaRange / steps + initialTheta - thetaRange / 2 
                arc.modify(i, pos = vec(cos(theta) * (self.display.radius + epsilon * scene.range), 
                                    sin(theta) * (self.display.radius + epsilon * scene.range), 0) + self.pos)
            arc.visible = True
    
    def hideSelect(self):
        for x in range(4):
            arc = self.selectDisplay[x]
            arc.visible = False

    # endregion

    # region force & velocity
    def calculateNetForce(self):
        force = vec(0, 0, 0)
        for chargedObj in allChargedObjs:
            if (chargedObj != self):
                if (mag(self.pos - chargedObj.pos) > 2 * self.display.radius):
                    force += calculateForce(self, chargedObj)
        return force

    def applyForce(self):
        # calculate force from every other charge
        if (not self.fixed):
            # apply force
            self.vel += self.calculateNetForce() / self.mass

    def createForceLabel(self):    
        self.forceLabel.text = "{0:.3f}".format(mag(self.forceVec.axis)) + "μN"
        self.forceLabel.pos = self.forceVec.pos + self.forceVec.axis
        self.forceLabel.visible = True

    def applyVel(self):
        if (not self.fixed):
            self.pos += self.vel / numOfRate
            self.display.pos = self.pos
            if (self == chargedObjSelected):
                self.displaySelect()

    def createVelLabel(self):    
        self.velLabel.text = "{0:.3f}".format(mag(self.velVec.axis)) + "m/s"
        self.velLabel.pos = self.velVec.pos + self.velVec.axis
        self.velLabel.visible = True

    def createImpulseLabel(self):
        self.impulseLabel.text = "{0:.3f}".format(mag(self.impulseVec.axis)) + "μN"
        self.impulseLabel.pos = self.impulseVec.pos + self.impulseVec.axis
        self.impulseLabel.visible = True

    # endregion

    def checkCollision(self):
        for chargedObj in allChargedObjs:
            if (self != chargedObj):
                if (mag(self.pos - chargedObj.pos) <= self.display.radius + chargedObj.display.radius):
                    if (not (chargedObj in self.collided)):
                        # v1 = 2 * m2 / (m1 + m2) * v2 + (m1 - m2) / (m1 + m2) * v1
                        tempvel = (2 * chargedObj.mass / (chargedObj.mass + self.mass) * chargedObj.vel +
                        (self.mass - chargedObj.mass) / (chargedObj.mass + self.mass) * self.vel)

                        # v2 = 2 * m1 / (m1 + m2) * v1 + (m2 - m1) / (m1 + m2) * v2
                        chargedObj.vel = (2 * self.mass / (chargedObj.mass + self.mass) * self.vel +
                        (chargedObj.mass - self.mass) / (chargedObj.mass + self.mass) * chargedObj.vel)

                        self.vel = tempvel

                        # position check
                        dif = self.display.radius + chargedObj.display.radius - mag(self.pos - chargedObj.pos) 
                        tempPos = self.pos + norm(self.pos - chargedObj.pos) * dif / 2
                        chargedObj.pos = chargedObj.pos + norm(chargedObj.pos - self.pos) * dif / 2
                        self.pos = tempPos

                        # prevent collision calculation twice
                        chargedObj.collided.append(self)

    def displayElectricField(self):
        if (self.charge == 0):
            return
        
        if (electricFieldMode == 1):
            # determine size
            size = scene.range / 10
            # for every direction
            for i in range(self.numOfLine):
                # determine starting position
                theta = i * 2 * pi / self.numOfLine
                curPos = self.pos + vec(cos(theta), sin(theta), 0) * self.display.radius
                #for every step
                for j in range(electricFieldPrecision):
                    # don't display if too close to a charge
                    if (tooClose(self, curPos, size)):
                        self.electricFieldArrows[i][j].visible = False
                    else:
                        # determine the arrow 
                        electricField = calculateElectricField(curPos)
                        arrowLength = norm(electricField) * size
                        self.electricFieldArrows[i][j].visible = True
                        self.electricFieldArrows[i][j].pos = curPos
                        if (self.charge < 0):
                            self.electricFieldArrows[i][j].pos -= arrowLength
                        self.electricFieldArrows[i][j].axis = arrowLength

                        # opacity
                        if (electricOpacityMode):
                            self.electricFieldArrows[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
                        else:
                            self.electricFieldArrows[i][j].opacity = 1

                        # next position
                        curPos += arrowLength * self.charge / abs(self.charge)
        else: 
            # hide all electric field arrows
            for i in range(self.numOfLine):   
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j].visible = False

# Coulomb's Law for force of q2 on q1
def calculateForce(q1, q2):
    r12 = q1.pos - q2.pos
    return norm(r12) * K * q1.charge * q2.charge / (mag(r12)**2)

# endregion

# endregion

####################################################################################################

# region Electric Field and Potential

def displayElectricFieldAll():
    # calculate electric field for each arrow
    if (electricFieldMode == 2):
        size = scene.range / 10
        for i in range(gridPrecision):
            for j in range(gridPrecision):
                electricField = calculateElectricField(electricFieldArrowsAll[i][j].pos)
                electricFieldArrowsAll[i][j].axis = norm(electricField) * size
                if (electricOpacityMode):
                    electricFieldArrowsAll[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
                else:
                    electricFieldArrowsAll[i][j].opacity = 1
    
def calculateElectricField(pos):
    electricField = vec(0, 0, 0)
    for chargedObj in allChargedObjs:
        r = pos - chargedObj.pos
        # just check for now before I figure out what to do in this case
        if (mag(r) != 0):
            electricField += norm(r) * K * chargedObj.charge / (mag(r)**2)
    return electricField

def tooClose(owner, pos, size):
    for chargedObj in allChargedObjs:
            if (chargedObj != owner):
                if mag(pos - chargedObj.pos) < chargedObj.display.radius + size:
                    return True
    return False

# Electric Potential

def displayElectricPotential():
    # calculate electric potential for each label
    if (electricPotentialMode == 1):
        for i in range(gridPrecision-1):
            for j in range(gridPrecision-1):
                electricPotentialLabels[i][j].text = '{:1.2f}'.format(calculateElectricPotential(electricPotentialLabels[i][j].pos))

def calculateElectricPotential(pos):
    electricPotential = 0
    for chargedObj in allChargedObjs:
        r = pos - chargedObj.pos
        # just check for now before I figure out what to do in this case
        if (mag(r) != 0):
            electricPotential +=  K * chargedObj.charge / mag(r)
    return electricPotential

# endregion

####################################################################################################

# region User Controls

# Clicks
chargedObjSelected = None
spawnPos = None

def clicked():
    global chargedObjSelected, spawnPos
    # only when not playing
    if (not playing):
        # When no charge is selected
        if (chargedObjSelected == None):
            chargedObjSelected = chargedObjOnMouse()
            # select the charge when the click is on a charged object
            if (chargedObjSelected != None):
                chargedObjSelected.displaySelect()
                spawnPosIndicator.visible = False
                createCaptionSelectCharge()
            # spawn screen when the click is not on a charged object
            else:
                spawnPos = getMousePos()
                createCaptionSpawnScreen()
                displaySpawnPosIndicator(spawnPos)
        else:
            # reselect 
            if (chargedObjSelected != None):
                chargedObjSelected.hideSelect()
            chargedObjSelected = chargedObjOnMouse()

            # select again or deselect
            if (chargedObjSelected != None):
                chargedObjSelected.displaySelect()
                createCaptionSelectCharge()
            else:
                createCaptionMainScreen()

# helper methods
def chargedObjOnMouse():
    mousePos = getMousePos()
    for chargedObj in allChargedObjs:
        if (mag(mousePos - chargedObj.pos) <= chargedObj.display.radius):
            return chargedObj
    return None

def getMousePos():
    return scene.mouse.project(normal=vec(0, 0, 1))

def displaySpawnPosIndicator(pos):
    global spawnPosIndicator
    for i in range(steps * 8):
        theta = i * 2 * pi / steps 
        radius = scene.range / 75
        spawnPosIndicator.modify(i, pos = vec(cos(theta) * radius, sin(theta) * radius, 0) + pos)
    spawnPosIndicator.visible = True

# dragging
chargedObjToDrag = None
mouseDown = False

def onMouseDown():
    global chargedObjToDrag, mouseDown, ruler
    # assign charged object to drag
    chargedObjToDrag = chargedObjOnMouse()
    mouseDown = True

    # initial pos of ruler
    if (chargedObjToDrag == None and not playing):
        ruler.modify(0, getMousePos())
        ruler.modify(1, getMousePos())
        rulerLabel.visible = False

def onMouseUp():
    global chargedObjToDrag, mouseDown
    # apply force vector if necessary
    if (chargedObjSelected != None):
        if (chargedObjSelected.impulseVec.axis != vec(0, 0, 0)):
            chargedObjSelected.vel += chargedObjSelected.impulseVec.axis / forceScaler / chargedObjSelected.mass 
            chargedObjSelected.impulseVec.axis = vec(0, 0, 0)
            chargedObjSelected.impulseLabel.visible = False

    # minimum length check for the ruler
    if (mag(ruler.point(1)['pos'] - ruler.point(0)['pos']) < epsilon * scene.range):
        rulerLabel.visible = False
        ruler.modify(0, vec(0, 0, 0))
        ruler.modify(1, vec(0, 0, 0))
    
    # reset variables
    chargedObjToDrag = None
    mouseDown = False

def onMouseMove():
    global ruler
    # ruler when no object to drag and not playing
    if chargedObjToDrag == None and not playing:
        # avoid mouse move after mouse up
        if (mouseDown):
            ruler.modify(1, getMousePos())
            createRulerLabel()
    else: 
        # when charge selected is not the charge you are draging
        if (chargedObjSelected != chargedObjToDrag):
            # set position
            if (chargedObjToDrag != None):
                mousePos = getMousePos()
                chargedObjToDrag.pos = mousePos
                chargedObjToDrag.display.pos = chargedObjToDrag.pos
                chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
                # create velocity label only if velocity not too small
                if (mag(chargedObjToDrag.velVec.axis) > chargedObjToDrag.display.radius):
                    chargedObjToDrag.createVelLabel()

                # could have impacted electric field and potential in the spawn screen
                if (spawnPos != None):
                    updateSpawnScreen()
        else:
            if chargedObjToDrag != None:
                # velocity vector
                if (not playing):
                    chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
                    chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
                    chargedObjToDrag.createVelLabel()
                    # velocity too small reset
                    if (mag(chargedObjToDrag.velVec.axis) < chargedObjToDrag.display.radius):
                        chargedObjToDrag.velVec.axis = vec(0, 0, 0)
                        chargedObjToDrag.velLabel.visible = False
                    chargedObjToDrag.vel = chargedObjToDrag.velVec.axis
                    updateSelectScreen()

# endregion

####################################################################################################

# region Intro Screen

# Intro text
startText = text(pos = vec(0, -3, 0), text="JackXiang", align='center', color = color.cyan)
startText.height = 10
startText.length = 25

# Start Button
def start():
    scene.userzoom = True
    startText.visible = False

    # initialize the electric field arrows and grids
    setUnits()

    createElectricFieldArrowsAll()
    setElectricFieldArrowsAll()

    createPotentialGrid()
    setElectricPotentialGrid()
    
    createCaptionMainScreen()

    # bind events
    scene.bind('click', clicked)
    scene.bind('mousedown', onMouseDown)
    scene.bind('mouseup', onMouseUp)
    scene.bind('mousemove', onMouseMove)

scene.append_to_caption("   ")
startButton = button(text = "Start without preset", bind = start)
scene.append_to_caption("\n\n   ")

#Dipole
def dipolePreset():
    start()
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(5,0,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(-5, 0, 0) , vec(0, 0, 0)))
    
def threeChargePreset(): 
    start()
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(0,5,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, -1.5E-9, vec(-5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0)))

def butterflyPreset():
    start()
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(0,5,0), vec(1, -1, 0)))
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(5,5,0), vec(-1, -1, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 5E-9, vec(2.5,0,0), vec(0, 1, 0)))

def helixPreset(): 
    start()
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(-1.5,10,0), vec(.25, -2, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(1.5,10,0), vec(-.25, -2, 0)))

def helixGunPreset ():
    start()
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(-15,1.5,0), vec(2, -.25, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(-15,-1.5,0), vec(2, .25, 0)))
    allChargedObjs.append(ChargedObj(1E-6, -1E-9, vec(0,1.5,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(0,-1.5,0), vec(0, 0, 0)))
    
def dragonflyPreset ():
    start()
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(0,5,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(4.33,-2.5,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(-4.33,-2.5,0), vec(0, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, -5E-9, vec(0,0,0), vec(0, 0, 0)))
    
def somethingPreset():
    start()
    allChargedObjs.append(ChargedObj(1E-6, -5E-9, vec(0,5,0), vec(3, 0, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 1E-9, vec(5*cos(30),-5*sin(30),0), vec(-1, 2, 0)))
    allChargedObjs.append(ChargedObj(1E-6, 5E-9, vec(-5*cos(30),-5*sin(30),0), vec(1, 2, 0)))

# Presets
button(text = "Dipole", bind = dipolePreset)
scene.append_to_caption("   ")
button(text = "Three-Charge Motion", bind = threeChargePreset)
scene.append_to_caption("\n\n   ")
button(text = "Parallel Plates", bind = start)
scene.append_to_caption("   ")
button(text = "Faraday Bucket", bind = start)
scene.append_to_caption("\n\n   ")
button(text = "Draw Butterfly", bind = butterflyPreset) 
scene.append_to_caption("   ")
button(text = "Draw Helix", bind = helixPreset) 
scene.append_to_caption("\n\n   ")
button(text = "helix gun (kinda)", bind = helixGunPreset)
scene.append_to_caption("   ")
button(text = "draw dragonfly", bind = dragonflyPreset) 
scene.append_to_caption("\n\n   ")
button(text = "draw something", bind = somethingPreset)

# electric field Slider
electricFieldPrecision = 10

def electricFieldPrecisionShift():
    global electricFieldPrecision, electricFieldPrecisionText
    electricFieldPrecision = electricFieldPrecisionSlider.value
    electricFieldPrecisionText.text = "<center>Electric Field Precision: " + str(electricFieldPrecision) + "</center>"

scene.append_to_caption("\n\n")
electricFieldPrecisionSlider = slider(min = 5, max = 20, value = 10, step = 1, bind = electricFieldPrecisionShift, length = sliderLength)
electricFieldPrecisionText = wtext(text = "<center>Electric Field Precision: 10</center>")

# gridPrecision Slider
gridPrecision = 10

def gridPrecisionShift():
    global gridPrecision, gridPrecisionText
    gridPrecision = gridPrecisionSlider.value
    gridPrecisionText.text = "<center>Grid Precision: " + str(gridPrecision) + "</center>"

scene.append_to_caption("\n")
gridPrecisionSlider = slider(min = 5, max = 20, value = 10, step = 1, bind = gridPrecisionShift, length = sliderLength)
gridPrecisionText = wtext(text = "<center>Grid Precision: 10</center>")

# Instruction
def createInstruction():
    scene.append_to_caption(""" 
Instruction: 

Controls:
    Not Playing:
        Click:
            Charge not selected:
                Empty Space = Spawn Screen
                On a charge = Select Screen
            Charge selected:
                Empty Space = Deselect
        Drag:
            Start on a charge:
                Charge not selected = Position
                Charge selected = Velocity
            Start on empty space = Ruler
    Playing:
        Click & Drag = Force vector for selected charge
""")

createInstruction()

backButton = None

# endregion

####################################################################################################

# region Main Screen Caption

def createCaptionMainScreen():
    scene.caption = ""

    # play button
    global playButton
    scene.append_to_caption("   ")
    if (playing):
        playButton = button(text="Stop", bind = changePlay)
    else:
        playButton = button(text="Play", bind = changePlay)

    # instruction button
    global instructionButton
    scene.append_to_caption("   ")
    instructionButton = button(text="Instructions", bind = displayInstructionPage)

    # save button
    global saveButton
    scene.append_to_caption("   ")
    button (text = "Save", bind = changePlay)

    # time slider
    global timeSlider, timeText
    scene.append_to_caption("\n\n")
    timeSlider = slider(bind=timeShift, min = 0.1, max = 5, value = time, step = 0.1, length = sliderLength) 
    scene.append_to_caption("\n")
    timeText = wtext(text = "<center>Time in program for every second in real life:" + str(time) + "s</center>")
    
    # vector menu
    global vectorMenu
    scene.append_to_caption("\n   Show Vectors: ")
    vectorMenu = menu(choices = ["Velocity", "Force", "Neither"], bind = selectVector, selected = vectorToShow)

    # trail checkbox
    global trailCheckbox
    scene.append_to_caption("   ")
    trailCheckbox = checkbox(text = "Trail", bind = changeTrailStateAll, checked = trailStateAll)

    # clear trail button
    global clearTrailButton
    scene.append_to_caption("   ")
    clearTrailButton = button (text = "Clear All Trail", bind = clearTrailAll)

    # electric field mode button
    global electricFieldButton
    scene.append_to_caption("\n\n   ")
    electricFieldButton = button(text="Electric Field: Mode " + str(electricFieldMode), bind = changeElectricField)

    # electric field opacity checkbox
    global electricOpacityCheckbox
    scene.append_to_caption("   ")
    electricOpacityCheckbox = checkbox(text = "Electric Field Opacity", bind = changeElectricOpacityMode, checked = electricOpacityMode)

    # electric potential mode button
    global electricPotentialButton
    scene.append_to_caption("\n\n   ")
    electricPotentialButton = button(text="Electric Potential Mode " + str(electricPotentialMode), bind = changeElectricPotential)
    
    # grid mode checkbox
    global gridCheckbox
    scene.append_to_caption("   ")  
    gridCheckbox = checkbox(text="Grid", bind = changeGridMode, checked = gridMode)

# play button
playing = False

def changePlay():
    global playing, playButton
    playing = not playing
    if playing:
        playButton.text = "Stop"
    else:
        playButton.text = "Play"

    # for every object that is not fixed
    for co in allChargedObjs:
        if (not co.fixed):
            #set vector visibilities
            if (vectorToShow == "Velocity"):
                if (playing):
                    co.velVec.visible = False
                    co.velLabel.visible = False
                else:
                    co.velVec.visible = True
                    co.velVec.pos = co.pos
                    co.velVec.axis = co.vel
                    co.createVelLabel()
            elif (vectorToShow == "Force"):
                if (playing):
                    co.forceVec.visible = False
                    co.forceLabel.visible = False
                else:
                    co.forceVec.visible = True
                    co.forceVec.pos = co.pos
                    print(co.calculateNetForce())
                    co.forceVec.axis = co.calculateNetForce() * forceScaler
                    co.createForceLabel()

# instruction button
def displayInstructionPage():
    global startButton
    scene.caption = ""
    startButton = button(text = "Back", bind = createCaptionMainScreen)
    scene.append_to_caption("\n")
    createInstruction()

# save button
def save():
    print("!!!")

# time slider
time = 1

def timeShift():
    global time, timeText
    time = timeSlider.value
    timeText.text = "<center>Time in program for every second in real life:" + str(time) + "s</center>"

# vector menu
vectorToShow = "Velocity"

def selectVector():
    global vectorToShow
    vectorToShow = vectorMenu.selected

# trail checkbox
trailStateAll = False

def changeTrailStateAll():
    global trailStateAll, allChargedObjs
    trailStateAll = not trailStateAll
    for co in allChargedObjs:
        if (trailStateAll):
            co.trail.start()
        else:
            co.trail.stop()

# clear trail button
def clearTrailAll():
    for co in allChargedObjs:
        co.trail.clear()

# electic field mode button
electricFieldMode = 0

def changeElectricField():
    global electricFieldMode, electricFieldButton, electricFieldArrowsAll
    electricFieldMode += 1
    if electricFieldMode == 3:
        electricFieldMode = 0
    
    # set visibility
    if (electricFieldMode == 2):
        for i in range(gridPrecision):
            for j in range(gridPrecision):
                electricFieldArrowsAll[i][j].visible = True
    else:
        for i in range(gridPrecision):
            for j in range(gridPrecision):
                electricFieldArrowsAll[i][j].visible = False

    electricFieldButton.text = "Electric Field: Mode " + str(electricFieldMode)

# electric field opacity checkbox
electricOpacityMode = False

def changeElectricOpacityMode():
    global electricOpacityMode
    electricOpacityMode = not electricOpacityMode

# electric potential mode button
electricPotentialMode = 0

def changeElectricPotential():
    global electricPotentialMode, electricPotentialButton
    electricPotentialMode = electricPotentialMode + 1
    if (electricPotentialMode == 2):
        electricPotentialMode = 0
    # set visibility 
    if (electricPotentialMode == 1):
        for i in range(gridPrecision-1):
            for j in range(gridPrecision-1):
                electricPotentialLabels[i][j].visible = True
    else: 
        for i in range(gridPrecision-1):
            for j in range(gridPrecision-1):
                electricPotentialLabels[i][j].visible = False
        
    electricPotentialButton.text = "Electric Potential Mode " + str(electricPotentialMode)

# grid mode checkbox
gridMode = False

def changeGridMode():
    global gridMode
    gridMode = not gridMode
    if (gridMode):
        for i in range(gridPrecision):
            potentialGridRows[i].visible = True
            potentialGridCols[i].visible = True
    else:
        for i in range(gridPrecision):
            potentialGridRows[i].visible = False
            potentialGridCols[i].visible = False

# endregion

####################################################################################################

# region Spawn Screen Caption

def createCaptionSpawnScreen():
    scene.caption = ""

    # spawn charge menu
    global chargeMenu
    scene.append_to_caption("   Spawn Charge Object Menu: ")
    chargeMenu = menu(choices = ["Sphere", "Cyllinder", "Plate"], bind = selectSpawnChargeObj) 
    
    # spawn charge slider and input field
    global spawnChargeSlider, spawnChargeInputField
    scene.append_to_caption("\n\n")
    spawnChargeSlider = slider(bind = spawnChargeShift, min = -5, max = 5, value = spawnCharge / 1E-9, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n                             Charge: ")
    spawnChargeInputField = winput(bind = spawnChargeInput, text = spawnChargeSlider.value, width = 35)
    scene.append_to_caption(" nC")

    # spawn mass slider and input field
    global spawnMassSlider, spawnMassInputField
    scene.append_to_caption("\n\n")
    spawnMassSlider = slider(bind = spawnMassShift, min = 1, max = 5, value = spawnMass / 1E-6, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n                          Mass: ")
    spawnMassInputField = winput(bind = spawnMassInput, text = spawnMassSlider.value, width = 35)
    scene.append_to_caption(" * 10^-6 Kg")

    # spawn and back buttons
    global spawnButton, backButton
    scene.append_to_caption("\n\n   ")
    spawnButton = button(text = "Spawn", bind = spawnChargedObj)
    scene.append_to_caption("   ")
    backButton = button(text = "Back", bind = back)

    # spawn position input fields
    global spawnPosText, spawnXInputField, spawnYInputField
    scene.append_to_caption("\n\n   Position: <")
    spawnXInputField = winput(bind = spawnXInput, text = '{:1.2f}'.format(spawnPos.x), width = 50)
    scene.append_to_caption(", ")
    spawnYInputField = winput(bind = spawnYInput, text = '{:1.2f}'.format(spawnPos.y), width = 50) 
    scene.append_to_caption(">")

    # electric field and potential texts
    global electricFieldText, electricPotentialText
    scene.append_to_caption("\n\n   ")
    electricField = calculateElectricField(spawnPos)
    electricFieldText = wtext(text = "Electric Field: <" + 
                                        '{:1.2f}'.format(electricField.x) + ", " + 
                                        '{:1.2f}'.format(electricField.y) + "> N/C \n   Electric Field: "+
                                        '{:1.2f}'.format((mag(electricField))) + " N/C @ " +
                                        '{:1.2f}'.format(atan2(electricField.y, electricField.x) / pi * 180) + " degree")

    scene.append_to_caption("\n\n   ")
    electricPotentialText = wtext(text = "Electric Potential: " '{:1.2f}'.format(calculateElectricPotential(spawnPos)) + " V")

# spawn charge menu
def selectSpawnChargeObj():
    print("!!!")

# spawn charge slider and input field
spawnCharge = 1E-9

def spawnChargeShift():
    global spawnCharge, spawnChargeInputField
    spawnCharge = spawnChargeSlider.value * 1E-9
    spawnChargeInputField.text = spawnChargeSlider.value

def spawnChargeInput():
    global spawnCharge, spawnChargeSlider, spawnChargeInputField
    if (spawnChargeInputField.number != None):
        # min max
        num = max(spawnChargeSlider.min, spawnChargeInputField.number)
        num = min(spawnChargeSlider.max, num)
        # set values
        spawnCharge = num * 1E-9
        spawnChargeSlider.value = num
        spawnChargeInputField.text = num
    else:
        spawnChargeInputField.text = spawnCharge / 1E-9

# spawn mass slider and input field
spawnMass = 1E-6

def spawnMassShift():
    global spawnMass, spawnMassInputField
    spawnMass = spawnMassSlider.value * 1E-6
    spawnMassInputField.text = spawnMassSlider.value

def spawnMassInput():
    global spawnMass, spawnMassSlider, spawnMassInputField
    if (spawnMassInputField.number != None):
        # min max
        num = max(spawnMassSlider.min, spawnMassInputField.number)
        num = min(spawnMassSlider.max, num)
        # set values
        spawnMass = num * 1E-6
        spawnMassSlider.value = num
        spawnMassInputField.text = num
    else:
        spawnMassInputField.text = spawnMass / 1E-6

# spawn button
def spawnChargedObj():
    allChargedObjs.append(ChargedObj(spawnMass, spawnCharge, spawnPos, vec(0, 0, 0)))
    back()

# back button
def back():
    global spawnPos
    createCaptionMainScreen()
    spawnPosIndicator.visible = False
    spawnPos = None

# spawn position input fields
def spawnXInput():
    global spawnPos, spawnPosIndicator
    # change the x value of spawn position
    if (spawnXInputField.number != None):
        spawnPos.x = spawnXInputField.number
        updateSpawnScreen()
        displaySpawnPosIndicator(spawnPos)  

def spawnYInput():
    global spawnPos, spawnPosIndicator
    # change the y value of spawn position
    if (spawnYInputField.number != None):
        spawnPos.y = spawnYInputField.number
        updateSpawnScreen()
        displaySpawnPosIndicator(spawnPos)

# electric field and potential texts
def updateSpawnScreen():
    global electricFieldText, electricPotentialText
    # recalculate electric field and potential
    electricField = calculateElectricField(spawnPos)
    electricFieldText.text = ("Electric Field: <" + 
                                        '{:1.2f}'.format(electricField.x) + ", " + 
                                        '{:1.2f}'.format(electricField.y) + "> N/C \n   Electric Field: "+
                                        '{:1.2f}'.format((mag(electricField))) + " N/C @ " +
                                        '{:1.2f}'.format(atan2(electricField.y, electricField.x) / pi * 180) + " degree")
    electricPotentialText.text = "Electric Potential: " '{:1.2f}'.format(calculateElectricPotential(spawnPos)) + " V"

# endregion

####################################################################################################

# region Select Charge Screen Caption

def createCaptionSelectCharge():
    global playButton, deleteButton, fixButton
    global selectedChargeVelXYText, selectedChargeVelMAText
    global selectedChargeForceXYText, selectedChargeForceMAText

    global selectedChargeSlider, selectedChargeText
    global selectedMassSlider, selectedMassText

    scene.caption = ""

    global playButton
    scene.append_to_caption("   ")
    if (playing):
        playButton = button(text="Stop", bind = changePlay)
    else:
        playButton = button(text="Play", bind = changePlay)

    global cameraFollowButton
    scene.append_to_caption("   ")
    if (cameraFollowedObj == chargedObjSelected.display):
        cameraFollowButton = button(text = "Camera Unfollow", bind = cameraFollow)
    else:
        cameraFollowButton = button(text = "Camera Follow", bind = cameraFollow)

    scene.append_to_caption("\n\n")
    selectedChargeSlider = slider(bind = selectedChargeShift, min = -5, max = 5, value = chargedObjSelected.charge / 1E-9, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n")
    selectedChargeText = wtext(text = '<center>Charge: '+'{:1.2f}'.format(selectedChargeSlider.value) + " nC </center>")

    scene.append_to_caption("\n")
    selectedMassSlider = slider(bind = selectedMassShift, min = 1, max = 2, value = chargedObjSelected.mass / 1E-6, step = 0.1, length = sliderLength) 
    scene.append_to_caption("\n")
    selectedMassText = wtext(text = '<center>Mass: '+'{:1.2f}'.format(selectedMassSlider.value) + " * 10^-6 Kg</center>")

    scene.append_to_caption("\n   ")
    button(text="Show Velocity: True", bind=fixChargedObj)

    scene.append_to_caption("\n\n   ")
    button(text="Show Force: False", bind=deleteChargedObj)

    scene.append_to_caption("\n\n   ")
    fixButton = button(text="Fix", bind=fixChargedObj)

    scene.append_to_caption("\n\n   ")
    deleteButton = button(text="Delete", bind=deleteChargedObj)

    scene.append_to_caption("\n\n   ")
    wtext(text = "Position: <" + '{:1.2f}'.format(chargedObjSelected.pos.x) + ", " + '{:1.2f}'.format(chargedObjSelected.pos.y) + ">")
    scene.append_to_caption("\n   x:")
    winput(bind = spawnXInput)
    scene.append_to_caption("\n   y:")
    winput(bind = spawnYInput) 

    scene.append_to_caption("\n\n   ")
    selectedChargeVelXYText = wtext(text = "Velocity: <" + 
                    '{:1.2f}'.format(chargedObjSelected.vel.x) + ", " + 
                    '{:1.2f}'.format(chargedObjSelected.vel.y) + "> m/s")
    scene.append_to_caption("\n   x:")
    winput(bind = spawnXInput)
    scene.append_to_caption("\n   y:")
    winput(bind = spawnYInput) 

    scene.append_to_caption("\n\n   ")
    selectedChargeVelMAText = wtext(text = "Velocity: "+
                    '{:1.2f}'.format((mag(chargedObjSelected.vel))) + " m/s @ " +
                    '{:1.2f}'.format(atan2(chargedObjSelected.vel.y, chargedObjSelected.vel.x) / pi * 180) + " degree")
    scene.append_to_caption("\n   mag:")
    winput(bind = spawnXInput)
    scene.append_to_caption("\n   angle:")
    winput(bind = spawnYInput) 

    force = chargedObjSelected.calculateNetForce() / 1E-9
    scene.append_to_caption("\n\n   ")
    selectedChargeForceXYText = wtext(text = "Force: <" + 
                    '{:1.5f}'.format(force.x) + ", " + 
                    '{:1.5f}'.format(force.y) + "> nN") 
    scene.append_to_caption("\n   x:")
    winput(bind = spawnXInput)
    scene.append_to_caption("\n   y:")
    winput(bind = spawnYInput) 

    scene.append_to_caption("\n\n   ")
    selectedChargeForceMAText= wtext(text = "Force: "+
                    '{:1.5f}'.format((mag(force))) + " nN @ " +
                    '{:1.2f}'.format(atan2(force.y, force.x) / pi * 180) + " degree")
    scene.append_to_caption("\n   mag:")
    winput(bind = spawnXInput)
    scene.append_to_caption("\n   angle:")
    winput(bind = spawnYInput) 

# stats
selectedChargeVelXYText = None
selectedChargeVelMAText = None
selectedChargeForceXYText = None
selectedChargeForceMAText = None

def updateSelectScreen():
    global selectedChargeVelXYText, selectedChargeVelMAText, selectedChargeForceXYText, selectedChargeForceMAText
    selectedChargeVelXYText.text = ("Velocity: <" + 
                    '{:1.2f}'.format(chargedObjSelected.vel.x) + ", " + 
                    '{:1.2f}'.format(chargedObjSelected.vel.y) + "> m/s")
    selectedChargeVelMAText.text = ("Velocity: "+
                    '{:1.2f}'.format((mag(chargedObjSelected.vel))) + " m/s @ " +
                    '{:1.2f}'.format(atan2(chargedObjSelected.vel.y, chargedObjSelected.vel.x) / pi * 180) + " degree")
    force = chargedObjSelected.calculateNetForce() / 1E-9

    selectedChargeForceXYText.text = ("Force: <" + 
                    '{:1.5f}'.format(force.x) + ", " + 
                    '{:1.5f}'.format(force.y) + "> nN") 
    selectedChargeForceMAText.text = ("Force: "+
                    '{:1.5f}'.format((mag(force))) + " nN @ " +
                    '{:1.2f}'.format(atan2(force.y, force.x) / pi * 180) + " degree")

# camera follow button
cameraFollowedObj = None

def cameraFollow():
    global cameraFollowButton, cameraFollowedObj
    # unfollow
    if (cameraFollowedObj == chargedObjSelected.display):
        scene.camera.follow(None)
        cameraFollowedObj = None
        cameraFollowButton.text = "Camera Follow"
    # follow
    else:
        scene.camera.follow(chargedObjSelected.display)
        cameraFollowedObj = chargedObjSelected.display
        cameraFollowButton.text = "Camera Unfollow"

cameraFollowButton = None

# select charge slider
def selectedChargeShift(): 
    global chargedObjSelected, selectedChargeSlider, selectedChargeText
    chargedObjSelected.charge = selectedChargeSlider.value * 1E-9      
    selectedChargeText.text = '<center>Charge: '+'{:1.2f}'.format(selectedChargeSlider.value) + " nC </center>"
    # change the texture
    if (chargedObjSelected.charge > 0):
        if (chargedObjSelected.fixed):
            chargedObjSelected.display.texture = fixedPositiveSphereTexture
        else:
            chargedObjSelected.display.texture = positiveSphereTexture
    elif (chargedObjSelected.charge < 0): 
        if (chargedObjSelected.fixed):
            chargedObjSelected.display.texture = fixedNegativeSphereTexture
        else:
            chargedObjSelected.display.texture = negativeSphereTexture
    else:
        if (chargedObjSelected.fixed):
            chargedObjSelected.display.texture = fixedNeutralSphereTexture
        else:
            chargedObjSelected.display.texture = neutralSphereTexture

    # colors
    if (chargedObjSelected.charge > 0):
        curColor = color.red
    elif (chargedObjSelected.charge < 0):
        curColor = color.blue
    else:
        curColor = color.black

    chargedObjSelected.velVec.color = curColor
    chargedObjSelected.impulseVec.color = curColor

    for i in range(chargedObjSelected.numOfLine):
        for j in range(electricFieldPrecision):
            chargedObjSelected.electricFieldArrows[i][j].color = curColor

    chargedObjSelected.trail.color = curColor

selectedChargeSlider = None
selectedChargeText = None

# select mass slider
def selectedMassShift(): 
    global chargedObjSelected, selectedMassSlider, selectedMassText
    chargedObjSelected.mass = selectedMassSlider.value * 1E-6   
    selectedMassText.text = '<center>Mass: '+'{:1.2f}'.format(selectedMassSlider.value) + " * 10^-6 Kg</center>"
    # change radius
    chargedObjSelected.display.radius = ((chargedObjSelected.mass) / (((4/3)* pi*spawnDensity)))**(1/3)
    chargedObjSelected.displaySelect()

selectedMassSlider = None
selectedMassText = None

# delete button
def deleteChargedObj():
    global chargedObjSelected

    # hide everything, remove from list, reset chargedObjSelected
    chargedObjSelected.display.visible = False
    chargedObjSelected.velVec.visible = False
    chargedObjSelected.impulseVec.visible = False
    chargedObjSelected.velLabel.visible = False
    chargedObjSelected.impulseLabel.visible = False
    chargedObjSelected.hideSelect()
    for i in range(chargedObjSelected.numOfLine):   
            for j in range(electricFieldPrecision):
                chargedObjSelected.electricFieldArrows[i][j].visible = False
    allChargedObjs.remove(chargedObjSelected)
    if (chargedObjSelected == cameraFollowedObj):
        scene.camera.follow(None)
        cameraFollowedObj = None
    chargedObjSelected = None
    createCaptionMainScreen()

deleteButton = None

# fix button
def fixChargedObj():
    global chargedObjSelected
    chargedObjSelected.fixed = not chargedObjSelected.fixed

    # text
    if (chargedObjSelected.fixed):
        fixButton.text = "Unfix"
    else:
        fixButton.text = "Fix"

    # texture
    if (chargedObjSelected.fixed): 
        if chargedObjSelected.charge > 0:
            chargedObjSelected.display.texture = fixedPositiveSphereTexture
        elif chargedObjSelected.charge < 0:
            chargedObjSelected.display.texture = fixedNegativeSphereTexture
        else: 
            chargedObjSelected.display.texture = fixedNeutralSphereTexture
    else:
        if chargedObjSelected.charge > 0:
            chargedObjSelected.display.texture = positiveSphereTexture 
        elif chargedObjSelected.charge < 0:
            chargedObjSelected.display.texture = negativeSphereTexture
        else: 
            chargedObjSelected.display.texture = neutralSphereTexture

fixButton = None

# endregion 

####################################################################################################

# region Program Runs Here
curRange = scene.range

while True:
    rate(numOfRate * time)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    for chargedObj in allChargedObjs:
        chargedObj.displayElectricField()

    # reset electric field arrows and electric potential grid for all if user zooms
    if (curRange != scene.range):
        curRange = scene.range
        setUnits()
        setElectricFieldArrowsAll()
        setElectricPotentialGrid()

    displayElectricFieldAll()
    displayElectricPotential()

    # collision
    for charge in allChargedObjs:
        charge.checkCollision()
    for charge in allChargedObjs:
        charge.collided = []

    # update force vector because it is possible that mouse is not moving
    if (playing and mouseDown and chargedObjSelected != None):
        chargedObjSelected.impulseVec.pos = chargedObjSelected.pos
        chargedObjSelected.impulseVec.axis = getMousePos() - chargedObjSelected.pos 
        chargedObjSelected.createImpulseLabel()

# endregion
