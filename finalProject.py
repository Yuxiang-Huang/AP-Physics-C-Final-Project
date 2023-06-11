# Web VPython 3.2
from vpython import *

####################################################################################################

# region Variables

testMode = False

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
# scalar because there will be units for these variables
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

# runs this many times per second
numOfRate = 2000

# generally for drawing
steps = 3
# for small gap
epsilon = 0.01

electricFieldOpacitySetter = 1

# caption
sliderLength = 450
# for the space before text under a slider
slider20Spaces = "                    "
slider30Spaces = "                              "

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

# each charged obj will do maximum one pos check per run
posChecked = []

def resetPosChecked():
    global posChecked
    posChecked = []

# Math for rescaling (assume height > width)
def setUnits():
    global unitWidth, unitHeight
    unitWidth = 2 * scene.width / scene.height * scene.range / gridPrecision
    unitHeight = 2 * scene.range / gridPrecision

# region electric field for mode 2

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
        potentialGridRows[i].pos = (vec(0, (i - gridPrecision / 2 + 1/2) * unitHeight, 0) 
                                    + vec(scene.camera.pos.x, scene.camera.pos.y, 0))

        # cols
        potentialGridCols[i].size = vec(thickness, unitHeight * gridPrecision, thickness)
        potentialGridCols[i].pos = (vec((i - gridPrecision / 2 + 1/2) * unitWidth, 0, 0)
                                    + vec(scene.camera.pos.x, scene.camera.pos.y, 0))

    # labels
    for i in range(gridPrecision-1):
        for j in range(gridPrecision-1):
            electricPotentialLabels[i][j].pos = (vec((i - gridPrecision / 2 + 1) * unitWidth, 
                                                    (j - gridPrecision / 2 + 1) * unitHeight, 0) 
                                                + vec(scene.camera.pos.x, scene.camera.pos.y, 0))
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
for i in range(steps + 1):
    spawnPosIndicator.append({"pos": vec(0, 0, 0), "color": color.yellow})
spawnPosIndicator.visible = False

#endregion

#endregion

####################################################################################################

# region Classes

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
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
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
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
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
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.black)

            self.trail = attach_trail(self.display, color = color.black)

        # select display
        self.selectDisplay = []
        self.createSelectDisplay()
        allTrails.append(self.trail)
        self.updateDisplay()

    def noTrailUpdateDisplay(self):
        # update pos
        self.trail.stop()
        self.display.pos = self.pos
        if (self.trailState):
            self.trail.start()

        # update select display
        if (self == chargedObjSelected and not self.deleted):
            self.displaySelect()
        
        # update vectors
        if (self.fixed or self.deleted):
            self.hideVec()
        else:
            if (vectorToShow == "Velocity"):
                self.createVelVec()
            elif (vectorToShow == "Force"):
                self.createForceVec()
            else:
                self.hideVec()

    def updateDisplay(self):
        # update pos
        self.display.pos = self.pos

        # update select display
        if (self == chargedObjSelected and not self.deleted):
            self.displaySelect()
        
        # update vectors
        if (self.fixed or self.deleted):
            self.hideVec()
        else:
            if (vectorToShow == "Velocity"):
                self.createVelVec()
            elif (vectorToShow == "Force"):
                self.createForceVec()
            else:
                self.hideVec()

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
            size = scene.range / electricFieldPrecision
            # for every direction
            for i in range(numOfLine):
                # determine starting position
                theta = i * 2 * pi / numOfLine
                curPos = self.pos + vec(cos(theta), sin(theta), 0) * (self.display.radius + epsilon)
                #for every step
                for j in range(electricFieldPrecision):
                    # determine the arrow 
                    electricField = calculateNetElectricField(curPos)
                    arrowLength = norm(electricField) * size

                    self.electricFieldArrows[i][j].visible = True
                    self.electricFieldArrows[i][j].pos = curPos
                    if (self.charge < 0):
                        self.electricFieldArrows[i][j].pos -= arrowLength
                    self.electricFieldArrows[i][j].axis = arrowLength

                    # don't display if too close to a charge
                    if (tooClose(self.electricFieldArrows[i][j])):
                        self.electricFieldArrows[i][j].visible = False

                    # opacity
                    if (electricOpacityMode):
                        self.electricFieldArrows[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
                    else:
                        self.electricFieldArrows[i][j].opacity = 1

                    # next position
                    curPos += arrowLength * self.charge / abs(self.charge)
        else: 
            # hide all electric field arrows
            for i in range(numOfLine):   
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j].visible = False

    def calculateElectricField(self, pos):
        r = pos - self.pos
        if (mag(r) == 0):
            return vec(0, 0, 0)
        return norm(r) * K * self.charge / (mag(r)**2)
    
    def calculateElectricPotential(self, pos):
        r = pos - self.pos
        if (mag(r) == 0):
            return 0
        return  K * self.charge / mag(r)
    
    # endregion

    # region collision body

    def onObj(self, pos):
        return mag(pos - self.pos) <= self.display.radius

    def checkCollision(self):
        # skip if fixed
        if (self.fixed):
            return
        
        for chargedObj in allChargedObjs:
            if (self != chargedObj):
                # skip plates
                if (chargedObj.type == "Plate"):
                    continue
                # colliding distance
                if (mag(self.pos - chargedObj.pos) <= self.display.radius + chargedObj.display.radius):
                    if (not (chargedObj in self.collided)):
                        # collide with fixed obj
                        if (chargedObj.fixed):
                            # find theta (angle between vectors)
                            magnitude = mag(self.vel)
                            dif = chargedObj.pos - self.pos
                            theta = acos(dif.dot(self.vel) / mag(dif) / mag(self.vel))

                            # cross product to figure out add or subtract
                            if (dif.cross(self.vel).z < 0):
                                finalTheta = atan2(dif.y, dif.x) + theta
                            else:
                                finalTheta = atan2(dif.y, dif.x) - theta

                            self.vel = -vec(magnitude * cos(finalTheta), magnitude * sin(finalTheta), 0)

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

                        chargedObj.updateDisplay()

                        # prevent collision calculation twice
                        chargedObj.collided.append(self)
        # update position                
        self.updateDisplay()

    def posCheck(self):
        # each charged obj will do maximum one pos check per run
        if (self in posChecked):
            return
        posChecked.append(self)
        # push away other objs on top of obj
        for co in allChargedObjs:
            if (co != self):
                if (co.type == "Sphere"):
                    # colliding distance
                    if (mag(self.pos - co.pos) < self.display.radius + co.display.radius):
                        dif = self.display.radius + co.display.radius - mag(self.pos - co.pos) 
                        dir = norm(co.pos - self.pos)
                        if (mag(dir) == 0):
                            randomTheta = random() * pi * 2
                            dir = vec(cos(randomTheta), sin(randomTheta), 0)
                        co.pos += dir * dif
                        co.noTrailUpdateDisplay()
                        co.posCheck()
                elif (co.type == "Plate"):
                    # colliding distance
                    dif = pointLineDist(self.pos, co.pos, co.display.axis, co.display.height) - (self.display.radius + co.display.height / 2)
                    if (dif < 0):
                        # using cross product to find colliding point
                        if ((self.pos - co.pos).cross(co.display.axis).z > 0):
                            co.pos -= norm(vec(-co.display.axis.y, co.display.axis.x, 0)) * dif
                        else:
                            co.pos -= norm(vec(co.display.axis.y, -co.display.axis.x, 0)) * dif
                        co.updateDisplay()
                        co.posCheck()
                    
    # endregion 

# endregion

# region Plate

