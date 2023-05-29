import vpython

# set scene
vpython.scene.background = vpython.color.white
vpython.scene.width = 1000
vpython.scene.height = 650
vpython.scene.range = 10
vpython.scene.userzoom = False
vpython.scene.userspin = False
vpython.scene.fov = vpython.pi / 50
vpython.scene.align = "left"

#constants
K = 9E9
spawnDensity = 2.5E-6
steps = 10
epsilon = 0.01
numOfRate = 1000
sliderLength = 450

# electric field stuff
electricFieldOpacitySetter = 1
precision = 10

forceScaler = 1E6

# Test place

####################################################################################################

# region Initilization

# region electric field for mode 2
electricFieldArrowsAll = [ [0]*precision for i in range(precision)]
for i in range(precision):
    for j in range(precision):
        electricFieldArrowsAll[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.orange)

# Math for rescaling
# unit width = 2 * vpython.scene.width / vpython.scene.height * vpython.scene.range / precision
# unit height = 2 * vpython.scene.range / precision

# method for rescaling
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

# endregion

# region electric potential
potentialGridRows = []
potentialGridCols = []

for i in range(precision):
    potentialGridRows.append(vpython.box(axis=vpython.vec(1, 0, 0), color = vpython.color.black, visible = False))
    potentialGridCols.append(vpython.box(axis=vpython.vec(0, 0, 1), color = vpython.color.black, visible = False))

electricPotentialLabels = [ [0]* (precision - 1) for i in range(precision - 1)]
for i in range(precision-1):
    for j in range(precision-1):
        electricPotentialLabels[i][j] = vpython.label(text = "0", visible = False, box = False)

# method for rescaling
def setElectricPotentialGrid():
    # determine thickness
    thickness = vpython.scene.range / 200
    for i in range(precision):
        # rows
        potentialGridRows[i].size = vpython.vec(2 * vpython.scene.width / vpython.scene.height * vpython.scene.range,
                                                           thickness, thickness)
        potentialGridRows[i].pos = vpython.vec(0, (i - precision / 2) * 2 * vpython.scene.range / precision, 0)
        potentialGridRows[i].pos += vpython.vec(0, vpython.scene.range / precision, 0)

        # cols
        potentialGridCols[i].size = vpython.vec(thickness, 2 * vpython.scene.range, thickness)
        potentialGridCols[i].pos = vpython.vec((i - precision / 2) * 2 * 
                                               vpython.scene.width / vpython.scene.height * vpython.scene.range / precision, 0, 0)
        potentialGridCols[i].pos += vpython.vec(vpython.scene.width / vpython.scene.height * vpython.scene.range / precision, 0, 0)

    # labels
    for i in range(precision-1):
        for j in range(precision-1):
            # assume height > width
            electricPotentialLabels[i][j].pos = vpython.vec(
                        (i - precision / 2 + 1) * 2 * vpython.scene.width / vpython.scene.height * vpython.scene.range / precision, 
                        (j - precision / 2 + 1) * 2 * vpython.scene.range / precision, 0)
            electricPotentialLabels[i][j].height = 10

setElectricPotentialGrid()

# endregion 

# region ruler
ruler = vpython.curve({"pos": vpython.vector(0, 0, 0), "color": vpython.color.cyan},
                      {"pos": vpython.vector(0, 0, 0), "color": vpython.color.cyan})
rulerLabel = vpython.label(text="0", visible = False, color = vpython.color.magenta)

def createRulerLabel():
    global ruler, rulerLabel

    # create new ruler label in the middle of the ruler
    rulerLabel.text = "{0:.3f}".format(vpython.mag(ruler.point(1)['pos'] - ruler.point(0)['pos'])) + "m"
    rulerLabel.pos = ruler.point(0)['pos'] + (ruler.point(1)['pos'] - ruler.point(0)['pos']) / 2
    rulerLabel.visible = True
         
# store all spawned charges
allChargedObjs = []

#endregion

