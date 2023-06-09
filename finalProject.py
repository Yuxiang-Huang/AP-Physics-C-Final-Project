# Web VPython 3.2
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
chargeScalar = 1E-9
chargeDensityScalar = 1E-12
massScalar = 1E-9
sphereMassDensity = 2.5E-9

# ratio of length to height for a plate
plateHeightFactor = 20
# ratio of length to length of select display
plateSelectDisplayFactor = 40
# for plate when calculating electric field and potential
deltaFactor = 10

numOfRate = 2000
steps = 10
epsilon = 0.01
electricFieldOpacitySetter = 1

# caption
sliderLength = 450
# the space before text under a slider
sliderTextSpaceLess = "                    "
sliderTextSpaceMore = "                             "

# texture links
positiveSphereTexture = "https://i.imgur.com/9c10QCm.png"
negativeSphereTexture = "https://i.imgur.com/r6loarb.png"
neutralSphereTexture = "https://i.imgur.com/eLOxvSS.png"

fixedPositiveSphereTexture = "https://i.imgur.com/ADy8l2o.png"
fixedNegativeSphereTexture = "https://i.imgur.com/ReG5wU7.png"
fixedNeutralSphereTexture = "https://i.imgur.com/b80Axoa.png"

positivePlateTexture = "https://i.imgur.com/0nKY4ns.png"
negativePlateTexture = "https://i.imgur.com/Ccmo21E.png"
neutralPlateTexture = "https://i.imgur.com/eLOxvSS.png"

# endregion

####################################################################################################

# region Initilization

# store all spawned charges
allChargedObjs = []
allTrails = []

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

def clone(co):
    # copy stats including mass, charge, pos, vel, fixed, trail
    if (co.type == "Sphere"):
        copy = SphereChargedObj(co.mass, co.charge, co.pos, co.vel, co.fixed)
    elif (co.type == "Plate"):
        copy = PlateChargedObj(co.mass, co.charge, co.pos, co.vel)
    copy.trailState = co.trailState
    if (not copy.trailState):
        copy.trail.stop()
    return copy

# region Sphere

class SphereChargedObj:       
    def __init__(self, mass, charge, spawnPos, spawnVel, spawnFixed):
        # patch for making sure deleting everything
        self.deleted = False

        # type 
        self.type = "Sphere"

        # physics variables
        self.charge = charge
        self.mass = mass
        self.pos = spawnPos
        self.vel = spawnVel
        self.fixed = spawnFixed
        self.collided = []

        # force labels
        self.velLabel = label(text = "0", visible = False)
        self.forceLabel = label(text = "0", visible = False)
        self.impulseLabel = label(text = "0", visible = False)

        # radius
        spawnRadius = ((mass) / (((4/3)* pi*sphereMassDensity)))**(1/3)

        # possibly sliders for more variables
        self.numOfLine = 8

        self.trailState = True

        # spheres
        if (charge > 0):
            # display and vectors
            self.display = sphere(pos = spawnPos, radius = spawnRadius)
            if (self.fixed):
                self.display.texture = fixedPositiveSphereTexture
            else:
                self.display.texture = positiveSphereTexture
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
            self.display = sphere(pos=spawnPos, radius=spawnRadius)
            if (self.fixed):
                self.display.texture = fixedNegativeSphereTexture
            else:
                self.display.texture = negativeSphereTexture
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
            self.display = sphere(pos=spawnPos, radius=spawnRadius)
            if (self.fixed):
                self.display.texture = fixedNeutralSphereTexture
            else:
                self.display.texture = neutralSphereTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.black)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.black)

            self.trail = attach_trail(self.display, color = color.black)

        # select display
        self.selectDisplay = []
        self.createSelectDisplay()
        allTrails.append(self.trail)
        self.updateDisplay()

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
        for arc in self.selectDisplay:
            arc.visible = False

    # endregion

    # region force, velocity, and impulse
    def calculateNetForce(self):
        force = calculateNetElectricFieldExclude(self.pos, self) * self.charge
        return force

    def applyForce(self):
        # calculate force from every other charge
        if (not self.fixed):
            # apply force: F * ∆t = m * ∆v
            self.vel += self.calculateNetForce() / numOfRate / self.mass

    def createForceVec(self):
        # arrow
        self.forceVec.visible = True
        self.forceVec.pos = self.pos
        self.forceVec.axis = self.calculateNetForce() * 1E9
        # label
        self.forceLabel.text = "{0:.3f}".format(mag(self.forceVec.axis)) + "nN"
        self.forceLabel.pos = self.forceVec.pos + self.forceVec.axis
        self.forceLabel.visible = True

    def applyVel(self):
        if (not self.fixed):
            self.pos += self.vel / numOfRate
        self.updateDisplay()

    def createVelVec(self):
        # arrow    
        self.velVec.visible = True
        self.velVec.pos = self.pos
        self.velVec.axis = self.vel
        # label
        self.velLabel.text = "{0:.3f}".format(mag(self.velVec.axis)) + "m/s"
        self.velLabel.pos = self.velVec.pos + self.velVec.axis
        self.velLabel.visible = True

    def createImpulseLabel(self):
        self.impulseLabel.text = "{0:.3f}".format(mag(self.impulseVec.axis)) + "μN * " + str(1 / numOfRate) + "s"
        self.impulseLabel.pos = self.impulseVec.pos + self.impulseVec.axis
        self.impulseLabel.visible = True

    def updateDisplay(self):
        self.display.pos = self.pos
        if (self == chargedObjSelected and not self.deleted):
            self.displaySelect()
        
        # vectors
        if (self.fixed or self.deleted):
            self.hideVec()
        else:
            if (vectorToShow == "Velocity"):
                self.createVelVec()
            elif (vectorToShow == "Force"):
                self.createForceVec()
            else:
                self.hideVec()
    
    def hideVec(self):
        self.velVec.visible = False
        self.velLabel.visible = False
        self.forceVec.visible = False
        self.forceLabel.visible = False

    # endregion

    # region electric field and potential

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
                        electricField = calculateNetElectricField(curPos)
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

    def calculateElectricField(self, pos):
        r = pos - self.pos
        return norm(r) * K * self.charge / (mag(r)**2)
    
    def calculateElectricPotential(self, pos):
        r = pos - self.pos
        return  K * self.charge / mag(r)
    
    # endregion

    def onObj(self, mousePos):
        return mag(mousePos - self.pos) <= self.display.radius

    def checkCollision(self):
        # skip if fixed
        if (self.fixed):
            return
        
        for chargedObj in allChargedObjs:
            if (self != chargedObj):
                if (mag(self.pos - chargedObj.pos) <= self.display.radius + chargedObj.display.radius):
                    if (not (chargedObj in self.collided)):
                        # collide with fixed obj
                        if (chargedObj.fixed):
                            # reverse velocity
                            self.vel = - self.vel

                            # position check
                            self.pos = chargedObj.pos + norm(self.pos - chargedObj.pos) * (self.display.radius + chargedObj.display.radius)
                        else:
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

# endregion

# region Plate