class PlateChargedObj:       
    def __init__(self, spawnCharge, spawnArea, spawnAngle, spawnPos):
        # patch for making sure deleting everything
        self.deleted = False

        # type 
        self.type = "Plate"

        # physics variables
        self.charge = spawnCharge
        self.chargeDensity = max(abs(spawnCharge) / spawnArea, 10 * chargeDensityScalar)
        self.pos = spawnPos
        self.collided = []

        # radius
        spawnLen = sqrt(spawnArea)

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
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.red)

        elif (self.charge < 0):
            # display and vectors
            self.display.texture = negativePlateTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.blue)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.blue)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.blue)
        
        else:
            # display and vectors
            self.display.texture = neutralPlateTexture
            self.velVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.forceVec = arrow(axis = vec(0, 0, 0), color = color.black)
            self.impulseVec = arrow(axis = vec(0, 0, 0), color = color.black)

            # initialize all electric field arrows
            self.electricFieldArrows = [ [0]*electricFieldPrecision for i in range(numOfLine)]
            for i in range(numOfLine):
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j] = arrow(axis = vec(0, 0, 0), color = color.black)

        # not in use but there might be places I forgot to check
        self.trailState = False
        self.trail = attach_trail(self.display)
        self.trail.stop()
        self.fixed = True

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

        self.selectDisplayReset.append(vec(self.pos.x, self.pos.y, self.pos.z))
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
        self.selectDisplayReset.append(vec(self.pos.x, self.pos.y, self.pos.z))
        self.selectDisplayReset.append(rotAngle)

        for c in self.selectDisplay:
            c.visible = True
    
    def hideSelect(self):
        for curve in self.selectDisplay:
            curve.visible = False

    # endregion    

    # region electric field and potential

    def displayElectricField(self):
        if (self.charge == 0):
            return
        
        if (electricFieldMode == 1):
            # determine size
            size = scene.range / electricFieldPrecision
            # for every direction
            for i in range(numOfLine):
                # helper variables
                deltaX = self.display.axis.x / (numOfLine / 2 + 1)
                deltaY = self.display.axis.y / (numOfLine / 2 + 1)
                 # determine starting position
                curPos = self.pos - self.display.axis / 2 + vec(deltaX, deltaY, 0)
                curPos += vec(deltaX * (i % (numOfLine / 2)), deltaY * (i % (numOfLine / 2)), 0)
                if (i >= numOfLine / 2):
                    curPos += (self.display.height / 2 + epsilon) / 2 * norm(vec(-self.display.axis.y, self.display.axis.x, 0))
                else:
                    curPos += (self.display.height / 2 + epsilon) / 2 * norm(vec(self.display.axis.y, self.display.axis.x, 0))

                #for every step
                for j in range(electricFieldPrecision):
                    # determine the arrow 
                    electricField = calculateNetElectricField(curPos)
                    arrowLength = norm(electricField) * size

                    self.electricFieldArrows[i][j].visible = True
                    self.electricFieldArrows[i][j].pos = curPos
                    if (self.charge < 0):
                        self.electricFieldArrows[i][j].pos -= arrowLength
                    self.electricFieldArrows[i][j].axis = arrowLength

                    # don't display if too close to a charge
                    if (tooClose(self.electricFieldArrows[i][j])):
                        self.electricFieldArrows[i][j].visible = False

                    # opacity
                    if (electricOpacityMode):
                        self.electricFieldArrows[i][j].opacity = mag(electricField) / electricFieldOpacitySetter
                    else:
                        self.electricFieldArrows[i][j].opacity = 1

                    # next position
                    curPos += arrowLength * self.charge / abs(self.charge)
        else: 
            # hide all electric field arrows
            for i in range(numOfLine):   
                for j in range(electricFieldPrecision):
                    self.electricFieldArrows[i][j].visible = False

    def calculateElectricField(self, pos):
        if (self.charge == 0):
            return vec(0, 0, 0)
        
        electricField = vec(0, 0, 0)
        # helper variables
        deltaX = self.display.axis.x / (deltaFactor - 1)
        deltaY = self.display.axis.y / (deltaFactor - 1)
        deltaZ = self.display.width / (deltaFactor - 1)
        startPos = self.pos - self.display.axis / 2
        # loop to find pos of each dA
        for i in range(deltaFactor):
            for j in range(deltaFactor):
                curPos = vec(startPos.x + deltaX * i, startPos.y + deltaY * i, - self.display.width / 2 + deltaZ * j)
                # dE = norm(r) * K * (dA * charge density) / r^2
                r = pos - curPos
                if (mag(r) > 0):
                    dA = self.display.length / deltaFactor * self.display.width / deltaFactor
                    electricField += norm(r) * K * (dA * self.chargeDensity) / (mag(r)**2) * self.charge / abs(self.charge)
        return electricField
    
    def calculateElectricPotential(self, pos):
        if (self.charge == 0):
            return 0
        
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
                if (mag(r) > 0):
                    dA = self.display.length / deltaFactor * self.display.width / deltaFactor 
                    electricFieldPotential += K * (dA * self.chargeDensity) / mag(r) * self.charge / abs(self.charge)
        return electricFieldPotential
    
    # endregion

    # region collision body

    def onObj(self, pos):
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
            v1 = vertices[i] - pos
            v2 = vertices[(i + 1) % 4] - pos
            if v1.cross(v2).z < 0:
                return False
        return True

    def checkCollision(self):
        for co in allChargedObjs:
            if (co.type == "Sphere"):
                # using cross product to find colliding point
                if ((co.pos - self.pos).cross(self.display.axis).z > 0):
                    collidingPoint = co.pos + norm(vec(-self.display.axis.y, self.display.axis.x, 0)) * co.display.radius
                    # colliding distance
                    if (self.onObj(collidingPoint)):
                        angleIn = acos(dot(co.vel, self.display.axis) / mag(co.vel) / mag(self.display.axis))
                        magnitude = mag(co.vel)
                        # subtract angle
                        finalAngle = atan2(self.display.axis.y, self.display.axis.x) - angleIn
                        co.vel = vec(magnitude * cos(finalAngle), magnitude * sin(finalAngle), 0)
                else:
                    collidingPoint = co.pos + norm(vec(self.display.axis.y, -self.display.axis.x, 0)) * co.display.radius
                    # colliding distance
                    if (self.onObj(collidingPoint)):
                        angleIn = acos(dot(co.vel, self.display.axis) / mag(co.vel) / mag(self.display.axis))
                        magnitude = mag(co.vel)
                        # add angle
                        finalAngle = atan2(self.display.axis.y, self.display.axis.x) + angleIn
                        co.vel = vec(magnitude * cos(finalAngle), magnitude * sin(finalAngle), 0)
                
                # edge detection
                if (co.onObj(self.pos + self.display.axis / 2)):
                    co.vel = - co.vel

    def posCheck(self):
        # each charged obj will do maximum one pos check per run
        if (self in posChecked):
            return
        posChecked.append(self)
        # push away other objs on top of obj
        for co in allChargedObjs:
            if (co != self):
                if (co.type == "Sphere"):
                    # colliding distance
                    dif = pointLineDist(co.pos, self.pos, self.display.axis, self.display.height) - (co.display.radius + self.display.height / 2)
                    if (dif < 0):
                        # using cross product to find colliding point
                        if ((co.pos - self.pos).cross(self.display.axis).z > 0):
                            co.pos += norm(vec(-self.display.axis.y, self.display.axis.x, 0)) * dif
                        else:
                            co.pos += norm(vec(self.display.axis.y, -self.display.axis.x, 0)) * dif
                        co.noTrailUpdateDisplay()
                        co.posCheck()
    
    # endregion

# endregion

def pointLineDist(pointPos, linePos, lineAxis, height):
    # too far away to draw perpendicular case
    if (mag(pointPos - linePos) > mag(lineAxis/2)):
        # two endpoints (subtract by half the height to prevent counting it when calculating collision)
        return min(mag(linePos + lineAxis / 2 - pointPos), mag(linePos - lineAxis / 2 - pointPos)) + height / 2
    else:    
        # vector way to find distance between point and line from multi
        v0 = linePos - pointPos
        return mag(v0.cross(lineAxis)) / mag(lineAxis)

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

# endregion