# region select display
spawnPosIndicator = vpython.curve()
for i in range(steps * 8):
    theta = i * 2 * vpython.pi / steps 
    radius = vpython.scene.range / 50
    spawnPosIndicator.append({"pos": vpython.vec(vpython.cos(theta) * radius, vpython.sin(theta) * radius, 0)
                        , "color": vpython.color.yellow})
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
        self.velLabel = vpython.label(text="0", visible = False)
        self.forceLabel = vpython.label(text="0", visible = False)
        # Displays
        spawnRadius = ((mass) / (((4/3)* vpython.pi*spawnDensity)))**(1/3)

        # spheres for now
        if (charge > 0):
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, texture = "https://i.imgur.com/Id1Q11U.png")
            self.velVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.red)
            self.forceVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.red)

            # electric field
            # possibly sliders for more variables
            self.numOfLine = 8
            # initialize all the arrows
            self.electricFieldArrows = [ [0]*precision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(precision):
                    self.electricFieldArrows[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.red)
        elif (charge < 0):
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, texture="https://i.imgur.com/r6loarb.png")
            self.velVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.blue)
            self.forceVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.blue)

            # electric field
            # possibly sliders for more variables
            self.numOfLine = 8
            # initialize all the arrows
            self.electricFieldArrows = [ [0]*precision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(precision):
                    self.electricFieldArrows[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.blue)
        else:
            self.display = vpython.sphere(pos=spawnPos, radius=spawnRadius, color = vpython.color.black)
            self.velVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.black)
            self.forceVec = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.black)

            # electric field
            # possibly sliders for more variables
            self.numOfLine = 8
            # initialize all the arrows
            self.electricFieldArrows = [ [0]*precision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(precision):
                    self.electricFieldArrows[i][j] = vpython.arrow(axis = vpython.vec(0, 0, 0), color = vpython.color.black)
        
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
                arc.append({"pos": vpython.vec(vpython.cos(theta) * (self.display.radius + epsilon * vpython.scene.range), 
                                    vpython.sin(theta) * (self.display.radius + epsilon * vpython.scene.range), 0) + self.pos
                                    , "color": vpython.color.yellow})
            
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
                arc.modify(i, pos = vpython.vec(vpython.cos(theta) * (self.display.radius + epsilon * vpython.scene.range), 
                                    vpython.sin(theta) * (self.display.radius + epsilon * vpython.scene.range), 0) + self.pos)
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
            self.pos += self.vel / numOfRate
            self.display.pos = self.pos
            if (self == chargedObjSelected):
                self.displaySelect()

    def createVelLabel(self):    
        self.velLabel.text = "{0:.3f}".format(vpython.mag(self.velVec.axis)) + "m/s"
        self.velLabel.pos = self.velVec.pos + self.velVec.axis
        self.velLabel.visible = True

    def createForceLabel(self):
        self.forceLabel.text = "{0:.3f}".format(vpython.mag(self.forceVec.axis)) + "μN"
        self.forceLabel.pos = self.forceVec.pos + self.forceVec.axis
        self.forceLabel.visible = True

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
                #for every step
                for j in range(precision):
                    # don't display if too close to a charge
                    if (tooClose(self, curPos, size)):
                        self.electricFieldArrows[i][j].visible = False
                    else:
                        # determine the arrow 
                        electricField = calculateElectricField(curPos)
                        arrowLength = vpython.norm(electricField) * size
                        self.electricFieldArrows[i][j].visible = True
                        self.electricFieldArrows[i][j].pos = curPos
                        if (self.charge < 0):
                            self.electricFieldArrows[i][j].pos -= arrowLength
                        self.electricFieldArrows[i][j].axis = arrowLength

                        # opacity
                        if (electricOpacity):
                            self.electricFieldArrows[i][j].opacity = vpython.mag(electricField) / electricFieldOpacitySetter
                        else:
                            self.electricFieldArrows[i][j].opacity = 1

                        # next position
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

# endregion

# endregion

####################################################################################################

# region Electric Field and Potential

def displayElectricFieldAll():
    # calculate electric field for each arrow
    if (electricFieldMode == 2):
        size = vpython.scene.range / 10
        for i in range(precision):
            for j in range(precision):
                electricField = calculateElectricField(electricFieldArrowsAll[i][j].pos)
                electricFieldArrowsAll[i][j].axis = vpython.norm(electricField) * size
                if (electricOpacity):
                    electricFieldArrowsAll[i][j].opacity = vpython.mag(electricField) / electricFieldOpacitySetter
                else:
                    electricFieldArrowsAll[i][j].opacity = 1
    
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

# Electric Potential

def displayElectricPotential():
    # calculate electric potential for each label
    if (electricPotentialMode):
        for i in range(precision-1):
            for j in range(precision-1):
                electricPotentialLabels[i][j].text = '{:1.2f}'.format(calculateElectricPotential(electricPotentialLabels[i][j].pos))

def calculateElectricPotential(pos):
    electricPotential = 0
    for chargedObj in allChargedObjs:
        r = pos - chargedObj.pos
        # just check for now before I figure out what to do in this case
        if (vpython.mag(r) != 0):
            electricPotential +=  K * chargedObj.charge / vpython.mag(r)
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
        if (vpython.mag(mousePos - chargedObj.pos) <= chargedObj.display.radius):
            return chargedObj
        
def getMousePos():
    return vpython.scene.mouse.project(normal=vpython.vec(0, 0, 1))

def displaySpawnPosIndicator(pos):
    global spawnPosIndicator
    for i in range(steps * 8):
        theta = i * 2 * vpython.pi / steps 
        radius = vpython.scene.range / 50
        spawnPosIndicator.modify(i, pos = vpython.vec(vpython.cos(theta) * radius, vpython.sin(theta) * radius, 0) + pos)
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
        if (chargedObjSelected.forceVec.axis != vpython.vec(0, 0, 0)):
            chargedObjSelected.vel += chargedObjSelected.forceVec.axis / forceScaler / chargedObjSelected.mass 
            chargedObjSelected.forceVec.axis = vpython.vec(0, 0, 0)
            chargedObjSelected.forceLabel.visible = False

    # minimum length check for the ruler
    if (vpython.mag(ruler.point(1)['pos'] - ruler.point(0)['pos']) < epsilon * vpython.scene.range):
        rulerLabel.visible = False
        ruler.modify(0, vpython.vec(0, 0, 0))
        ruler.modify(1, vpython.vec(0, 0, 0))
    
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
                if (vpython.mag(chargedObjToDrag.velVec.axis) > chargedObjToDrag.display.radius):
                    chargedObjToDrag.createVelLabel()
        else:
            if chargedObjToDrag != None:
                # velocity vector
                if (not playing):
                    chargedObjToDrag.velVec.pos = chargedObjToDrag.pos
                    chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
                    chargedObjToDrag.createVelLabel()
                    # velocity too small reset
                    if (vpython.mag(chargedObjToDrag.velVec.axis) < chargedObjToDrag.display.radius):
                        chargedObjToDrag.velVec.axis = vpython.vec(0, 0, 0)
                        chargedObjToDrag.velLabel.visible = False
                    chargedObjToDrag.vel = chargedObjToDrag.velVec.axis

# endregion

####################################################################################################

# region Intro Screen

# Intro text
startText = vpython.text(pos = vpython.vec(0, -3, 0), text="JackXiang", align='center', color = vpython.color.cyan)
startText.height = 10
startText.length = 25

# Start Button
def start():
    vpython.scene.userzoom = True
    startText.visible = False
    createCaptionMainScreen()

    # bind events
    vpython.scene.bind('click', clicked)
    vpython.scene.bind('mousedown', onMouseDown)
    vpython.scene.bind('mouseup', onMouseUp)
    vpython.scene.bind('mousemove', onMouseMove)

vpython.scene.append_to_caption("   ")
startButton = vpython.button(text = "Start without preset", bind = start)
vpython.scene.append_to_caption("\n\n   ")

# Presets
vpython.button(text = "Dipole", bind = start)
vpython.scene.append_to_caption("   ")
vpython.button(text = "Three-Charge Motion", bind = start)
vpython.scene.append_to_caption("\n\n   ")
vpython.button(text = "Parallel Plates", bind = start)
vpython.scene.append_to_caption("   ")
vpython.button(text = "Faraday Bucket", bind = start)

# Precision Slider
def precisionShift():
    global precision
    precision = precisionSlider.value

vpython.scene.append_to_caption("\n\n")
precisionSlider = vpython.slider(min = 5, max = 20, value = 10, bind = precisionShift, length = sliderLength)
precisionText = vpython.wtext(text = "<center>Precision: 10</center>")

# Instruction
def createInstruction():
    vpython.scene.append_to_caption(""" 
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

# endregion

####################################################################################################

# region Main Screen Caption

def createCaptionMainScreen():
    global playing, playButton, time, timeSlider, timeText
    global electricFieldMode, electricFieldButton, electricOpacity, electricOpacityButton, electricPotentialMode, electricPotentialButton
    global instructionButton, resetButton

    vpython.scene.caption = ""

    playing = False
    vpython.scene.append_to_caption("   ")
    playButton = vpython.button(text="Play", bind=changePlay)

    vpython.scene.append_to_caption("   ")
    vpython.button (text = "Collision: True", bind = changePlay)

    vpython.scene.append_to_caption("   ")
    vpython.button (text = "Trail: False", bind = changePlay)

    vpython.scene.append_to_caption("   ")
    vpython.button (text = "Save", bind = changePlay)

    time = 1
    vpython.scene.append_to_caption("\n\n")
    timeSlider = vpython.slider(bind=timeShift, min = 0.1, max = 5, value = 1, step = 0.1, length = sliderLength) 
    vpython.scene.append_to_caption("\n")
    timeText = vpython.wtext(text = '<center>Time in program for every second in real life: 1s</center>')

    vpython.scene.append_to_caption("\n\n   ")
    vpython.button(text="Show Velocity: True", bind=fixChargedObj)

    vpython.scene.append_to_caption("   ")
    vpython.button(text="Show Force: False", bind=deleteChargedObj)

    electricFieldMode = 0
    vpython.scene.append_to_caption("\n\n   ")
    electricFieldButton = vpython.button(text="Electric Field: Mode 0", bind=changeElectricField)

    electricOpacity = False
    vpython.scene.append_to_caption("   ")
    electricOpacityButton = vpython.button(text = "Electric Field Opacity: Off", bind=chanageElectricOpacityMode)

    electricPotentialMode = False
    vpython.scene.append_to_caption("\n\n   ")
    electricPotentialButton = vpython.button(text="Electric Potential: False", bind=changeElectricPotential)
    
    vpython.scene.append_to_caption("   ")  
    vpython.button(text="Grid: Off", bind=changeElectricPotential)

    vpython.scene.append_to_caption("\n\n   ")
    instructionButton = vpython.button(text="Instructions", bind=displayInstructionPage)

    vpython.scene.append_to_caption("   ")
    resetButton = vpython.button(text="Reset", bind=resetScene)  

# time slider
time = 1

def timeShift():
    global timeSlider, timeText

timeSlider = None
timeText = None

# electic field mode button
electricFieldMode = 0

def changeElectricField():
    global electricFieldMode, electricFieldButton, electricFieldArrowsAll
    electricFieldMode += 1
    if electricFieldMode == 3:
        electricFieldMode = 0
    
    # set visibility
    if (electricFieldMode == 2):
        for i in range(precision):
            for j in range(precision):
                electricFieldArrowsAll[i][j].visible = True
    else:
        for i in range(precision):
            for j in range(precision):
                electricFieldArrowsAll[i][j].visible = False

    electricFieldButton.text = "Electric Field: Mode " + str(electricFieldMode)

electricFieldButton = None

# electric field opacity button
electricOpacity = False

def chanageElectricOpacityMode():
    global electricOpacity, electricFieldButton
    electricOpacity = not electricOpacity
    if (electricOpacity):
        electricOpacityButton.text = "Electric Field Opacity: On"
    else:
        electricOpacityButton.text = "Electric Field Opacity: Off"

electricOpacityButton = None

# electric potential grid button
electricPotentialMode = False

def changeElectricPotential():
    global electricPotentialMode, electricPotentialButton
    electricPotentialMode = not electricPotentialMode
    # set visibility 
    if (electricPotentialMode):
        for i in range(precision-1):
            for j in range(precision-1):
                electricPotentialLabels[i][j].visible = True
        for i in range(precision):
            potentialGridRows[i].visible = True
            potentialGridCols[i].visible = True
    else: 
        for i in range(precision-1):
            for j in range(precision-1):
                electricPotentialLabels[i][j].visible = False
        for i in range(precision):
            potentialGridRows[i].visible = False
            potentialGridCols[i].visible = False
        
    electricPotentialButton.text = "Electric Potential: " + str(electricPotentialMode)

electricPotentialButton = None

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
            co.velLabel.visible = False
    else:
        for co in allChargedObjs:
            co.velVec.visible = True
            co.velVec.pos = co.pos
            co.velVec.axis = co.vel
            co.createVelLabel()

playButton = None

# instruction and back buttons
def displayInstructionPage():
    global startButton
    vpython.scene.caption = ""
    startButton = vpython.button(text = "Back", bind = createCaptionMainScreen)
    vpython.scene.append_to_caption("\n")
    createInstruction()

instructionButton = None
backButton = None

# reset button
def resetScene():
    global chargedObjSelected, ruler, rulerLabel, playing, electricFieldMode
    global electricFieldArrowsAll, potentialGridRows, potentialGridCols, electricPotentialLabels
    # delete every charge
    while len(allChargedObjs) > 0:
        chargedObjSelected = allChargedObjs[0]
        deleteChargedObj()

    # ruler
    ruler.modify(0, vpython.vec(0, 0, 0))
    ruler.modify(1, vpython.vec(0, 0, 0))
    rulerLabel.visible = False

    # caption
    createCaptionMainScreen()

    # electric field and potential reset
    for i in range(precision):
        for j in range(precision):
            electricFieldArrowsAll[i][j].visible = False

    for i in range(precision-1):
        for j in range(precision-1):
            electricPotentialLabels[i][j].visible = False
    for i in range(precision):
        potentialGridRows[i].visible = False
        potentialGridCols[i].visible = False

    # reset zoom
    vpython.scene.range = 10

resetButton = None 

# endregion

####################################################################################################

# region Spawn Screen Caption

def createCaptionSpawnScreen():
    global spawnCharge, spawnChargeSlider, spawnChargeText, spawnMass, massSlider, massText, chargeMenu, spawnButton, startButton

    vpython.scene.caption = ""

    vpython.scene.append_to_caption("   Spawn Charge Object Menu: ")
    chargeMenu = vpython.menu(text = "Charge Menu", choices = ["Sphere", "Cyllinder", "Plate", "Box"], bind = spawnRadio) 
    
    spawnCharge = 1E-9
    vpython.scene.append_to_caption("\n\n")
    spawnChargeSlider = vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = 1, step = 0.1, length = sliderLength)
    vpython.scene.append_to_caption("\n")
    spawnChargeText = vpython.wtext(text = '<center>Charge: '+'{:1.2f}'.format(spawnChargeSlider.value) + " nC </center>")

    spawnMass = 1E-6
    vpython.scene.append_to_caption("\n")
    massSlider = vpython.slider(bind=massShift, min = 1, max = 2, value = 1, step = 0.1, length = sliderLength) 
    vpython.scene.append_to_caption("\n")
    massText = vpython.wtext(text = '<center>Mass: '+'{:1.2f}'.format(massSlider.value) + " * 10^-6 Kg</center>")

    vpython.scene.append_to_caption("\n   ")
    spawnButton = vpython.button(text = "Spawn", bind = spawnChargedObj)

    vpython.scene.append_to_caption("   ")
    startButton = vpython.button(text = "Back", bind = start)

# spawn menu
def spawnRadio():
    global chargeMenu 
    chargeMenu.text = "Charge Menu:" 

chargeMenu = None

# spawn slider
spawnCharge = 1E-9

def spawnChargeShift():
    global spawnCharge, spawnChargeText
    spawnCharge = spawnChargeSlider.value * 1E-9
    spawnChargeText.text = '<center>Charge: '+'{:1.2f}'.format(spawnChargeSlider.value) + " nC </center>"
    
spawnChargeSlider = None
spawnChargeText = None

# mass slider
spawnMass = 1E-6

def massShift():
    global spawnMass, massText
    spawnMass = massSlider.value * 1E-6
    massText.text = '<center>Mass: '+'{:1.2f}'.format(massSlider.value) + " * 10^-6 Kg <center>"

massSlider = None
massText = None

# spawn button
def spawnChargedObj():
    allChargedObjs.append(ChargedObj(spawnMass, spawnCharge, spawnPos, vpython.vec(0, 0, 0)))

spawnButton = None

# endregion

####################################################################################################

# region Select Charge Screen Caption

def createCaptionSelectCharge():
    global deleteButton, fixButton

    vpython.scene.caption = ""

    vpython.slider(bind = spawnChargeShift, min = -5, max = 5, value = 1, step = 0.1, length = sliderLength)
    vpython.scene.append_to_caption("\n")
    vpython.wtext(text = '<center>Charge: '+'{:1.2f}'.format(1) + " nC </center>")

    vpython.scene.append_to_caption("\n")
    vpython.slider(bind=massShift, min = 1, max = 2, value = 1, step = 0.1, length = sliderLength) 
    vpython.scene.append_to_caption("\n")
    vpython.wtext(text = '<center>Mass: '+'{:1.2f}'.format(1) + " * 10^-6 Kg</center>")

    vpython.scene.append_to_caption("\n   ")
    vpython.button(text="Show Velocity: True", bind=fixChargedObj)

    vpython.scene.append_to_caption("\n\n   ")
    vpython.button(text="Show Force: False", bind=deleteChargedObj)

    vpython.scene.append_to_caption("\n\n   ")
    fixButton = vpython.button(text="Fix", bind=fixChargedObj)

    vpython.scene.append_to_caption("\n\n   ")
    deleteButton = vpython.button(text="Delete", bind=deleteChargedObj)
    
# delete button
def deleteChargedObj():
    global chargedObjSelected

    # hide everything, remove from list, reset chargedObjSelected
    chargedObjSelected.display.visible = False
    chargedObjSelected.velVec.visible = False
    chargedObjSelected.forceVec.visible = False
    chargedObjSelected.velLabel.visible = False
    chargedObjSelected.forceLabel.visible = False
    chargedObjSelected.hideSelect()
    for i in range(chargedObjSelected.numOfLine):   
            for j in range(precision):
                chargedObjSelected.electricFieldArrows[i][j].visible = False
    allChargedObjs.remove(chargedObjSelected)
    chargedObjSelected = None

deleteButton = None

# fix button
def fixChargedObj():
    chargedObjSelected.fixed = not chargedObjSelected.fixed

fixButton = None

# endregion 

####################################################################################################

# region Program Runs Here
curRange = vpython.scene.range

while True:
    vpython.rate(numOfRate)
    if (playing):
        for chargedObj in allChargedObjs:
            chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            chargedObj.applyVel()
    for chargedObj in allChargedObjs:
        chargedObj.displayElectricField()

    # reset electric field arrows and electric potential grid for all if user zooms
    if (curRange != vpython.scene.range):
        curRange = vpython.scene.range
        setElectricFieldArrowsAll()
        setElectricPotentialGrid()

    displayElectricFieldAll()
    displayElectricPotential()

    # for charge in allChargedObjs:
    #     charge.checkCollision()

    # update force vector because it is possible that mouse is not moving
    if (playing and mouseDown and chargedObjSelected != None):
        chargedObjSelected.forceVec.pos = chargedObjSelected.pos
        chargedObjSelected.forceVec.axis = getMousePos() - chargedObjSelected.pos 
        chargedObjSelected.createForceLabel()

# endregion