class PlateChargedObj:       
    def __init__(self, spawnCharge, spawnChargeDensity, spawnAngle, spawnPos):
        # patch for making sure deleting everything
        self.deleted = False

        # type 
        self.type = "Plate"

        # physics variables
        self.charge = spawnCharge
        self.chargeDensity = spawnChargeDensity
        self.pos = spawnPos
        self.collided = []

        # radius
        spawnLen = sqrt(abs(self.charge) / self.chargeDensity)

        # possibly sliders for more variables
        self.numOfLine = 8

        # thin boxes
        self.display = box(pos = spawnPos, size = vec(spawnLen, spawnLen / plateHeightFactor, spawnLen),
                            axis = vec(cos(radians(spawnAngle)), sin(radians(spawnAngle)), 0))
        
        # differ in charge sign
        if (self.charge > 0):
            # display and vectors
            self.display.texture = positivePlateTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.red)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.red)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.red)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.red)

        elif (self.charge < 0):
            # display and vectors
            self.display.texture = negativePlateTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.blue)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.blue)
        
        else:
            # display and vectors
            self.display.texture = neutralPlateTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.black)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(self.numOfLine)]
            for i in range(self.numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.black)

        # trail (not in use)
        self.trailState = True
        self.trail = attach_trail(self.display)

        # select display
        self.selectDisplay = []
        self.selectDisplayReset = []
        self.createSelectDisplay()
        self.updateDisplay()

    def updateDisplay(self):
        self.display.pos = self.pos
        if (self == chargedObjSelected and not self.deleted):
            self.displaySelect()
    
    # region select display

    def createSelectDisplay(self):
        # create select display
        len = self.display.length / plateSelectDisplayFactor

        # helper variables
        halfLen = self.display.length / 2 + epsilon * 10
        halfHei = self.display.height / 2 + epsilon * 10
        rotAngle = atan2(self.display.axis.y, self.display.axis.x)

        # right side
        curve1 = curve()
        curve1.append({"pos": vec(halfLen - len, halfHei, 0) + self.pos, "color": color.yellow})
        curve1.append({"pos": vec(halfLen, halfHei, 0) + self.pos, "color": color.yellow})
        curve1.append({"pos": vec(halfLen, - halfHei, 0) + self.pos, "color": color.yellow})
        curve1.append({"pos": vec(halfLen - len, - halfHei, 0) + self.pos, "color": color.yellow})
        curve1.rotate(angle = rotAngle, axis = vec(0, 0, 1), origin = self.pos)
        self.selectDisplay.append(curve1)

        # left side
        curve2 = curve()
        curve2.append({"pos": vec(- halfLen + len, halfHei, 0) + self.pos, "color": color.yellow})
        curve2.append({"pos": vec(- halfLen, halfHei, 0) + self.pos, "color": color.yellow})
        curve2.append({"pos": vec(- halfLen, - halfHei, 0) + self.pos, "color": color.yellow})
        curve2.append({"pos": vec(- halfLen + len, - halfHei, 0) + self.pos, "color": color.yellow})
        curve2.rotate(angle = rotAngle, axis = vec(0, 0, 1), origin = self.pos)
        self.selectDisplay.append(curve2)

        self.selectDisplayReset.append(self.pos)
        self.selectDisplayReset.append(rotAngle)

        for c in self.selectDisplay:
            c.visible = False
    
    def displaySelect(self):
        # modify select display
        len = self.display.length / plateSelectDisplayFactor

        # helper variables
        halfLen = self.display.length / 2 + epsilon * 10
        halfHei = self.display.height / 2 + epsilon * 10
        rotAngle = atan2(self.display.axis.y, self.display.axis.x)

        # right side
        curve1 = self.selectDisplay[0]
        curve1.modify(0, pos = vec(halfLen - len, halfHei, 0) + self.pos)
        curve1.modify(1, pos = vec(halfLen, halfHei, 0) + self.pos)
        curve1.modify(2, pos = vec(halfLen, - halfHei, 0) + self.pos)
        curve1.modify(3, pos = vec(halfLen - len, - halfHei, 0) + self.pos)
        
        # reverse rotation and rotate
        curve1.rotate(angle = -self.selectDisplayReset[1], axis = vec(0, 0, 1), 
                      origin = self.selectDisplayReset[0])
        curve1.rotate(angle = rotAngle, axis = vec(0, 0, 1), origin = self.pos)

        # left side
        curve2 = self.selectDisplay[1]
        curve2.modify(0, pos = vec(-halfLen + len, halfHei, 0) + self.pos)
        curve2.modify(1, pos = vec(-halfLen, halfHei, 0) + self.pos)
        curve2.modify(2, pos = vec(-halfLen, - halfHei, 0) + self.pos)
        curve2.modify(3, pos = vec(-halfLen + len, - halfHei, 0) + self.pos)
        curve2.rotation = vec(0, 0, 0)

        # reverse rotation and rotate
        curve2.rotate(angle = -self.selectDisplayReset[1], axis = vec(0, 0, 1), 
                      origin = self.selectDisplayReset[0])
        curve2.rotate(angle = rotAngle, axis = vec(0, 0, 1), origin = self.pos)

        # new reset
        self.selectDisplayReset = []
        self.selectDisplayReset.append(self.pos)
        self.selectDisplayReset.append(rotAngle)

        for c in self.selectDisplay:
            c.visible = True
    
    def hideSelect(self):
        for curve in self.selectDisplay:
            curve.visible = False

    # endregion    

    # region electric field and potential

    def displayElectricField(self):
        # if (self.charge == 0):
        return
        # if (electricFieldMode == 1):
        #     # determine size
        #     size = scene.range / 10
        #     # for every direction
        #     for i in range(self.numOfLine):
        #         # determine starting position
        #         theta = i * 2 * pi / self.numOfLine
        #         curPos = self.pos + vec(cos(theta), sin(theta), 0) * self.display.radius
        #         #for every step
        #         for j in range(electricFieldPrecision):
        #             # don't display if too close to a charge
        #             if (tooClose(self, curPos, size)):
        #                 self.electricFieldArrows[i][j].visible = False
        #             else:
        #                 # determine the arrow 
        #                 electricField = calculateElectricField(curPos)
        #                 arrowLength = norm(electricField) * size
        #                 self.electricFieldArrows[i][j].visible = True
        #                 self.electricFieldArrows[i][j].pos = curPos
        #                 if (self.charge < 0):
        #                     self.electricFieldArrows[i][j].pos -= arrowLength
        #                 self.electricFieldArrows[i][j].axis = arrowLength

        #                 # opacity
        #                 if (electricOpacityMode):
        #                     self.electricFieldArrows[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
        #                 else:
        #                     self.electricFieldArrows[i][j].opacity = 1

        #                 # next position
        #                 curPos += arrowLength * self.charge / abs(self.charge)
        # else: 
        #     # hide all electric field arrows
        #     for i in range(self.numOfLine):   
        #         for j in range(electricFieldPrecision):
        #             self.electricFieldArrows[i][j].visible = False

    def calculateElectricField(self, pos):
        electricField = vec(0, 0, 0)
        # helper variables
        deltaX = self.display.axis.x / (deltaFactor - 1)
        deltaY = self.display.axis.y / (deltaFactor - 1)
        deltaZ = self.display.width / (deltaFactor - 1)
        startPos = self.pos - norm(self.display.axis) * self.display.length / 2
        # loop to find pos of each dA
        for i in range(deltaFactor):
            for j in range(deltaFactor):
                curPos = vec(startPos.x + deltaX * i, startPos.y + deltaY * i, - self.display.width / 2 + deltaZ * j)
                # dE = norm(r) * K * (dA * charge density) / r^2
                r = pos - curPos
                dA = self.display.length / deltaFactor * self.display.width / deltaFactor 
                electricField += norm(r) * K * (dA * self.chargeDensity) / (mag(r)**2) * self.charge / abs(self.charge)
        return electricField
    
    def calculateElectricPotential(self, pos):
        electricFieldPotential = 0
        # helper variables
        deltaX = self.display.axis.x / (deltaFactor - 1)
        deltaY = self.display.axis.y / (deltaFactor - 1)
        deltaZ = self.display.width / (deltaFactor - 1)
        startPos = self.pos - norm(self.display.axis) * self.display.length / 2
        # loop to find pos of each dA
        for i in range(deltaFactor):
            for j in range(deltaFactor):
                curPos = vec(startPos.x + deltaX * i, startPos.y + deltaY * i, - self.display.width / 2 + deltaZ * j)
                # dV = K * (dA * charge density) / r
                r = pos - curPos
                dA = self.display.length / deltaFactor * self.display.width / deltaFactor 
                electricFieldPotential += K * (dA * self.chargeDensity) / mag(r) * self.charge / abs(self.charge)
        return electricFieldPotential
    
    # endregion
    
    def checkCollision(self):
        # skip if fixed
        if (self.fixed):
            return
        
        for chargedObj in allChargedObjs:
            if (self != chargedObj):
                if (mag(self.pos - chargedObj.pos) <= self.display.radius + chargedObj.display.radius):
                    if (not (chargedObj in self.collided)):
                        # collide with fixed obj
                        if (chargedObj.fixed):
                            # reverse velocity
                            self.vel = - self.vel

                            # apply force again
                            # self.vel += calculateForce(chargedObj, self) / numOfRate / self.mass

                            # position check
                            self.pos = chargedObj.pos + norm(self.pos - chargedObj.pos) * (self.display.radius + chargedObj.display.radius)
                        else:
                            # v1 = 2 * m2 / (m1 + m2) * v2 + (m1 - m2) / (m1 + m2) * v1
                            tempvel = (2 * chargedObj.mass / (chargedObj.mass + self.mass) * chargedObj.vel +
                            (self.mass - chargedObj.mass) / (chargedObj.mass + self.mass) * self.vel)

                            # v2 = 2 * m1 / (m1 + m2) * v1 + (m2 - m1) / (m1 + m2) * v2
                            chargedObj.vel = (2 * self.mass / (chargedObj.mass + self.mass) * self.vel +
                            (chargedObj.mass - self.mass) / (chargedObj.mass + self.mass) * chargedObj.vel)

                            self.vel = tempvel

                            # apply force again
                            # self.vel += calculateForce(chargedObj, self) / numOfRate / self.mass
                            # chargedObj.vel += calculateForce(self, chargedObj) / numOfRate / self.mass

                            # position check
                            dif = self.display.radius + chargedObj.display.radius - mag(self.pos - chargedObj.pos) 
                            tempPos = self.pos + norm(self.pos - chargedObj.pos) * dif / 2
                            chargedObj.pos = chargedObj.pos + norm(chargedObj.pos - self.pos) * dif / 2
                            self.pos = tempPos

                        # prevent collision calculation twice
                        chargedObj.collided.append(self)


        # if (self.charge == 0):
        #     return
        
        # if (electricFieldMode == 1):
        #     # determine size
        #     size = scene.range / 10
        #     # for every direction
        #     for i in range(self.numOfLine):
        #         # determine starting position
        #         theta = i * 2 * pi / self.numOfLine
        #         curPos = self.pos + vec(cos(theta), sin(theta), 0) * self.display.radius
        #         #for every step
        #         for j in range(electricFieldPrecision):
        #             # don't display if too close to a charge
        #             if (tooClose(self, curPos, size)):
        #                 self.electricFieldArrows[i][j].visible = False
        #             else:
        #                 # determine the arrow 
        #                 electricField = calculateElectricField(curPos)
        #                 arrowLength = norm(electricField) * size
        #                 self.electricFieldArrows[i][j].visible = True
        #                 self.electricFieldArrows[i][j].pos = curPos
        #                 if (self.charge < 0):
        #                     self.electricFieldArrows[i][j].pos -= arrowLength
        #                 self.electricFieldArrows[i][j].axis = arrowLength

        #                 # opacity
        #                 if (electricOpacityMode):
        #                     self.electricFieldArrows[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
        #                 else:
        #                     self.electricFieldArrows[i][j].opacity = 1

        #                 # next position
        #                 curPos += arrowLength * self.charge / abs(self.charge)
        # else: 
            # hide all electric field arrows
            for i in range(self.numOfLine):   
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j].visible = False

    def onObj(self, mousePos):
        # find vertices
        halfLen = self.display.length / 2
        halfHei = self.display.height / 2
        rotAngle = atan2(self.display.axis.y, self.display.axis.x)

        vertices = [vec(halfLen, halfHei, 0) + self.pos, vec(-halfLen, halfHei, 0) + self.pos, 
                    vec(-halfLen, -halfHei, 0) + self.pos, vec(halfLen, -halfHei, 0) + self.pos]

        for i in range(4):
            vertices[i] -= self.pos
            vertices[i] = vertices[i].rotate(angle = rotAngle)
            vertices[i] += self.pos
        
        # use cross products to determine if inside
        for i in range(4):
            v1 = vertices[i] - mousePos
            v2 = vertices[(i + 1) % 4] - mousePos
            if v1.cross(v2).z < 0:
                return False
        return True