def test():
    global quantumTunneling
    quantumTunneling = True
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(5,5,0), vec(-1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 5*chargeScalar, vec(2.5,0,0), vec(0, 1, 0), False))

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
        # shell theorem
        if (co.type == "Sphere"):
            if (mag(co.pos - exclude.pos) > (co.display.radius + exclude.display.radius)):
                electricField += co.calculateElectricField(pos)
        else:
            electricField += co.calculateElectricField(pos)
    return electricField

def tooClose(arrow):
    for co in allChargedObjs:
        stepToCheck = 2
        # check the middle point on the arrow
        curPos = arrow.pos + arrow.axis /4
        for i in range(round(stepToCheck) + 1):
            if (co.onObj(curPos)):
                return True
            curPos += arrow.axis / 2 / stepToCheck 
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
    for i in range(steps + 1):
        theta = i * 2 * pi / steps + pi / 6
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
    
    # after set position
    if (not playing and chargedObjToDrag != None and chargedObjSelected != chargedObjToDrag):
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
            if (not playing and chargedObjToDrag != None):
                # set position
                mousePos = getMousePos()
                chargedObjToDrag.pos = mousePos + dragOffset
                chargedObjToDrag.updateDisplay()

                # don't display trail when move
                chargedObjToDrag.trail.stop()

                chargedObjToDrag.posCheck()
                resetPosChecked()

                # could have impacted electric field and potential in the spawn screen
                if (spawnPos != None):
                    updateSpawnScreen()

                # update the force in select screen
                if (chargedObjSelected != None and chargedObjSelected.type == "Sphere"):
                    updateForceStatSelectScreen()
        else:
            # common conditions: not playing, dragging 
            if not playing and chargedObjToDrag != None:
                # additional contiditional for velocity vector: sphere, and obj not fixed
                if (chargedObjToDrag.type == "Sphere" and not chargedObjToDrag.fixed):
                    # set vector to shownmode to velocity
                    global vectorToShow, vectorMenu
                    for co in allChargedObjs:
                        if (co.type == "Sphere" and not co.fixed):
                            co.createVelVec()
                            if (vectorToShow == "Force"):
                                co.forceVec.visible = False
                                co.forceLabel.visible = False
                    vectorToShow = "Velocity"
                    vectorMenu.selected = vectorToShow

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
                # angle for plate
                elif (chargedObjToDrag.type == "Plate"):
                    # find angle to mouse
                    difVec = getMousePos() - chargedObjToDrag.pos
                    angle = round(degrees(atan2(difVec.y, difVec.x)))
                    angleModified(angle % 180)

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
    instructionButton = button(text="README", bind = displayInstructionPage)

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
    timeText = wtext(text = "<center>Time in program for every second in real life: " + str(time) + "s</center>")

    # update timer
    global updateTimeSlider, updateTimeText
    scene.append_to_caption("\n")
    updateTimeSlider = slider(bind=updateTimeShift, min = 0.1, max = 2, value = updateTime, step = 0.1, length = sliderLength) 
    scene.append_to_caption("\n")
    updateTimeText = wtext(text = "<center>Physical variables update every " + str(updateTime) + "s</center>")

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
playing = True

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
    scene.append_to_caption("\n\n")
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

# time slider
updateTime = 0.1

def updateTimeShift():
    global updateTime, updateTimeText
    updateTime = updateTimeSlider.value
    updateTimeText.text = "<center>Physical variables update every " + str(updateTime) + "s</center>"

# vector menu
vectorToShow = "Neither"

def selectVector():
    global vectorToShow
    # hide earlier vector
    for co in allChargedObjs:
        if (co.type == "Sphere"):
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
    scene.append_to_caption("   Spawn Object Menu: ")
    chargeMenu = menu(choices = ["Sphere", "Plate"], bind = selectSpawnChargeObj, selected = spawnType) 
    
    # spawn charge slider and input field
    global spawnChargeSlider, spawnChargeInputField
    scene.append_to_caption("\n\n")
    if (chargeMenu.selected == "Sphere"):
        spawnChargeSlider = slider(bind = spawnChargeShift, min = -5, max = 5, value = spawnChargeSphere / chargeScalar, step = 0.1, length = sliderLength)
    elif (chargeMenu.selected == "Plate"):
        spawnChargeSlider = slider(bind = spawnChargeShift, min = -5, max = 5, value = spawnChargePlate / chargeScalar, step = 0.1, length = sliderLength)
    scene.append_to_caption("\n" + slider30Spaces + "Charge: ")
    spawnChargeInputField = winput(bind = spawnChargeInput, text = spawnChargeSlider.value, width = 35)
    scene.append_to_caption(" nC")

    if (chargeMenu.selected == "Plate"):
        if (spawnChargePlate == 0):
            # select area slider and input field
            global spawnAreaSlider, spawnAreaInputField
            scene.append_to_caption("\n\n")
            spawnAreaSlider = slider(bind = spawnAreaShift, min = 4, max = 500, value = spawnArea, step = 1, length = sliderLength)
            scene.append_to_caption("\n" + slider30Spaces + "Area: ")
            spawnAreaInputField = winput(bind = spawnAreaInput, text = spawnAreaSlider.value, width = 35)
            scene.append_to_caption(" m^2")

            spawnAreaSlider.disabled = playing
            spawnAreaInputField.disabled = playing
        else:
        # select charge density slider and input field
            global spawnChargeDensitySlider, spawnChargeDensityInputField
            scene.append_to_caption("\n\n")
            spawnChargeDensitySlider = slider(bind = spawnChargeDensityShift, min = 10, max = 25, value = spawnChargeDensity / chargeDensityScalar, step = 1, length = sliderLength)
            scene.append_to_caption("\n" + slider20Spaces + "Charge Density: ")
            spawnChargeDensityInputField = winput(bind = spawnChargeDensityInput, text = spawnChargeDensitySlider.value, width = 35)
            scene.append_to_caption(" pC/m^2")

            spawnChargeDensitySlider.disabled = playing
            spawnChargeDensityInputField.disabled = playing

    # spawn mass slider and input field
    global spawnMassSlider, spawnMassInputField
    if (chargeMenu.selected == "Sphere"):
        scene.append_to_caption("\n\n")
        spawnMassSlider = slider(bind = spawnMassShift, min = 1, max = 5, value = spawnMass / massScalar, step = 0.1, length = sliderLength)
        scene.append_to_caption("\n" + slider30Spaces + "Mass: ")
        spawnMassInputField = winput(bind = spawnMassInput, text = spawnMassSlider.value, width = 35)
        scene.append_to_caption(" * 10^-9 Kg")

    # spawn angle slider and input field
    global spawnAngleSlider, spawnAngleInputField
    if (chargeMenu.selected == "Plate"):
        scene.append_to_caption("\n\n")
        spawnAngleSlider = slider(bind = spawnAngleShift, min = 0, max = 180, value = spawnAngle, step = 1, length = sliderLength)
        scene.append_to_caption("\n" + slider30Spaces + "Angle: ")
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
spawnType = "Sphere"

def selectSpawnChargeObj():
    global spawnType
    spawnType = chargeMenu.selected
    createCaptionSpawnScreen()

# spawn charge slider and input field
spawnChargeSphere = chargeScalar
spawnChargePlate = chargeScalar

def plateSpawnChargeCheck():
    global spawnChargePlate, spawnArea
    # for 0 charge case
    num = spawnChargeSlider.value
    # change to 0 charge
    if (spawnChargePlate != 0 and num == 0):
        # change charge density to length
        spawnChargePlate = num * chargeScalar
        createCaptionSpawnScreen()
    # change from 0 charge
    elif (spawnChargePlate == 0 and num != 0):
        spawnChargePlate = num * chargeScalar  
        spawnArea = round(spawnChargePlate / spawnChargeDensity)
        createCaptionSpawnScreen()
    # not related to 0 charge
    elif (spawnChargePlate != 0 and num != 0):
        spawnChargePlate = num * chargeScalar  
        spawnArea = round(spawnChargePlate / spawnChargeDensity)