# endregion

# endregion

def testPlate():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(2,0,0), vec(0, 0, 0), False))
    allChargedObjs.append(PlateChargedObj(chargeScalar, 10 * chargeDensityScalar, 90, vec(0, 0, 0)))

####################################################################################################

# region Electric Field and Potential

def displayElectricFieldAll():
    # calculate electric field for each arrow
    if (electricFieldMode == 2):
        size = scene.range / 10
        for i in range(gridPrecision):
            for j in range(gridPrecision):
                electricField = calculateNetElectricField(electricFieldArrowsAll[i][j].pos)
                electricFieldArrowsAll[i][j].axis = norm(electricField) * size
                if (electricOpacityMode):
                    electricFieldArrowsAll[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
                else:
                    electricFieldArrowsAll[i][j].opacity = 1
    
def calculateNetElectricField(pos):
    electricField = vec(0, 0, 0)
    for co in allChargedObjs:
        electricField += co.calculateElectricField(pos)
    return electricField

def calculateNetElectricFieldExclude(pos, exclude):
    electricField = vec(0, 0, 0)
    for co in allChargedObjs:
        if (co != exclude):
            electricField += co.calculateElectricField(pos)
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
                electricPotentialLabels[i][j].text = '{:1.3f}'.format(calculateNetElectricPotential(electricPotentialLabels[i][j].pos))

def calculateNetElectricPotential(pos):
    electricPotential = 0
    for co in allChargedObjs:
        electricPotential +=  co.calculateElectricPotential(pos)
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
                createCaptionSelectScreen()
            # spawn screen when the click is not on a charged object
            else:
                spawnPos = getMousePos()
                createCaptionSpawnScreen()
                displaySpawnPosIndicator(spawnPos)
        else:
            # reselect 
            chargedObjSelected.hideSelect()
            chargedObjSelected = chargedObjOnMouse()

            # select again or deselect
            if (chargedObjSelected != None):
                chargedObjSelected.displaySelect()
                createCaptionSelectScreen()
            else:
                createCaptionMainScreen()

# helper methods
def chargedObjOnMouse():
    mousePos = getMousePos()
    for co in allChargedObjs:
        if (co.onObj(mousePos)):
            return co
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
dragOffset = vec(0, 0, 0)

def onMouseDown():
    global chargedObjToDrag, mouseDown, ruler, dragOffset
    # assign charged object to drag
    chargedObjToDrag = chargedObjOnMouse()
    if (chargedObjToDrag != None):
        dragOffset = chargedObjToDrag.pos - getMousePos()
    mouseDown = True

    # initial pos of ruler
    if (chargedObjToDrag == None and not playing):
        ruler.modify(0, getMousePos())
        ruler.modify(1, getMousePos())
        rulerLabel.visible = False

def onMouseUp():
    global chargedObjToDrag, mouseDown
    # apply impulse vector if necessary
    if (chargedObjSelected != None):
        if (chargedObjSelected.impulseVec.axis != vec(0, 0, 0)):
            chargedObjSelected.vel += chargedObjSelected.impulseVec.axis / 1E6 / numOfRate / chargedObjSelected.mass 
            chargedObjSelected.impulseVec.axis = vec(0, 0, 0)
            chargedObjSelected.impulseLabel.visible = False

    # minimum length check for the ruler
    if (mag(ruler.point(1)['pos'] - ruler.point(0)['pos']) < epsilon * scene.range):
        rulerLabel.visible = False
        ruler.modify(0, vec(0, 0, 0))
        ruler.modify(1, vec(0, 0, 0))
    
    if (chargedObjToDrag != None):
        # start trail if necessary
        if (chargedObjToDrag.trailState):
            chargedObjToDrag.trail.start()

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
                chargedObjToDrag.pos = mousePos + dragOffset
                chargedObjToDrag.updateDisplay()

                # don't display trail when move
                chargedObjToDrag.trail.stop()

                # could have impacted electric field and potential in the spawn screen
                if (spawnPos != None):
                    updateSpawnScreen()

                # update the force in select screen
                if (chargedObjSelected != None):
                    updateForceStatSelectScreen()
        else:
            # conditions for setting velocity vectors: not playing, dragging, sphere, obj not fixed, and in show velocity vector mode, 
            if not playing and chargedObjToDrag != None and chargedObjToDrag.type == "Sphere" and not chargedObjToDrag.fixed and vectorToShow == "Velocity":
                # set velocity vector
                chargedObjToDrag.velVec.axis = getMousePos() - chargedObjToDrag.pos
                chargedObjToDrag.vel = chargedObjToDrag.velVec.axis
                chargedObjToDrag.createVelVec()
                # reset if velocity vector is too small
                if (mag(chargedObjToDrag.velVec.axis) < chargedObjToDrag.display.radius):
                    chargedObjToDrag.vel = vec(0, 0, 0)
                    chargedObjToDrag.velVec.visible = False
                    chargedObjToDrag.velLabel.visible = False
                updateVelocityStatsSelectScreen()

# endregion

####################################################################################################

# region Intro Screen

# intro text
startText = text(pos = vec(0, -3, 0), text="JackXiang", align='center', color = color.cyan)
startText.height = 10
startText.length = 25

# start Button
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

# presets
def dipolePreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5,0,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-5, 0, 0) , vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(5, -1, 0) , vec(0, 0, 0), False))
    