def spawnChargeShift():
    global spawnChargeSphere, spawnChargePlate, spawnChargeInputField
    spawnChargeInputField.text = spawnChargeSlider.value
    if (chargeMenu.selected == "Sphere"):
        spawnChargeSphere = spawnChargeSlider.value * chargeScalar    
    elif (chargeMenu.selected == "Plate"):
        plateSpawnChargeCheck()

def spawnChargeInput():
    global spawnChargeSphere, spawnChargePlate, spawnChargeSlider, spawnChargeInputField
    if (spawnChargeInputField.number != None):
        # min max and restrain on magnitude
        num = max(spawnChargeSlider.min, spawnChargeInputField.number)
        num = min(spawnChargeSlider.max, num)
        if (num != 0):
            num = max(0.1, abs(num)) * round(abs(num) / num)
        # set values
        spawnChargeSlider.value = num
        spawnChargeInputField.text = num
        if (chargeMenu.selected == "Sphere"):
            spawnChargeSphere = num * chargeScalar
        elif (chargeMenu.selected == "Plate"):
            plateSpawnChargeCheck()
    else:
        # invalid input
        if (chargeMenu.selected == "Sphere"):
            spawnChargeInputField.text = spawnChargeSphere / chargeScalar
        elif (chargeMenu.selected == "Plate"):
            spawnChargeInputField.text = spawnChargePlate / chargeScalar

# spawn charge density slider and input field
spawnChargeDensity = 10 * chargeDensityScalar

def spawnChargeDensityShift():
    global spawnChargeDensity, spawnArea, spawnChargeDensityInputField
    spawnChargeDensity = spawnChargeDensitySlider.value * chargeDensityScalar    
    spawnArea = spawnChargePlate / spawnChargeDensity
    spawnChargeDensityInputField.text = spawnChargeDensitySlider.value

def spawnChargeDensityInput():
    global spawnChargeDensity, spawnArea, spawnChargeDensitySlider, spawnChargeDensityInputField
    if (spawnChargeDensityInputField.number != None):
        # min max
        num = max(spawnChargeDensitySlider.min, spawnChargeDensityInputField.number)
        num = min(spawnChargeDensitySlider.max, num)
        # set values
        spawnChargeDensity = num * chargeDensityScalar
        spawnArea = spawnChargePlate / spawnChargeDensity
        spawnChargeDensitySlider.value = num
        spawnChargeDensityInputField.text = num
    else:
        # invalid input
        spawnChargeDensityInputField.text = spawnChargeDensity / chargeDensityScalar

# spawn area slider and input field
spawnArea = 100

def spawnAreaShift():
    global spawnArea, spawnAreaInputField
    spawnArea = spawnAreaSlider.value
    spawnAreaInputField.text = spawnAreaSlider.value

def spawnAreaInput():
    global spawnArea, spawnAreaSlider, spawnAreaInputField
    if (spawnAreaInputField.number != None):
        # min max
        num = max(spawnAreaSlider.min, spawnAreaInputField.number)
        num = min(spawnAreaSlider.max, num)
        # set values
        spawnArea = num
        spawnAreaSlider.value = num
        spawnAreaInputField.text = num
    else:
        # invalid input
        spawnAreaInputField.text = spawnArea

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
        allChargedObjs.append(PlateChargedObj(spawnChargePlate, spawnArea, spawnAngle, spawnPos))
    # prevent overlap
    allChargedObjs[-1].posCheck()
    resetPosChecked()
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
    scene.append_to_caption("\n" + slider30Spaces + "Charge: ")
    selectedChargeInputField = winput(bind = selectedChargeInput, text = selectedChargeSlider.value, width = 35)
    scene.append_to_caption(" nC")

    selectedChargeSlider.disabled = playing
    selectedChargeInputField.disabled = playing

    # for plate
    if (chargedObjSelected.type == "Plate"):
        if (chargedObjSelected.charge == 0):
            # select area slider and input field
            global selectedAreaSlider, selectedAreaInputField
            scene.append_to_caption("\n\n")
            selectedAreaSlider = slider(bind = selectedAreaShift, min = 4, max = 500, value = round(chargedObjSelected.display.length *  chargedObjSelected.display.width), step = 1, length = sliderLength)
            scene.append_to_caption("\n" + slider30Spaces + "Area: ")
            selectedAreaInputField = winput(bind = selectedAreaInput, text = selectedAreaSlider.value, width = 35)
            scene.append_to_caption(" m^2")

            selectedAreaSlider.disabled = playing
            selectedAreaInputField.disabled = playing
        else:
        # select charge density slider and input field
            global selectedChargeDensitySlider, selectedChargeDensityInputField
            scene.append_to_caption("\n\n")
            selectedChargeDensitySlider = slider(bind = selectedChargeDensityShift, min = 10, max = 25, value = round(chargedObjSelected.chargeDensity / chargeDensityScalar), step = 1, length = sliderLength)
            scene.append_to_caption("\n" + slider20Spaces + "Charge Density: ")
            selectedChargeDensityInputField = winput(bind = selectedChargeDensityInput, text = selectedChargeDensitySlider.value, width = 35)
            scene.append_to_caption(" pC/m^2")

            selectedChargeDensitySlider.disabled = playing
            selectedChargeDensityInputField.disabled = playing

    # select mass slider and input field
    global selectedMassSlider, selectedMassInputField
    if (chargedObjSelected.type == "Sphere"):
        scene.append_to_caption("\n\n")
        selectedMassSlider = slider(bind = selectedMassShift, min = 1, max = 5, value = chargedObjSelected.mass / massScalar, step = 0.1, length = sliderLength)
        scene.append_to_caption("\n" + slider30Spaces + "Mass: ")
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
        scene.append_to_caption("\n" + slider30Spaces + "Angle: ")
        selectedAngleInputField = winput(bind = selectedAngleInput, text = selectedAngleSlider.value, width = 35)
        scene.append_to_caption(" degrees")

        selectedAngleSlider.disabled = playing
        selectedAngleInputField.disabled = playing

    # need for both types but not in the same place...
    global deleteButton
        
    # for sphere
    if (chargedObjSelected.type == "Sphere"):
        # fix button
        global fixCheckBox
        scene.append_to_caption("\n\n   ")
        fixCheckBox = checkbox(text = "Fixed", bind=fixChargedObj, checked = chargedObjSelected.fixed)

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
        num = selectedChargeSlider.value
        # change the texture
        if (num > 0 and chargedObjSelected.charge <= 0):
            if (chargedObjSelected.fixed):
                chargedObjSelected.display.texture = fixedPositiveSphereTexture
            else:
                chargedObjSelected.display.texture = positiveSphereTexture
        elif (num < 0 and chargedObjSelected.charge >= 0): 
            if (chargedObjSelected.fixed):
                chargedObjSelected.display.texture = fixedNegativeSphereTexture
            else:
                chargedObjSelected.display.texture = negativeSphereTexture
        elif (num == 0 and chargedObjSelected.charge != 0):
            if (chargedObjSelected.fixed):
                chargedObjSelected.display.texture = fixedNeutralSphereTexture
            else:
                chargedObjSelected.display.texture = neutralSphereTexture

        chargedObjSelected.charge = num * chargeScalar

        # colors    
        if (chargedObjSelected.charge > 0):
            curColor = color.red
        elif (chargedObjSelected.charge < 0):
            curColor = color.blue
        else:
            curColor = color.black

        chargedObjSelected.velVec.color = curColor
        chargedObjSelected.impulseVec.color = curColor

        for i in range(numOfLine):
            for j in range(electricFieldPrecision):
                chargedObjSelected.electricFieldArrows[i][j].color = curColor

        chargedObjSelected.trail.color = curColor

        # update force
        updateForceStatSelectScreen()
    elif (chargedObjSelected.type == "Plate"):
        num = selectedChargeSlider.value
        # change the texture
        if (chargedObjSelected.charge <= 0 and num > 0):
            chargedObjSelected.display.texture = positivePlateTexture
        elif (chargedObjSelected.charge >= 0 and num < 0): 
            chargedObjSelected.display.texture = negativePlateTexture
        elif (chargedObjSelected.charge != 0 and num == 0): 
            chargedObjSelected.display.texture = neutralPlateTexture

        # change to 0 charge
        if (chargedObjSelected.charge != 0 and num == 0):
            # change charge density to length
            chargedObjSelected.charge = num * chargeScalar
            createCaptionSelectScreen()
        # change from 0 charge
        elif (chargedObjSelected.charge == 0 and num != 0):
            chargedObjSelected.charge = num * chargeScalar  
            len = sqrt(abs(chargedObjSelected.charge) / chargedObjSelected.chargeDensity)
            chargedObjSelected.display.length = len
            chargedObjSelected.display.height = len / plateHeightFactor
            chargedObjSelected.display.width = len
            chargedObjSelected.displaySelect()
            createCaptionSelectScreen()
        # not related to 0 charge
        elif (chargedObjSelected.charge != 0 and num != 0):
            chargedObjSelected.charge = num * chargeScalar  
            len = sqrt(abs(chargedObjSelected.charge) / chargedObjSelected.chargeDensity)
            chargedObjSelected.display.length = len
            chargedObjSelected.display.height = len / plateHeightFactor
            chargedObjSelected.display.width = len
            chargedObjSelected.displaySelect()
    # prevent overlap
    chargedObjSelected.posCheck()
    resetPosChecked()

    # update force vectors
    if (vectorToShow == "Force"):
        for co in allChargedObjs:
            if (co.type == "Sphere"):
                co.createForceVec()

def selectedChargeShift(): 
    global chargedObjSelected, selectedChargeSlider, selectedChargeInputField    
    selectedChargeInputField.text = selectedChargeSlider.value
    selectedChargeModified()
    
def selectedChargeInput():
    global chargedObjSelected, selectedChargeSlider, selectedChargeInputField
    if (selectedChargeInputField.number != None):
        # min max and restrain on magnitude
        num = max(selectedChargeSlider.min, selectedChargeInputField.number)
        num = min(selectedChargeSlider.max, num)
        if (num != 0):
            num = max(0.1, abs(num)) * round(abs(num) / num)
        
        # set values
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
    # prevent overlap
    chargedObjSelected.posCheck()
    resetPosChecked()
    # update force vectors
    if (vectorToShow == "Force"):
        for co in allChargedObjs:
            if (co.type == "Sphere"):
                co.createForceVec()

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
        chargedObjSelected.posCheck()
        resetPosChecked()
        # update force vectors
        if (vectorToShow == "Force"):
            for co in allChargedObjs:
                if (co.type == "Sphere"):
                    co.createForceVec()
    else:
        selectedChargeDensityInputField.text = chargedObjSelected.chargeDensity / chargeDensityScalar

# selected area slider and input field
def selectedAreaShift(): 
    global chargedObjSelected, selectedAreaSlider, selectedAreaInputField 
    selectedAreaInputField.text = selectedAreaSlider.value
    # change length
    len = sqrt(selectedAreaSlider.value)
    chargedObjSelected.display.size = vec(len, len / plateHeightFactor, len)
    chargedObjSelected.displaySelect()

def selectedAreaInput():
    global chargedObjSelected, selectedAreaSlider, selectedAreaInputField 
    if (selectedAreaInputField.number != None):
        # min max
        num = max(selectedAreaSlider.min, selectedAreaInputField.number)
        num = min(selectedAreaSlider.max, num)
        # set values
        selectedAreaSlider.value = num
        selectedAreaInputField.text = num
        # change length
        len = sqrt(selectedAreaSlider.value)
        chargedObjSelected.display.size = vec(len, len / plateHeightFactor, len)
        chargedObjSelected.displaySelect()
    else:
        selectedAreaInputField.text = chargedObjSelected.display.length

# selected mass slider and input field
def selectedMassShift(): 
    global chargedObjSelected, selectedMassSlider, selectedMassInputField
    chargedObjSelected.mass = selectedMassSlider.value * massScalar   
    selectedMassInputField.text = selectedMassSlider.value
    # change radius
    chargedObjSelected.display.radius = ((chargedObjSelected.mass) / (((4/3)* pi*sphereMassDensity)))**(1/3)
    chargedObjSelected.displaySelect()
    # prevent overlap
    chargedObjSelected.posCheck()
    resetPosChecked()

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
        # prevent overlap
        chargedObjSelected.posCheck()
        resetPosChecked()
    else:
        selectedMassInputField.text = chargedObjSelected.mass / massScalar

# selected angle slider and input field
def selectedAngleShift(): 
    global chargedObjSelected, selectedAngleSlider, selectedAngleInputField
    selectedAngleInputField.text = selectedAngleSlider.value
    # change angle
    angle = radians(selectedAngleSlider.value)
    chargedObjSelected.display.axis = vec(cos(angle), sin(angle), 0) * mag(chargedObjSelected.display.axis)
    chargedObjSelected.displaySelect()
    # prevent overlap
    chargedObjSelected.posCheck()
    resetPosChecked()

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
        # prevent overlap
        chargedObjSelected.posCheck()
        resetPosChecked()
    else:
        selectedAngleInputField.text = degrees(atan2(chargedObjSelected.display.axis.y, chargedObjSelected.display.axis.x))

# use for mouse control
def angleModified(angle):
    global chargedObjSelected, selectedAngleInputField, selectedAngleSlider
    # slider and input field
    selectedAngleSlider.value = angle
    selectedAngleInputField.text = angle
    # change display
    chargedObjSelected.display.axis = vec(cos(radians(angle)), sin(radians(angle)), 0) * mag(chargedObjSelected.display.axis)
    chargedObjSelected.displaySelect()
    # prevent overlap
    chargedObjSelected.posCheck()
    resetPosChecked()
    # update force vectors
    if (vectorToShow == "Force"):
        for co in allChargedObjs:
            if (co.type == "Sphere"):
                co.createForceVec()

# fix button
def fixChargedObj():
    global chargedObjSelected
    chargedObjSelected.fixed = not chargedObjSelected.fixed

    # text
    if (chargedObjSelected.fixed):
        # reset velocity and hide vectors
        chargedObjSelected.vel = vec(0, 0, 0)
        chargedObjSelected.hideVec()
    else:
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
    if (co.type == "Sphere"):
        co.velVec.visible = False
        co.velLabel.visible = False
        co.forceVec.visible = False
        co.forceLabel.visible = False
        co.impulseVec.visible = False
        co.impulseLabel.visible = False
    co.deleted = True
    co.hideSelect()
    for i in range(numOfLine):   
            for j in range(electricFieldPrecision):
                co.electricFieldArrows[i][j].visible = False
    if (co == cameraFollowedObj):
        scene.camera.follow(None)
        cameraFollowedObj = None
    co = None
    # update force vectors
    if (vectorToShow == "Force"):
        for co in allChargedObjs:
            if (co.type == "Sphere"):
                co.createForceVec()

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
        if (chargedObjSelected.type == "Sphere"):
            chargedObjSelected.noTrailUpdateDisplay()
            updateForceStatSelectScreen()
        elif (chargedObjSelected.type == "Plate"):
            chargedObjSelected.display.pos.x = chargedObjSelected.pos.x
            chargedObjSelected.updateDisplay()
        chargedObjSelected.posCheck()
    else: 
        # invalid input
        selectPosXInputField.text = '{:1.3f}'.format(chargedObjSelected.pos.x)

def selectPosYInput():
    global chargedObjSelected, selectPosYInputField
    # change the y value of select position
    if (selectPosYInputField.number != None):
        chargedObjSelected.pos.y = selectPosYInputField.number
        if (chargedObjSelected.type == "Sphere"):
            chargedObjSelected.noTrailUpdateDisplay()
            updateForceStatSelectScreen()
        elif (chargedObjSelected.type == "Plate"):
            chargedObjSelected.display.pos.y = chargedObjSelected.pos.y
            chargedObjSelected.updateDisplay()
        chargedObjSelected.posCheck()
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