def threeChargePreset(): 
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -1.5*chargeScalar, vec(-5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0), False))

def butterflyPreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(5,5,0), vec(-1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 5*chargeScalar, vec(2.5,0,0), vec(0, 1, 0), False))

def helixPreset(): 
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-1.5,10,0), vec(.25, -2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(1.5,10,0), vec(-.25, -2, 0), False))

def helixGunPreset ():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-15,1.5,0), vec(2, -.25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-15,-1.5,0), vec(2, .25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,1.5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,-1.5,0), vec(0, 0, 0), False))
    
def dragonflyPreset ():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(4.33,-2.5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-4.33,-2.5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -5*chargeScalar, vec(0,0,0), vec(0, 0, 0), False))
    
def somethingPreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -5*chargeScalar, vec(0,5,0), vec(3, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5*cos(30),-5*sin(30),0), vec(-1, 2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 5*chargeScalar, vec(-5*cos(30),-5*sin(30),0), vec(1, 2, 0), False))

def yPreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(5,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 15*chargeScalar, vec(2.5,0,0), vec(0, 0, 0), False))

def jPreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(-5,5,0), vec(1, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(-6,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(6,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(0, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -.25*chargeScalar, vec(2.5,-3.5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -.25*chargeScalar, vec(-3.5,-6.5,0), vec(0, 0, 0), False))

def chargeTrampolinePreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,0,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(5,0,0), vec(0, 0, 0), False))
    
def figureEightPreset():
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,0,0), vec(1,1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar * 1.1, vec(0,-5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar * 1.1, vec(0,5,0), vec(0, 0, 0), True))
    
def circularOrbitPreset(): 
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,0,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(sqrt((9E9*1E-9*1E-9)/(5*1E-9)), 0, 0), False))
    
#same right now as circular orbit, but this is unfixed and the circular orbit will be fixed
def loopWavePreset(): 
    start()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-15,0,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-15,5,0), vec(sqrt((9E9*1E-9*1E-9)/(5*1E-9)), 0, 0), False))

# preset
button(text = "test plate", bind = testPlate)
scene.append_to_caption("\n\n   ")
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
button(text = "Draw a Y", bind = yPreset)
scene.append_to_caption(" ")
button(text = "Draw a J", bind = jPreset)
scene.append_to_caption("\n\n   ")
button(text = "Charge Trampoline", bind = chargeTrampolinePreset) 
scene.append_to_caption("\n\n   ")
button(text = "model circular orbit", bind = circularOrbitPreset)
scene.append_to_caption(" ")
button(text = "loop Wave Thing", bind = loopWavePreset)
scene.append_to_caption("\n\n   ")
button(text = "draw figure 8", bind = figureEightPreset)

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
        playButton = button(text="■ Stop", bind = changePlay)
    else:
        playButton = button(text="► Play", bind = changePlay)

    # instruction button
    global instructionButton
    scene.append_to_caption("   ")
    instructionButton = button(text="Instructions", bind = displayInstructionPage)

    # clear button
    global clearButton
    scene.append_to_caption("   ")
    clearButton = button(text = "Clear", bind = clear)

    # save button
    global saveButton
    scene.append_to_caption("   ")
    saveButton = button(text = "Save", bind = save)

    createSavedCaption()

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
    global allTrailCheckbox
    scene.append_to_caption("   ")
    allTrailCheckbox = checkbox(text = "All Trail", bind = changeTrailStateAll, checked = trailStateAll)

    # clear trail button
    global clearAllTrailButton
    scene.append_to_caption("   ")
    clearAllTrailButton = button (text = "Clear All Trail", bind = clearTrailAll)

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
    if (playing):
        playButton.text = "■ Stop"
        # take out sliders to prevent changing charge and mass during play
        if (chargedObjSelected != None):
            createCaptionSelectScreen() 
    else:
        playButton.text = "► Play"
        # update select screen if necessary
        if (chargedObjSelected != None):
            createCaptionSelectScreen()

# instruction button
def displayInstructionPage():
    global startButton
    scene.caption = ""
    startButton = button(text = "Back", bind = createCaptionMainScreen)
    scene.append_to_caption("\n")
    createInstruction()

# save button
savedVersions = []
savedVersionsNames = []

def save():
    global savedVersions, savedVersionsNames
    newVersion = []
    # clone all charged objs
    for co in allChargedObjs:
        copy = clone(co)
        # hide
        copy.display.visible = False
        copy.hideVec()
        # add to new list
        newVersion.append(copy)
    # add to stored versions
    savedVersions.append(newVersion)
    name = input("Save as: ")
    # name already exists
    if (name in savedVersionsNames):
        name += " ({})".format(len(savedVersionsNames))
    savedVersionsNames.append(name)
    createCaptionMainScreen()
    
def createSavedCaption():
    for i in range(len(savedVersions)):
        scene.append_to_caption("   ")
        button(text = savedVersionsNames[i], bind = toSaved)