# region Intro and Preset Screen

# start simulation button
def startSimulation():
    # also use in intro screen random charge configuration
    if (not secondScreen):
        return
    
    # bind events
    scene.bind('click', clicked)
    scene.bind('mousedown', onMouseDown)
    scene.bind('mouseup', onMouseUp)
    scene.bind('mousemove', onMouseMove)
    
    global playing, secondScreenText
    playing = False
    secondScreenText.visible = False

    scene.userzoom = True

    # initialize the electric field arrows and grids
    setUnits()

    createElectricFieldArrowsAll()
    setElectricFieldArrowsAll()

    createPotentialGrid()
    setElectricPotentialGrid()
    
    createCaptionMainScreen()

quantumTunneling = False

configurationList = []

# region presets
def dipolePreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5,0,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-5, 0, 0) , vec(0, 0, 0), False))
configurationList.append(dipolePreset)

def threeChargePreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -1.5*chargeScalar, vec(-5*cos(pi/6),-5*sin(pi/6),0), vec(0, 0, 0), False))
configurationList.append(threeChargePreset)

def helixPreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-1.5,10,0), vec(.25, -2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(1.5,10,0), vec(-.25, -2, 0), False))
configurationList.append(helixPreset)

def helixGunPreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-15,1.5,0), vec(2, -.25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-15,-1.5,0), vec(2, .25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,1.5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,-1.5,0), vec(0, 0, 0), False))
configurationList.append(helixGunPreset)  

def yPreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(0,5,0), vec(1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(.1*massScalar, 0, vec(4.5,.5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(10,5,0), vec(-1, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(.1*massScalar, 0, vec(0,-5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(.1*massScalar, 0, vec(-.5,5.5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(.1*massScalar, 0, vec(10.5,5.5,0), vec(0, 0, 0), True))
configurationList.append(yPreset)

def jPreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(-5,5,0), vec(.3, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(-6,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(6,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(0, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -.25*chargeScalar, vec(2.5,-4,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -.25*chargeScalar, vec(-3.5,-7,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(-4.572,.584,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 0, vec(0,5.95,0), vec(0, 0, 0), True))
configurationList.append(jPreset)

def chargeTrampolinePreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5,5,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,0,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(5,0,0), vec(0, 0, 0), False))
configurationList.append(chargeTrampolinePreset)

def figureEightPreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,0,0), vec(1,1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, 1.1*chargeScalar, vec(0,-5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, 1.1*chargeScalar, vec(0,5,0), vec(0, 0, 0), True))
configurationList.append(figureEightPreset)

def circularOrbitPreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,0,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(sqrt((9E9*1E-9*1E-9)/(5*1E-9)), 0, 0), False))
configurationList.append(circularOrbitPreset)

#same right now as circular orbit, but this is unfixed and the circular orbit will be fixed
def loopWavePreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-15,0,0), vec(0, 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-15,5,0), vec(sqrt((9E9*1E-9*1E-9)/(5*1E-9)), 0, 0), False))
configurationList.append(loopWavePreset)

def collisionWavePreset():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-5.675+15+5,-3.158+10+4,0), vec(-1.991, -.786, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -1.5*chargeScalar, vec(-4.467+15+5,-4.987+10+4,0), vec(.273, -.382, 0), False))
configurationList.append(collisionWavePreset)

def elipticalObritPreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -5*chargeScalar, vec(0,5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(5,0,0), vec(-.5, 2.55, 0), False))
configurationList.append(elipticalObritPreset)

#(self, spawnCharge, spawnArea, spawnAngle, spawnPos)
def parallelPlatesPreset():
    startSimulation()
    allChargedObjs.append(PlateChargedObj(chargeScalar, 100, 90, vec(5, 0, 0)))
    allChargedObjs.append(PlateChargedObj(-chargeScalar, 100, 90, vec(-5, 0, 0)))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(0, -1, 0), False))
configurationList.append(parallelPlatesPreset)
  
def faradayBucketPreset(): 
    startSimulation()
    allChargedObjs.append(PlateChargedObj(-chargeScalar, 100, 0, vec(0, -7, 0)))
    allChargedObjs.append(PlateChargedObj(-chargeScalar, 100, 90, vec(-5, -2, 0)))
    allChargedObjs.append(PlateChargedObj(-chargeScalar, 100, 90, vec(5, -2, 0)))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(0, 0, 0), False))
configurationList.append(faradayBucketPreset)   

def plateTunnelPreset():
    startSimulation()
    allChargedObjs.append(PlateChargedObj(5*chargeScalar, 5*chargeScalar / (25 * chargeDensityScalar), 90, vec(3, 0, 0)))
    allChargedObjs.append(PlateChargedObj(-5*chargeScalar, 5*chargeScalar / (25 * chargeDensityScalar), 90, vec(-3, 0, 0)))
    allChargedObjs.append(SphereChargedObj(massScalar, 0.5*chargeScalar, vec(-1,10,0), vec(0, -1, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -0.5*chargeScalar, vec(1,10,0), vec(0, -1, 0), False))
configurationList.append(plateTunnelPreset)

def chargeTrampoline2Preset():
    startSimulation()
    allChargedObjs.append(PlateChargedObj(5*chargeScalar, 5*chargeScalar / (25 * chargeDensityScalar), 45, vec(0, 0, 0)))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(2.5,-2.5,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -7.5*chargeScalar, vec(7.5,2.5,0), vec(0, -1, 0), False))
configurationList.append(chargeTrampoline2Preset)

def flowerPreset():
    startSimulation()
    num = 50
    radius = 10
    # ring of charge
    for i in range(num):
        theta = 2 * pi / num * i
        allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(cos(theta) * radius, sin(theta) * radius, 0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0,0,0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(0,5,0), vec(sqrt((9E9*1E-9*1E-9)/(5*1E-9)), 0, 0), False))
configurationList.append(flowerPreset)

def fourHelixPreset(): 
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-1.5,10,0), vec(.25, -2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(1.5,10,0), vec(-.25, -2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(1.5,-10,0), vec(-.25, 2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-1.5,-10,0), vec(.25, 2, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(10,1.5,0), vec(-2, -.25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(10,-1.5,0), vec(-2, .25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, vec(-10,1.5,0), vec(2, -.25, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(-10,-1.5,0), vec(2, .25, 0), False))
configurationList.append(fourHelixPreset)

def orbits():
    startSimulation()
    allChargedObjs.append(SphereChargedObj(massScalar, 5*chargeScalar, vec(0, 0, 0), vec(0, 0, 0), True))
    allChargedObjs.append(SphereChargedObj(massScalar, -0.1 * chargeScalar, vec(2, 0, 0), vec(0, 1.5, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -0.1 * chargeScalar, vec(-4, 0, 0), vec(0, -sqrt(1.125), 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -0.1 * chargeScalar, vec(0, 6, 0), vec(-sqrt(0.75), 0, 0), False))
    allChargedObjs.append(SphereChargedObj(massScalar, -0.1 * chargeScalar, vec(0, -8, 0), vec(0.75, 0, 0), False))
configurationList.append(orbits)

def mineField():
    startSimulation()
    # 5 - 10 postive charges
    num = round(random() * 5) + 5
    len = 10
    maxVel = 5
    minVel = 2
    # positive charge
    for i in range(num):
        randomPos = vec(random() * len - len / 2, random() * len - len / 2, 0)
        allChargedObjs.append(SphereChargedObj(massScalar, chargeScalar, randomPos, vec(0, 0, 0), True))
        allChargedObjs[-1].posCheck()
    # negative charge
    theta = random() * 2 * pi
    magnitude = random() * maxVel + minVel
    randomVel = vec(magnitude * cos(theta), magnitude * cos(theta), 0)
    allChargedObjs.append(SphereChargedObj(massScalar, -chargeScalar, vec(0, 0, 0), randomVel, False))
    allChargedObjs[-1].posCheck()
configurationList.append(mineField)

def randomChargeArena():
    startSimulation()
    # borders
    len = 9
    allChargedObjs.append(PlateChargedObj(0 * chargeScalar, 4 * len * len, 0, vec(0, -len, 0)))
    allChargedObjs.append(PlateChargedObj(0 * chargeScalar, 4 * len * len, 0, vec(0, len, 0)))
    allChargedObjs.append(PlateChargedObj(0 * chargeScalar, 4 * len * len, 90, vec(len, 0, 0)))
    allChargedObjs.append(PlateChargedObj(0 * chargeScalar, 4 * len * len, 90, vec(-len, 0, 0)))

    # 5 - 10 sphere charges
    num = round(random() * 5) + 5
    for i in range(num):
        randomPos = vec(random() * len - len / 2, random() * len - len / 2, 0)
        if (random() >= 0.5):
            allChargedObjs.append(SphereChargedObj(massScalar, 5*chargeScalar, randomPos, vec(0, 0, 0), False))
        else:
            allChargedObjs.append(SphereChargedObj(massScalar, -5*chargeScalar, randomPos, vec(0, 0, 0), False))
        allChargedObjs[-1].posCheck()

    # clear trail
    global trailStateAll
    trailStateAll = False
    for co in allChargedObjs:
        co.trail.stop() 
        co.trailState = False
configurationList.append(randomChargeArena)

# endregion    

def createPresetScreen():
    scene.caption = ""

    # region preset buttons
    scene.append_to_caption("   ")
    button(text = "Start without preset", bind = startSimulation)
    scene.append_to_caption("   ")
    button(text = "Y", bind = yPreset)
    scene.append_to_caption("   ")
    button(text = "J", bind = jPreset)

    scene.append_to_caption("\n\n  ")
    button(text = "Plate Tunnel", bind = plateTunnelPreset)
    scene.append_to_caption("  ")
    button(text = "draw figure 8", bind = figureEightPreset)
    scene.append_to_caption("\n\n   ")
    button(text = "Dipole", bind = dipolePreset)
    scene.append_to_caption("  ")
    button(text = "Three-Charge Motion", bind = threeChargePreset)
    scene.append_to_caption("\n\n   ")
    button(text = "Parallel Plates", bind = parallelPlatesPreset)
    scene.append_to_caption("  ")
    button(text = "Faraday Bucket", bind = faradayBucketPreset)
    scene.append_to_caption("\n\n   ")
    button(text = "Draw Helix", bind = helixPreset) 
    scene.append_to_caption("  ")
    button(text = "helix gun (kinda)", bind = helixGunPreset)
    scene.append_to_caption("\n\n   ")
    button(text = "model circular orbit", bind = circularOrbitPreset)
    scene.append_to_caption("  ")
    button(text = 'model eliptical orbit', bind = elipticalObritPreset) 
    scene.append_to_caption("\n\n   ")
    button(text = "loop Wave", bind = loopWavePreset)
    scene.append_to_caption("  ")
    button(text="Collision Wave", bind = collisionWavePreset) 
    scene.append_to_caption("\n\n   ")
    button(text = "Charge Trampoline", bind = chargeTrampolinePreset) 
    scene.append_to_caption("  ")
    button(text = "Charge Trampoline 2", bind = chargeTrampoline2Preset)
    scene.append_to_caption("\n\n  ")
    button(text = "Flower", bind = flowerPreset)
    scene.append_to_caption("  ")
    button(text = "Helix Madness", bind = fourHelixPreset)
    scene.append_to_caption("\n\n  ")
    button(text = "Orbits", bind = orbits)
    scene.append_to_caption("  ")
    button(text = "MineField", bind = mineField)
    scene.append_to_caption("  ")
    button(text = "Chaos", bind = randomChargeArena)
    
    # endregion
    
    # number of electric field lines slider and input field
    scene.append_to_caption("\n\n")
    slider(min = 4, max = 16, value = numOfLine, step = 1, bind = numOfLineShift, length = sliderLength)
    scene.append_to_caption("\n         Number of Electric Field Line Directions: ")
    winput(bind = numOfLineInput, text = numOfLine, width = 25)

    # electric field precision slider and input field
    scene.append_to_caption("\n\n")
    slider(min = 5, max = 20, value = electricFieldPrecision, step = 1, bind = electricFieldPrecisionShift, length = sliderLength)
    scene.append_to_caption("\n      Number of Electric Field Lines Per Direction: ")
    winput(bind = electricFieldPrecisionInput, text = electricFieldPrecision, width = 25)

    # grid precision slider and input field
    scene.append_to_caption("\n\n")
    slider(min = 5, max = 20, value = gridPrecision, step = 1, bind = gridPrecisionShift, length = sliderLength)
    scene.append_to_caption("\n" + slider20Spaces + "    Number of Grid Lines: ")
    winput(bind = gridPrecisionInput, text = gridPrecision, width = 25)

# region intro screen sliders and input fields

# number of electric field lines slider and input field
numOfLine = 8

def numOfLineShift():
    global numOfLine, numOfLineInputField
    numOfLine = numOfLineSlider.value
    numOfLineInputField.text = numOfLineSlider.value

def numOfLineInput():
    global numOfLine, numOfLineSlider
    if (numOfLineInputField.number != None):
        # min max
        num = round(num)
        num = max(numOfLineSlider.min, numOfLineInputField.number)
        num = min(numOfLineSlider.max, num)
        # set values
        numOfLineSlider.value = num
        numOfLineInputField.text = num
        numOfLine = num
    else:
        numOfLineInputField.text = numOfLine

# electric field precision slider and input field
electricFieldPrecision = 10

def electricFieldPrecisionShift():
    global electricFieldPrecision, electricFieldPrecisionInputField
    electricFieldPrecision = electricFieldPrecisionSlider.value
    electricFieldPrecisionInputField.text = electricFieldPrecisionSlider.value

def electricFieldPrecisionInput():
    global electricFieldPrecision, electricFieldPrecisionSlider
    if (electricFieldPrecisionInputField.number != None):
        # min max
        num = round(num)
        num = max(electricFieldPrecisionSlider.min, electricFieldPrecisionInputField.number)
        num = min(electricFieldPrecisionSlider.max, num)
        # set values
        electricFieldPrecisionSlider.value = num
        electricFieldPrecisionInputField.text = num
        electricFieldPrecision = num
    else:
        electricFieldPrecisionInputField.text = electricFieldPrecision

# grid precision slider and input field
gridPrecision = 10

def gridPrecisionShift():
    global gridPrecision, gridPrecisionInputField
    gridPrecision = gridPrecisionSlider.value
    gridPrecisionInputField.text = gridPrecisionSlider.value

def gridPrecisionInput():
    global gridPrecision, gridPrecisionSlider
    if (gridPrecisionInputField.number != None):
        # min max
        num = round(num)
        num = max(gridPrecisionSlider.min, gridPrecisionInputField.number)
        num = min(gridPrecisionSlider.max, num)
        # set values
        gridPrecisionSlider.value = num
        gridPrecisionInputField.text = num
        gridPrecision = num
    else:
        gridPrecisionInputField.text = gridPrecision

# endregion

# instruction
def createInstruction():
    scene.append_to_caption("""README: 

<b>Mouse Controls:</b>
Clicking:
When Not Playing: If an object is not selected, clicking on empty space will bring you to the spawn screen, and clicking an object will bring you to the select screen. If an object is already selected, clicking on empty space will deselect that object.
When Playing: When an object is selected, clicking will apply an impulse in that direction. 

Dragging: 
When Not Playing: Dragging an unselected object will move it. Dragging a selected spherical object will set its velocity and change the show vector mode to velocity. Dragging a selected plate object will set its angle. Dragging starting from empty space will measure the distance from that point to the point when you stop dragging. 
When Playing: When an object is selected, dragging and releasing will also apply an impulse in that direction.

<b>Intro Screen:</b>
Click on the start text to start the program.

<b>Preset Screen:</b> 
Presets: The user can choose to start the simulation without any preset, which will bring them to the main screen without any object placed down. They can also choose to start with a preset, which will bring them to the main screen with the premade charge configuration already placed down. 

Number of Electric Field Directions and Number of Electric Field Lines Per Direction Slider: Set the respective stats in electric field mode 1.

Number of Grid Lines Slider: Sets the respective quantity for electric field mode 2, electric potential mode 1, and the grid option. 

<b>Main Screen:</b> 
Play Button: Once objects are placed down, the play button starts the simulation of how those objects interact. When playing, the play button becomes a stop button, which allows the user to pause the simulation at any point to change the configuration. 

Clear Button: Clears all objects and trails from the screen.

Save Button: Saves the current charge configuration as a button so that the user can access any charge configuration that they find interesting at a later point in time. 

Time in Program Slider: Speeds up or slows down the simulation. (Disclaimer: due to the speed the computer runs the program, it is possible that this slider has no significant effect on the speed of the simulation.)

Update Time in Program Slider: Every this amount of time, the program will update the following physical variables: electric field mode, electric potential mode, and select screen.

Show Vector Menu: Allows the user to see either the velocity vector, the force vector, or neither on each spherical object throughout the simulation.

All Trail Check Box: Allows the user to see the path traveled by each particle throughout the simulation when checked. 

Clear All Trail Button: Allows the user to clear all the trails.

Electric Field Mode: Allows the user to either see no electric field in mode 0, the electric field on each object in mode 1, or the net electric field for the entire configuration in mode 2. 

Electric Field Opacity Check Box: When checked, displays the magnitude of the electric field through the opacity of the field arrows. 

Electric Potential Mode Button: Allows the user to either see no electric potential data in mode 0, or see the value of the electric potential of a grid of points across the screen in mode 1.

Grid Checkbox: When checked, allows the user to display a grid with the electric potential measurements at the center of each box and the electric field arrows at the vertices.

<b>Spawn Screen:</b> entered when empty space is clicked in the main screen
Spawn Object Menu: allows the user to select whether to spawn a sphere or plate.

Charge Slider: Sets the charge of the object to be spawned.

Mass Slider (For Spheres): Sets the mass of the sphere to be spawned.

Charge Density Slider (For Plates): Sets the area charge density of the plate to be spawned.

Angle Slider (For Plates): Sets the angle of placement with respect to the x-axis of the plate to be spawned.

Spawn Button: Spawns an object with variables set by the sliders.

Back Button: Takes the user back to the Main Screen.

Position, Electric Field, and Electric Potential Text: Display the position where the object will be spawned, and the electric field and electric potential at that point, denoted by the yellow triangle.

<b>Select Screen:</b> Entered when the user clicks on an object in the main screen while not playing. Denoted by the yellow arcs around the selected object. Contains all the same options as the main screen, Plus: 
Camera Follow Button: When pressed, the camera will follow the selected object when play is pressed, rather than remaining at the center of the screen.

Charge, Charge Density, Mass, and Angle Sliders: Allow the user to change the respective variables for the selected object (Cannot be changed while playing).

Fix Button: Allows the user to fix the selected object in place so it will not move when Play is pressed, but will still exert a force on other objects. Denoted by a black texture.

Trail Check Box: Allows the user to turn the trail on or off for the selected object (rather than for all objects through the All Trail Check Box). 

Clear Trail Button: Clears the trail for the selected object.

Delete: Deletes the selected object.

<b>Disclaimers:</b>
Loading Time: Because each screen takes time to load the caption, the user should allow each screen a couple of seconds to load or there will be an error message.

Precision Error: There is a low innate precision error in the program, which means that after a long enough time, some of the symmetric charge configurations will break out of their cycle. 

Slowing Down the Program: The user should be advised that turning on a lot of the modes, such as selecting an object while playing, turning on electric field lines, and turning on electric potential data, can slow down the program, and thus the movements of the objects, quite a bit. 

Presets: We suggest playing around with the masses in the presets! It yields cool results. 

Plates: The user should keep in mind that we assume that the mass of plates >> mass of spheres.
""")

createInstruction()

# region create intro screen

# intro text
introText = text(pos = vec(0, -1, -10), text="Electro-Sketch", align='center', color = color.cyan)
introText.height = 10
introText.length = 30

# start text
startText = text(pos = vec(0, -8, -10), text="start", align='center', color = color.white)
startText.height = 5
startText.length = 10

hover = False
startBox = box(pos = vec(0, -6, -20), size = vec(12, 6, 0.1), color = color.green)

# click to the second screen
secondScreen = False

def start():
    global secondScreen, introText, startText, hover
    if (hover):
        hover = False
        secondScreen = True
        # clear
        introText.visible = False
        startText.visible = False
        startBox.visible = False
    
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
        
        # new text
        global secondScreenText
        secondScreenText = text(pos = vec(0, -3, -10), text="Pick Your Preset", align='center', color = color.cyan, visible = False)
        secondScreenText.height = 10    
        secondScreenText.length = 30
        secondScreenText.visible = True

        # caption
        createPresetScreen()
    
scene.bind('click', start)

# test mode or intro configuration
if (testMode):
    hover = True
    start()
    test()
else:
    configurationList[int(random() * len(configurationList))]()

# endregion

# endregion

####################################################################################################

# region Program Runs Here
curRange = scene.range
curCameraPos = scene.camera.pos

t = 0

while True:
    rate(numOfRate * time)
    t += 1

    # before simulation
    if (not secondScreen):
        mousePos = scene.mouse.project(normal=vec(0, 0, 1), point = vec(0, 0, -20))
        # hover over start text
        if ((mousePos.x < startBox.pos.x + startBox.length / 2) and (mousePos.x > startBox.pos.x - startBox.length / 2) and (mousePos.y < startBox.pos.y + startBox.height / 2) and (mousePos.y > startBox.pos.y - startBox.height / 2)):
            startText.color = color.black
            hover = True
        else:
            startText.color = color.white
            hover = False

    if (playing):
        for chargedObj in allChargedObjs:
            if (chargedObj.type == "Sphere"):
                chargedObj.applyForce()
        for chargedObj in allChargedObjs:
            if (chargedObj.type == "Sphere"):
                chargedObj.applyVel()
        # collision
        if (not quantumTunneling):
            for charge in allChargedObjs:
                charge.checkCollision()
            for charge in allChargedObjs:
                if (chargedObj.type == "Sphere"):
                    charge.collided = []

    # once per second if playing
    if (playing and t % (numOfRate * updateTime) == 0):
        for chargedObj in allChargedObjs:
            chargedObj.displayElectricField()

        # reset electric field arrows and electric potential grid for all if user zooms or pan
        if (curRange != scene.range or curCameraPos != scene.camera.pos):
            curRange = scene.range
            curCameraPos = scene.camera.pos
            setUnits()
            setElectricFieldArrowsAll()
            setElectricPotentialGrid()

        displayElectricFieldAll()
        displayElectricPotential()

        # update stats in select screen
        if (chargedObjSelected != None):
            updatePosStatSelectScreen()
            if (chargedObjSelected.type == "Sphere"):
                updateVelocityStatsSelectScreen()
                updateForceStatSelectScreen()
    elif (not playing):
        for chargedObj in allChargedObjs:
            chargedObj.displayElectricField()

        # reset electric field arrows and electric potential grid for all if user zooms or pan
        if (curRange != scene.range or curCameraPos != scene.camera.pos):
            curRange = scene.range
            curCameraPos = scene.camera.pos
            setUnits()
            setElectricFieldArrowsAll()
            setElectricPotentialGrid()

        displayElectricFieldAll()
        displayElectricPotential()

    # update force vector because it is possible that mouse is not moving
    if (playing and mouseDown and chargedObjSelected != None and chargedObjSelected.type == "Sphere" and not chargedObjSelected.fixed):
        chargedObjSelected.impulseVec.pos = chargedObjSelected.pos
        chargedObjSelected.impulseVec.axis = getMousePos() - chargedObjSelected.pos 
        chargedObjSelected.createImpulseLabel()

# endregion