def toSaved(version):
    global allChargedObjs 
    clear()
    i = savedVersionsNames.index(version.text)
    for co in savedVersions[i]:
        # clone again so the button can be reused
        allChargedObjs.append(clone(co))

# clear button
def clear():
    global chargedObjSelected
    # clear all charged objs
    i = len(allChargedObjs) - 1
    while i >= 0:
        deleteChargedObj(allChargedObjs[i])
        i -= 1
    # clear all trails
    i = len(allTrails) - 1
    while i >= 0:
        allTrails[i].clear()
        allTrails.remove(allTrails[i])
        i -= 1
    createCaptionMainScreen()

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
    # hide earlier vector
    for co in allChargedObjs:
        if (not co.fixed):
            if (vectorToShow == "Velocity"):
                co.velVec.visible = False
                co.velLabel.visible = False
            elif (vectorToShow == "Force"):
                co.forceVec.visible = False
                co.forceLabel.visible = False

    vectorToShow = vectorMenu.selected

    # show new vector if not playing
    if (not playing):
        for co in allChargedObjs:
            if (not co.fixed):
                if (vectorToShow == "Velocity"):
                    co.createVelVec()
                elif (vectorToShow == "Force"):
                    co.createForceVec()

# all trail checkbox
trailStateAll = True

def changeTrailStateAll():
    global trailStateAll, allChargedObjs
    trailStateAll = not trailStateAll
    for co in allChargedObjs:
        if (trailStateAll):
            co.trail.start()
        else:
            co.trail.stop()

# clear all trail button
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
    chargeMenu = menu(choices = ["Sphere", "Plate"], bind = selectSpawnChargeObj, selected = spawnType) 
    
    # spawn charge slider and input field
    global spawnChargeSlider, spawnChargeInputField
    scene.append_to_caption("\n\n")
    if (chargeMenu.selected == "Sphere"):
        spawnChargeSlider = slider(bind = spawnChargeShift, min = -5, max = 5, value = spawnChargeSphere / chargeScalar, step = 0.1, length = sliderLength)
    elif (chargeMenu.selected == "Plate"):
        spawnChargeSlider = slider(bind = spawnChargeShift, min = -5, max = 5, value = spawnChargePlate / chargeScalar, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n" + sliderTextSpaceMore + "Charge: ")
    spawnChargeInputField = winput(bind = spawnChargeInput, text = spawnChargeSlider.value, width = 35)
    scene.append_to_caption(" nC")

    global spawnChargeDensitySlider, spawnChargeDensityInputField
    if (chargeMenu.selected == "Plate"):
        scene.append_to_caption("\n\n")
        spawnChargeDensitySlider = slider(bind = spawnChargeDensityShift, min = 1, max = 100, value = spawnChargeDensity / chargeDensityScalar, step = 1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceLess + "Charge Density: ")
        spawnChargeDensityInputField = winput(bind = spawnChargeDensityInput, text = spawnChargeDensitySlider.value, width = 35)
        scene.append_to_caption(" pC/m^2")

    # spawn mass slider and input field
    global spawnMassSlider, spawnMassInputField
    if (chargeMenu.selected == "Sphere"):
        scene.append_to_caption("\n\n")
        spawnMassSlider = slider(bind = spawnMassShift, min = 1, max = 5, value = spawnMass / massScalar, step = 0.1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceMore + "Mass: ")
        spawnMassInputField = winput(bind = spawnMassInput, text = spawnMassSlider.value, width = 35)
        scene.append_to_caption(" * 10^-9 Kg")

    # spawn angle slider and input field
    global spawnAngleSlider, spawnAngleInputField
    if (chargeMenu.selected == "Plate"):
        scene.append_to_caption("\n\n")
        spawnAngleSlider = slider(bind = spawnAngleShift, min = 0, max = 180, value = spawnAngle, step = 1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceMore + "Angle: ")
        spawnAngleInputField = winput(bind = spawnAngleInput, text = spawnAngleSlider.value, width = 35)
        scene.append_to_caption(" degrees")

    # spawn and back buttons
    global spawnButton, backButton
    scene.append_to_caption("\n\n   ")
    spawnButton = button(text = "Spawn", bind = spawnChargedObj)
    scene.append_to_caption("   ")
    backButton = button(text = "Back", bind = back)

    # spawn position input fields
    global spawnXInputField, spawnYInputField
    scene.append_to_caption("\n\n   Position: <")
    spawnXInputField = winput(bind = spawnXInput, text = '{:1.3f}'.format(spawnPos.x), width = 60)
    scene.append_to_caption(", ")
    spawnYInputField = winput(bind = spawnYInput, text = '{:1.3f}'.format(spawnPos.y), width = 60) 
    scene.append_to_caption(">")

    # electric field and potential texts
    global electricFieldText, electricPotentialText
    scene.append_to_caption("\n\n   ")
    electricFieldText = wtext()
    scene.append_to_caption("\n\n   ")
    electricPotentialText = wtext()
    updateSpawnScreen()

# spawn charge menu
spawnType = "Plate"

def selectSpawnChargeObj():
    global spawnType
    spawnType = chargeMenu.selected
    createCaptionSpawnScreen()

# spawn charge slider and input field
spawnChargeSphere = chargeScalar
spawnChargePlate = chargeScalar

def spawnChargeShift():
    global spawnChargeSphere, spawnChargePlate, spawnChargeInputField
    if (chargeMenu.selected == "Sphere"):
        spawnChargeSphere = spawnChargeSlider.value * chargeScalar    
    elif (chargeMenu.selected == "Plate"):
        spawnChargePlate = spawnChargeSlider.value * chargeScalar    
    spawnChargeInputField.text = spawnChargeSlider.value

def spawnChargeInput():
    global spawnChargeSphere, spawnChargePlate, spawnChargeSlider, spawnChargeInputField
    if (spawnChargeInputField.number != None):
        # min max
        num = max(spawnChargeSlider.min, spawnChargeInputField.number)
        num = min(spawnChargeSlider.max, num)
        # set values
        if (chargeMenu.selected == "Sphere"):
            spawnChargeSphere = num * chargeScalar
        elif (chargeMenu.selected == "Plate"):
            spawnChargePlate = num * chargeScalar
        spawnChargeSlider.value = num
        spawnChargeInputField.text = num
    else:
        # invalid input
        if (chargeMenu.selected == "Sphere"):
            spawnChargeInputField.text = spawnChargeSphere / chargeScalar
        elif (chargeMenu.selected == "Plate"):
            spawnChargeInputField.text = spawnChargePlate / chargeScalar

# spawn charge density slider and input field
spawnChargeDensity = 10 * chargeDensityScalar

def spawnChargeDensityShift():
    global spawnChargeDensity, spawnChargeDensityInputField
    spawnChargeDensity = spawnChargeDensitySlider.value * chargeDensityScalar    
    spawnChargeDensityInputField.text = spawnChargeDensitySlider.value

def spawnChargeDensityInput():
    global spawnChargeDensity, spawnChargeDensitySlider, spawnChargeDensityInputField
    if (spawnChargeDensityInputField.number != None):
        # min max
        num = max(spawnChargeDensitySlider.min, spawnChargeDensityInputField.number)
        num = min(spawnChargeDensitySlider.max, num)
        # set values
        spawnChargeDensity = num * chargeDensityScalar
        spawnChargeDensitySlider.value = num
        spawnChargeDensityInputField.text = num
    else:
        # invalid input
        spawnChargeDensityInputField.text = spawnChargeDensity / chargeDensityScalar

# spawn mass slider and input field
spawnMass = massScalar

def spawnMassShift():
    global spawnMass, spawnMassInputField
    spawnMass = spawnMassSlider.value * massScalar
    spawnMassInputField.text = spawnMassSlider.value

def spawnMassInput():
    global spawnMass, spawnMassSlider, spawnMassInputField
    if (spawnMassInputField.number != None):
        # min max
        num = max(spawnMassSlider.min, spawnMassInputField.number)
        num = min(spawnMassSlider.max, num)
        # set values
        spawnMass = num * massScalar
        spawnMassSlider.value = num
        spawnMassInputField.text = num
    else:
        # invalid input
        spawnMassInputField.text = spawnMass / massScalar

# spawn angle slider and input field
spawnAngle = 90

def spawnAngleShift():
    global spawnAngle, spawnAngleInputField
    spawnAngle = spawnAngleSlider.value
    spawnAngleInputField.text = spawnAngleSlider.value

def spawnAngleInput():
    global spawnAngle, spawnAngleSlider, spawnAngleInputField
    if (spawnAngleInputField.number != None):
        # min max
        num = max(spawnAngleSlider.min, spawnAngleInputField.number)
        num = min(spawnAngleSlider.max, num)
        # set values
        spawnAngle = num
        spawnAngleSlider.value = num
        spawnAngleInputField.text = num
    else:
        # invalid input
        spawnAngleInputField.text = spawnAngle

# spawn button
def spawnChargedObj():
    if (spawnType == "Sphere"):
        allChargedObjs.append(SphereChargedObj(spawnMass, spawnChargeSphere, spawnPos, vec(0, 0, 0), False))
    elif (spawnType == "Plate"):
        allChargedObjs.append(PlateChargedObj(spawnChargePlate, spawnChargeDensity, spawnAngle, spawnPos))
    back()

# back button
def back():
    global spawnPos
    createCaptionMainScreen()
    spawnPosIndicator.visible = False
    spawnPos = None

# spawn position input fields
def spawnXInput():
    global spawnPos, spawnPosIndicator, spawnXInputField
    # change the x value of spawn position
    if (spawnXInputField.number != None):
        spawnPos.x = spawnXInputField.number
        updateSpawnScreen()
        displaySpawnPosIndicator(spawnPos)  
    else:
        # invalid input
        spawnXInputField.text = '{:1.3f}'.format(spawnPos.x)

def spawnYInput():
    global spawnPos, spawnPosIndicator, spawnYInputField
    # change the y value of spawn position
    if (spawnYInputField.number != None):
        spawnPos.y = spawnYInputField.number
        updateSpawnScreen()
        displaySpawnPosIndicator(spawnPos)
    else: 
        # invalid input
        spawnYInputField.text = '{:1.3f}'.format(spawnPos.y)

# electric field and potential texts
def updateSpawnScreen():
    global electricFieldText, electricPotentialText
    # recalculate electric field and potential
    electricField = calculateNetElectricField(spawnPos)
    electricFieldText.text = ("Electric Field: <" + 
                                        '{:1.3f}'.format(electricField.x) + ", " + 
                                        '{:1.3f}'.format(electricField.y) + "> N/C \n   Electric Field: "+
                                        '{:1.3f}'.format((mag(electricField))) + " N/C @ " +
                                        '{:1.2f}'.format(degrees(atan2(electricField.y, electricField.x))) + " degree")
    electricPotentialText.text = "Electric Potential: " '{:1.3f}'.format(calculateNetElectricPotential(spawnPos)) + " V"

# endregion

####################################################################################################

# region Select ChargedObj Screen Caption

def createCaptionSelectScreen():
    createCaptionMainScreen()

    # camera follow button
    global cameraFollowButton
    scene.append_to_caption("   ")
    if (cameraFollowedObj == chargedObjSelected.display):
        cameraFollowButton = button(text = "Camera Unfollow", bind = cameraFollow)
    else:
        cameraFollowButton = button(text = "Camera Follow", bind = cameraFollow)

    # select charge slider and input field
    global selectedChargeSlider, selectedChargeInputField
    scene.append_to_caption("\n\n")
    selectedChargeSlider = slider(bind = selectedChargeShift, min = -5, max = 5, value = chargedObjSelected.charge / chargeScalar, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n" + sliderTextSpaceMore + "Charge: ")
    selectedChargeInputField = winput(bind = selectedChargeInput, text = selectedChargeSlider.value, width = 35)
    scene.append_to_caption(" nC")

    selectedChargeSlider.disabled = playing
    selectedChargeInputField.disabled = playing

    # select charge density slider and input field
    global selectedChargeDensitySlider, selectedChargeDensityInputField
    if (chargedObjSelected.type == "Plate"):
        scene.append_to_caption("\n\n")
        selectedChargeDensitySlider = slider(bind = selectedChargeDensityShift, min = 1, max = 100, value = chargedObjSelected.chargeDensity / chargeDensityScalar, step = 1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceLess + "Charge Density: ")
        selectedChargeDensityInputField = winput(bind = selectedChargeDensityInput, text = selectedChargeDensitySlider.value, width = 35)
        scene.append_to_caption(" pC/m^2")

        selectedChargeDensitySlider.disabled = playing
        selectedChargeDensityInputField.disabled = playing

    # select mass slider and input field
    global selectedMassSlider, selectedMassInputField
    if (chargedObjSelected.type == "Sphere"):
        scene.append_to_caption("\n\n")
        selectedMassSlider = slider(bind = selectedMassShift, min = 1, max = 5, value = chargedObjSelected.mass / massScalar, step = 0.1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceMore + "Mass: ")
        selectedMassInputField = winput(bind = selectedMassInput, text = selectedMassSlider.value, width = 35)
        scene.append_to_caption(" * 10^-9 Kg")

        selectedMassSlider.disabled = playing
        selectedMassInputField.disabled = playing

    # select angle slider and input field
    global selectedAngleSlider, selectedAngleInputField
    if (chargedObjSelected.type == "Plate"):
        scene.append_to_caption("\n\n")
        selectedAngleSlider = slider(bind = selectedAngleShift, min = 0, max = 180, 
                                     value = degrees(atan2(chargedObjSelected.display.axis.y, chargedObjSelected.display.axis.x)), step = 1, length = sliderLength)
        scene.append_to_caption("\n" + sliderTextSpaceMore + "Angle: ")
        selectedAngleInputField = winput(bind = selectedAngleInput, text = selectedAngleSlider.value, width = 35)
        scene.append_to_caption(" degrees")

        selectedAngleSlider.disabled = playing
        selectedAngleInputField.disabled = playing

    # need for both types but not in the same place...
    global deleteButton
        
    # for sphere
    if (chargedObjSelected.type == "Sphere"):
        # fix button
        global fixButton
        scene.append_to_caption("\n\n   ")
        if (chargedObjSelected.fixed):
            fixButton = button(text = "Unfix", bind=fixChargedObj)
        else:
            fixButton = button(text = "Fix", bind=fixChargedObj)

        # trail checkbox
        global trailCheckbox
        scene.append_to_caption("   ")
        trailCheckbox = checkbox(text = "Trail", bind = changeTrailState, checked = chargedObjSelected.trailState)

        # clear trail button
        global clearTrailButton
        scene.append_to_caption("   ")
        clearTrailButton = button (text = "Clear Trail", bind = clearTrail)

        # delete button
        scene.append_to_caption("   ")
        deleteButton = button(text = "Delete", bind=deleteSelectChargedObj)

    # select position input fields
    global selectPosXInputField, selectPosYInputField
    scene.append_to_caption("\n\n   Position: <")
    selectPosXInputField = winput(bind = selectPosXInput, text = '{:1.3f}'.format(chargedObjSelected.pos.x), width = 60)
    scene.append_to_caption(", ")
    selectPosYInputField = winput(bind = selectPosYInput, text = '{:1.3f}'.format(chargedObjSelected.pos.y), width = 60) 
    scene.append_to_caption(">")

    # delete button for plate
    if (chargedObjSelected.type == "Plate"):
        scene.append_to_caption("   ")
        deleteButton = button(text = "Delete", bind=deleteSelectChargedObj)
    
    if (chargedObjSelected.type == "Sphere"):
        # select velocity XY setter
        global selectedVelXInputField, selectedVelYInputField
        scene.append_to_caption("\n\n   Velocity: <")
        selectedVelXInputField = winput(bind = selectVelXInput, width = 60)
        scene.append_to_caption(", ")
        selectedVelYInputField = winput(bind = selectVelYInput, width = 60) 
        scene.append_to_caption(">")

        # select velocity MA setter
        global selectedVelMagInputField, selectedVelAngleInputField
        scene.append_to_caption("\n   Velocity: <")
        selectedVelMagInputField = winput(bind = selectVelMagInput, width = 60)
        scene.append_to_caption(" m/s @ ")
        selectedVelAngleInputField = winput(bind = selectVelAngleInput, width = 60)
        scene.append_to_caption(" degree")

        updateVelocityStatsSelectScreen()

        # select force stats
        global selectedChargeForceXYText, selectedChargeForceMAText
        scene.append_to_caption("\n\n   ")
        selectedChargeForceXYText = wtext() 
        scene.append_to_caption("\n\n   ")
        selectedChargeForceMAText= wtext()
        updateForceStatSelectScreen()

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

# selected charge slider and input field
def selectedChargeModified():
    global chargedObjSelected
    if (chargedObjSelected.type == "Sphere"):
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
    elif (chargedObjSelected.type == "Plate"):
        # change the texture
        if (chargedObjSelected.charge > 0):
            chargedObjSelected.display.texture = positivePlateTexture
        elif (chargedObjSelected.charge < 0): 
            chargedObjSelected.display.texture = negativePlateTexture
        else:
            chargedObjSelected.display.texture = neutralPlateTexture

        # change length
        len = sqrt(abs(chargedObjSelected.charge) / chargedObjSelected.chargeDensity)
        chargedObjSelected.display.length = len
        chargedObjSelected.display.height = len / plateHeightFactor
        chargedObjSelected.display.width = len
        chargedObjSelected.displaySelect()

def selectedChargeShift(): 
    global chargedObjSelected, selectedChargeSlider, selectedChargeInputField
    chargedObjSelected.charge = selectedChargeSlider.value * chargeScalar      
    selectedChargeInputField.text = selectedChargeSlider.value
    selectedChargeModified()
    
def selectedChargeInput():
    global chargedObjSelected, selectedChargeSlider, selectedChargeInputField
    if (selectedChargeInputField.number != None):
        # min max
        num = max(selectedChargeSlider.min, selectedChargeInputField.number)
        num = min(selectedChargeSlider.max, num)
        # set values
        chargedObjSelected.charge = num * chargeScalar
        selectedChargeSlider.value = num
        selectedChargeInputField.text = num
        selectedChargeModified()
    else:
        selectedChargeInputField.text = chargedObjSelected.charge / chargeScalar

# selected charge density slider and input field
def selectedChargeDensityShift(): 
    global chargedObjSelected, selectedChargeDensitySlider, selectedChargeDensityInputField
    chargedObjSelected.chargeDensity = selectedChargeDensitySlider.value * chargeDensityScalar   
    selectedChargeDensityInputField.text = selectedChargeDensitySlider.value
    # change length
    len = sqrt(abs(chargedObjSelected.charge) / chargedObjSelected.chargeDensity)
    chargedObjSelected.display.length = len
    chargedObjSelected.display.height = len / plateHeightFactor
    chargedObjSelected.display.width = len
    chargedObjSelected.displaySelect()

def selectedChargeDensityInput():
    global chargedObjSelected, selectedChargeDensitySlider, selectedChargeDensityInputField 
    if (selectedChargeDensityInputField.number != None):
        # min max
        num = max(selectedChargeDensitySlider.min, selectedChargeDensityInputField.number)
        num = min(selectedChargeDensitySlider.max, num)
        # set values
        chargedObjSelected.chargeDensity = num * chargeDensityScalar
        selectedChargeDensitySlider.value = num
        selectedChargeDensityInputField.text = num
        # change length
        len = sqrt(abs(chargedObjSelected.charge) / chargedObjSelected.chargeDensity)
        chargedObjSelected.display.length = len
        chargedObjSelected.display.height = len / plateHeightFactor
        chargedObjSelected.display.width = len
        chargedObjSelected.displaySelect()
    else:
        selectedChargeDensityInputField.text = chargedObjSelected.chargeDensity / chargeDensityScalar

# selected mass slider and input field
def selectedMassShift(): 
    global chargedObjSelected, selectedMassSlider, selectedMassInputField
    chargedObjSelected.mass = selectedMassSlider.value * massScalar   
    selectedMassInputField.text = selectedMassSlider.value
    # change radius
    chargedObjSelected.display.radius = ((chargedObjSelected.mass) / (((4/3)* pi*sphereMassDensity)))**(1/3)
    chargedObjSelected.displaySelect()

def selectedMassInput():
    global chargedObjSelected, selectedMassSlider, selectedMassInputField 
    if (selectedMassInputField.number != None):
        # min max
        num = max(selectedMassSlider.min, selectedMassInputField.number)
        num = min(selectedMassSlider.max, num)
        # set values
        chargedObjSelected.mass = num * massScalar
        selectedMassSlider.value = num
        selectedMassInputField.text = num
        # change radius
        chargedObjSelected.display.radius = ((chargedObjSelected.mass) / (((4/3)* pi*sphereMassDensity)))**(1/3)
        chargedObjSelected.displaySelect()
    else:
        selectedMassInputField.text = chargedObjSelected.mass / massScalar

# selected mass slider and input field
def selectedAngleShift(): 
    global chargedObjSelected, selectedAngleSlider, selectedAngleInputField
    selectedAngleInputField.text = selectedAngleSlider.value
    # change angle
    angle = radians(selectedAngleSlider.value)
    chargedObjSelected.display.axis = vec(cos(angle), sin(angle), 0) * mag(chargedObjSelected.display.axis)
    chargedObjSelected.displaySelect()

def selectedAngleInput():
    global chargedObjSelected, selectedAngleSlider, selectedAngleInputField 
    if (selectedAngleInputField.number != None):
        # min max
        num = max(selectedAngleSlider.min, selectedAngleInputField.number)
        num = min(selectedAngleSlider.max, num)
        # set values
        selectedAngleSlider.value = num
        selectedAngleInputField.text = num
        # change angle
        angle = radians(num)
        chargedObjSelected.display.axis = vec(cos(angle), sin(angle), 0) * mag(chargedObjSelected.display.axis)
        chargedObjSelected.displaySelect()
    else:
        selectedAngleInputField.text = degrees(atan2(chargedObjSelected.display.axis.y, chargedObjSelected.display.axis.x))

# fix button
def fixChargedObj():
    global chargedObjSelected
    chargedObjSelected.fixed = not chargedObjSelected.fixed

    # text
    if (chargedObjSelected.fixed):
        fixButton.text = "Unfix"
        # reset velocity and hide vectors
        chargedObjSelected.vel = vec(0, 0, 0)
        chargedObjSelected.hideVec()
    else:
        fixButton.text = "Fix"
        chargedObjSelected.updateDisplay()

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

# trail checkbox
def changeTrailState():
    global chargedObjSelected
    chargedObjSelected.trailState = not chargedObjSelected.trailState
    if (chargedObjSelected.trailState):
        chargedObjSelected.trail.start()
    else:
        chargedObjSelected.trail.stop()

# clear trail button
def clearTrail():
    global chargedObjSelected
    chargedObjSelected.trail.clear()

# delete button
def deleteSelectChargedObj():
    global chargedObjSelected
    deleteChargedObj(chargedObjSelected)
    chargedObjSelected = None
    createCaptionMainScreen()

# another method to allow deleting all charges
def deleteChargedObj(co):
    global cameraFollowedObj
    # hide everything, remove from list, reset chargedObjSelected
    allChargedObjs.remove(co)
    co.display.visible = False
    co.velVec.visible = False
    co.velLabel.visible = False
    co.forceVec.visible = False
    co.forceLabel.visible = False
    co.impulseVec.visible = False
    co.impulseLabel.visible = False
    co.deleted = True
    co.hideSelect()
    for i in range(co.numOfLine):   
            for j in range(electricFieldPrecision):
                co.electricFieldArrows[i][j].visible = False
    if (co == cameraFollowedObj):
        scene.camera.follow(None)
        cameraFollowedObj = None
    co = None

# select position input fields
def updatePosStatSelectScreen():
    global selectPosXInputField, selectPosYInputField
    selectPosXInputField.text = '{:1.3f}'.format(chargedObjSelected.pos.x)
    selectPosYInputField.text = '{:1.3f}'.format(chargedObjSelected.pos.y)

def selectPosXInput():
    global chargedObjSelected, selectPosXInputField
    # change the x value of select position
    if (selectPosXInputField.number != None):
        chargedObjSelected.pos.x = selectPosXInputField.number
        # change position without trail
        chargedObjSelected.trail.stop()
        chargedObjSelected.display.pos.x = chargedObjSelected.pos.x
        if (chargedObjSelected.trailState):
            chargedObjSelected.trail.start()
        chargedObjSelected.updateDisplay()
        updateForceStatSelectScreen()
    else: 
        # invalid input
        selectPosXInputField.text = '{:1.3f}'.format(chargedObjSelected.pos.x)

def selectPosYInput():
    global chargedObjSelected, selectPosYInputField
    # change the y value of select position
    if (selectPosYInputField.number != None):
        chargedObjSelected.pos.y = selectPosYInputField.number
        chargedObjSelected.trail.stop()
        chargedObjSelected.display.pos.y = chargedObjSelected.pos.y
        if (chargedObjSelected.trailState):
            chargedObjSelected.trail.start()
        chargedObjSelected.updateDisplay()
        updateForceStatSelectScreen()
    else: 
        # invalid input
        selectPosYInputField.text = '{:1.3f}'.format(chargedObjSelected.pos.y)

# select velocity input field
def updateVelocityStatsSelectScreen(): 
    global selectedVelXInputField, selectedVelYInputField, selectedVelMagInputField, selectedVelAngleInputField
    selectedVelXInputField.text = '{:1.3f}'.format(chargedObjSelected.vel.x)
    selectedVelYInputField.text = '{:1.3f}'.format(chargedObjSelected.vel.y)
    selectedVelMagInputField.text = '{:1.3f}'.format((mag(chargedObjSelected.vel)))
    selectedVelAngleInputField.text = '{:1.3f}'.format(degrees(atan2(chargedObjSelected.vel.y, chargedObjSelected.vel.x)))

def selectVelXInput():
    global chargedObjSelected, selectedVelXInputField
    # change the x value of select velocity
    if (selectedVelXInputField.number != None):
        chargedObjSelected.vel.x = selectedVelXInputField.number
        chargedObjSelected.createVelVec()
        updateVelocityStatsSelectScreen()
    else: 
        # invalid input
        selectedVelXInputField.text = '{:1.3f}'.format(chargedObjSelected.vel.x)

def selectVelYInput():
    global chargedObjSelected, selectedVelYInputField
    # change the y value of select velocity
    if (selectedVelYInputField.number != None):
        chargedObjSelected.vel.y = selectedVelYInputField.number
        chargedObjSelected.createVelVec()
        updateVelocityStatsSelectScreen()
    else: 
        # invalid input
        selectedVelYInputField.text = '{:1.3f}'.format(chargedObjSelected.vel.y)

def selectVelMagInput():
    global chargedObjSelected, selectedVelMagInputField
    # change the magnitude of select velocity
    if (selectedVelMagInputField.number != None and selectedVelMagInputField.number >= 0):
        angle = atan2(chargedObjSelected.vel.y, chargedObjSelected.vel.x)
        chargedObjSelected.vel.x = selectedVelMagInputField.number * cos(angle)
        chargedObjSelected.vel.y = selectedVelMagInputField.number * sin(angle)
        chargedObjSelected.createVelVec()
        updateVelocityStatsSelectScreen()
    else: 
        # invalid input
        selectedVelMagInputField.text = '{:1.3f}'.format((mag(chargedObjSelected.vel)))
    
def selectVelAngleInput():
    global chargedObjSelected, selectedVelAngleInputField
    # change the angle of select velocity
    if (selectedVelAngleInputField.number != None):
        magnitude = mag(chargedObjSelected.vel)
        chargedObjSelected.vel.x = magnitude * cos(radians(selectedVelAngleInputField.number))
        chargedObjSelected.vel.y = magnitude * sin(radians(selectedVelAngleInputField.number))
        chargedObjSelected.createVelVec()
        updateVelocityStatsSelectScreen()
    else: 
        # invalid input
        selectedVelAngleInputField.text = '{:1.3f}'.format(degrees(atan2(chargedObjSelected.vel.y, chargedObjSelected.vel.x)))

# select force stats
def updateForceStatSelectScreen():
    global selectedChargeForceXYText, selectedChargeForceMAText

    force = chargedObjSelected.calculateNetForce() * 1E9

    selectedChargeForceXYText.text = ("Force: <" + 
                    '{:1.5f}'.format(force.x) + ", " + 
                    '{:1.5f}'.format(force.y) + "> nN") 
    selectedChargeForceMAText.text = ("Force: "+
                    '{:1.5f}'.format((mag(force))) + " nN @ " +
                    '{:1.2f}'.format(degrees(atan2(force.y, force.x))) + " degree")

# endregion 

####################################################################################################

# region Program Runs Here
curRange = scene.range

t = 0

while True:
    rate(numOfRate * time)
    t += 1

    if (playing):
        for chargedObj in allChargedObjs:
            if (chargedObj.type == "Sphere"):
                chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            if (chargedObj.type == "Sphere"):
                chargedObj.applyVel()
        # collision
        # for charge in allChargedObjs:
        #     charge.checkCollision()
        # for charge in allChargedObjs:
        #     charge.collided = []
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

    # update stats in select screen if necessary every second
    if (playing and chargedObjSelected != None and t % (numOfRate * time) == 0):
        updatePosStatSelectScreen()
        if (chargedObjSelected.type == "Sphere"):
            updateVelocityStatsSelectScreen()
            updateForceStatSelectScreen()

    # update force vector because it is possible that mouse is not moving
    if (playing and mouseDown and chargedObjSelected != None and not chargedObjSelected.fixed):
        chargedObjSelected.impulseVec.pos = chargedObjSelected.pos
        chargedObjSelected.impulseVec.axis = getMousePos() - chargedObjSelected.pos 
        chargedObjSelected.createImpulseLabel()

# endregion
