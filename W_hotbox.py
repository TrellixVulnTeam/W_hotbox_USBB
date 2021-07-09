#----------------------------------------------------------------------------------------------------------
# Wouter Gilsing
# woutergilsing@hotmail.com
version = '1.3'
releaseDate = 'Sept 4 2016'

#----------------------------------------------------------------------------------------------------------
#
#LICENSE
#
#----------------------------------------------------------------------------------------------------------
'''
Copyright (c) 2016, Wouter Gilsing
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Redistribution of this software in source or binary forms shall be free
      of all charges or fees to the recipient of this software.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

#----------------------------------------------------------------------------------------------------------

import nuke

from PySide import QtGui, QtCore

import os
import subprocess
import platform

import colorsys

#----------------------------------------------------------------------------------------------------------

class hotbox(QtGui.QWidget):
    '''
    The main class for the hotbox
    '''

    def __init__(self, subMenuMode = False, path = '', name = '', position = ''):
        super (hotbox, self).__init__()

        self.active = True

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        if not preferencesNode.knob('hotboxOpaqueBackground').value():
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        masterLayout = QtGui.QVBoxLayout()
        self.setLayout(masterLayout)

        #--------------------------------------------------------------------------------------------------
        #main hotbox
        #--------------------------------------------------------------------------------------------------

        if not subMenuMode:

            self.selection = nuke.selectedNodes()

            if len(self.selection) > 1:

                if len(list(set([i.Class() for i in nuke.selectedNodes()]))) == 1:
                    self.mode = 'Single'
                else:
                    self.mode = 'Multiple'

            else:
                self.mode = 'Single'

            #Layouts
            centerLayout = QtGui.QHBoxLayout()

            centerLayout.addStretch()
            centerLayout.addWidget(hotboxButton('Reveal in %s'%getFileBrowser(),'revealInBrowser()'))
            centerLayout.addSpacing(25)
            centerLayout.addWidget(hotboxCenter())
            centerLayout.addSpacing(25)
            centerLayout.addWidget(hotboxButton('Hotbox Manager','showHotboxManager()'))
            centerLayout.addStretch()

            self.topLayout = nodeButtons(self.mode)
            self.bottomLayout = nodeButtons('All')
            spacing = 12

        #--------------------------------------------------------------------------------------------------
        #submenu
        #--------------------------------------------------------------------------------------------------

        else:

            allItems = [path + '/' + i for i in sorted(os.listdir(path)) if i[0] not in ['.','_']]

            centerItems = allItems[:2]

            lists = [[],[]]
            for index, item in enumerate(allItems[2:]):

                if int((index%4)/2):
                    lists[index%2].append(item)
                else:
                    lists[index%2].insert(0,item)


            #Stretch layout
            centerLayout = QtGui.QHBoxLayout()

            centerLayout.addStretch()
            for index, item in enumerate(centerItems):
                centerLayout.addWidget(hotboxButton(item))
                if index == 0:
                    centerLayout.addWidget(hotboxCenter(False,path))

            if len(centerItems) == 1:
                centerLayout.addSpacing(105)

            centerLayout.addStretch()

            self.topLayout = nodeButtons('SubMenuTop',lists[0])
            self.bottomLayout = nodeButtons('SubMenuBottom',lists[1])
            spacing = 0

        #--------------------------------------------------------------------------------------------------
        #Equalize layouts to make sure the center layout is the center of the hotbox
        #--------------------------------------------------------------------------------------------------

        difference = self.topLayout.count() - self.bottomLayout.count()

        if difference != 0:

            extraLayout = QtGui.QVBoxLayout()

            for i in range(abs(difference)):
                extraLayout.addSpacing(35)

            if difference > 0:
                self.bottomLayout.addLayout(extraLayout)
            else:
                self.topLayout.insertLayout(0,extraLayout)

        #--------------------------------------------------------------------------------------------------

        masterLayout.addLayout(self.topLayout)
        masterLayout.addSpacing(spacing)
        masterLayout.addLayout(centerLayout)
        masterLayout.addSpacing(spacing)
        masterLayout.addLayout(self.bottomLayout)

        #position
        self.adjustSize()

        self.spwanPosition = QtGui.QCursor().pos() - QtCore.QPoint((self.width()/2),(self.height()/2))

        #set last position if a fresh instance of the hotbox is launched
        if position == '' and not subMenuMode:
            global lastPosition
            lastPosition = self.spwanPosition

        if subMenuMode:
            self.move(self.spwanPosition)

        else:
            self.move(lastPosition)

        #make sure the widgets closes when it loses focus
        self.installEventFilter(self)

    def closeHotbox(self):
        self.active = False
        self.close()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return False
        if event.text() == shortcut:
            global lastPosition
            lastPosition = ''
            self.closeHotbox()
            return True

    def eventFilter(self, object, event):
        if event.type() in [QtCore.QEvent.WindowDeactivate,QtCore.QEvent.FocusOut]:
            self.closeHotbox()
            return True
        return False

#----------------------------------------------------------------------------------------------------------
#Button field
#----------------------------------------------------------------------------------------------------------

class nodeButtons(QtGui.QVBoxLayout):
    '''
    Create QLayout filled with buttons
    '''
    def __init__(self, mode, allItems = ''):
        super (nodeButtons, self).__init__()

        selectedNodes = nuke.selectedNodes()
        mirrored = True

        #--------------------------------------------------------------------------------------------------
        #submenu
        #--------------------------------------------------------------------------------------------------

        if 'submenu' in mode.lower():

            self.rowMaxAmount = 3
            if 'top' in mode.lower():
                mirrored = False

        #--------------------------------------------------------------------------------------------------
        #main hotbox
        #--------------------------------------------------------------------------------------------------

        else:

            self.path = preferencesNode.knob('hotboxLocation').value().replace('\\','/')
            if self.path[-1] != '/':
                self.path = self.path + '/'

            self.allRepositories = list(set([self.path]+[i[1] for i in extraRepositories]))

            self.rowMaxAmount = int(preferencesNode.knob('hotboxRowAmountAll').value())

            self.folderList = []
            
            
            if mode == 'All':

                for repository in self.allRepositories:
                    self.folderList.append(repository + mode + '/')

            else:
                mirrored = False
                self.rowMaxAmount = int(preferencesNode.knob('hotboxRowAmountSelection').value())

                if mode == 'Single':

                    if len(selectedNodes) == 0:
                        nodeClass = 'No Selection'

                    else:
                        nodeClass = selectedNodes[0].Class()
                    
                    for repository in self.allRepositories:
                        self.folderList.append(repository + mode + '/' + nodeClass)
                    
                    #check if group, if so take the name of the group, as well as the class

                    if nodeClass == 'Group':
                        nodeClass = selectedNodes[0].name()
                        while nodeClass[-1] in [str(i) for i in range(10)]:
                            nodeClass = nodeClass[:-1]
                        for repository in self.allRepositories:
                            self.folderList.append(repository + mode + '/' + nodeClass)

                else:
                    #scan the 'multiple' folder for folders containing all the currently selected classes.
                    nodeClasses = sorted(list(set([i.Class() for i in selectedNodes])))
                    
                    for repository in self.allRepositories:
                        try:
                            for i in sorted(os.listdir(repository + mode)):
                                if i[0] not in ['.','_']:
                                    folderClasses = sorted(i.split('-'))
                                    if nodeClasses == sorted(list(set(nodeClasses).intersection(folderClasses))):
                                        self.folderList.append(repository + mode + '/' + i)
                        except:
                            pass
                        
            allItems = []

            for folder in list(set(self.folderList)):
                #check if path exists
                if os.path.exists(folder):
                    for i in sorted(os.listdir(folder)):
                        if i[0] not in ['.','_'] and len(i) in [3,6]:
                            if folder[-1] != '/':
                                folder += '/'
                            allItems.append(folder + i)

        #--------------------------------------------------------------------------------------------------
        #devide in rows based on the row maximum

        allRows = []
        row = []

        for i in range(len(allItems)):
            currentItem = allItems[i]
            if preferencesNode.knob('hotboxButtonSpawnMode').value():
                if len(row) %2:
                    row.append(currentItem)
                else:
                    row.insert(0,currentItem)
            else:
                row.append(currentItem)
            #when a row reaches its full capacity, add the row to the allRows list
            #and start a new one. Increase rowcapacity to get a triangular shape
            if len(row) == self.rowMaxAmount:
                allRows.append(row)
                row = []
                self.rowMaxAmount += preferencesNode.knob('hotboxRowStepSize').value()

        #if the last row is not completely full, add it to the allRows list anyway
        if len(row) != 0:
            allRows.append(row)

        if mirrored:
            rows =  allRows
        else:
            rows =  allRows[::-1]

        #nodeHotboxLayout
        for row in rows:
            self.rowLayout = QtGui.QHBoxLayout()

            self.rowLayout.addStretch()

            for button in row:
                buttonObject = hotboxButton(button)
                self.rowLayout.addWidget(buttonObject)
            self.rowLayout.addStretch()

            self.addLayout(self.rowLayout)

        self.rowAmount = len(rows)

#----------------------------------------------------------------------------------------------------------

class hotboxCenter(QtGui.QLabel):
    '''
    Center button of the hotbox.
    If the 'color nodes' is set to True in the preferencespanel, the button will take over the color and
    name of the current selection. If not, the button will be the same color as the other buttons will
    be in their selected state. The text will be read from the _name.json file in the folder.
    '''

    def __init__(self, node = True, name = ''):
        super ( hotboxCenter ,self ).__init__()

        self.node = node

        nodeColor = '#525252'
        textColor = '#eeeeee'

        selectedNodes = nuke.selectedNodes()

        if node:

            #if no node selected
            if len(selectedNodes) == 0:
                name = 'W_hotbox'
                nodeColorRGB = interface2rgb(640034559)

            #if node(s) selected
            else:
                name = nuke.selectedNode().name()
                nodeColorRGB = interface2rgb(getTileColor())

            if preferencesNode.knob('hotboxColorCenter').value():
                nodeColor = rgb2hex(nodeColorRGB)

                nodeColorHSV = colorsys.rgb_to_hsv(nodeColorRGB[0],nodeColorRGB[1],nodeColorRGB[2])

                if nodeColorHSV[2] > 0.7 and nodeColorHSV[1] < 0.4:
                    textColor = '#262626'

            width = 115
            height = 60


            if (len(set([i.Class() for i in selectedNodes]))) > 1:
                name = 'Selection'

        else:

            name = open(name + '/_name.json').read()
            nodeColor = getSelectionColor()

            width = 105
            height = 35

        self.setText(name)

        self.setAlignment(QtCore.Qt.AlignCenter)

        self.setFixedWidth(width)
        self.setFixedHeight(height)

        #resize font based on length of name
        fontSize = max(5,(13-(max(0,(len(name) - 11))/2)))
        font = QtGui.QFont(preferencesNode.knob('UIFont').value(), fontSize)
        self.setFont(font)

        self.setStyleSheet("""
                border: 1px solid black;
                color:%s;
                background:%s""" %(textColor, nodeColor))

        self.setSelectionStatus(True)

    def setSelectionStatus(self, selected = False):
        '''
        Define the style of the button for different states
        '''
        if not self.node:
            self.selected = selected

    def enterEvent(self, event):
        '''
        Change color of the button when the mouse starts hovering over it
        '''
        if not self.node:
            self.setSelectionStatus(True)
        return True

    def leaveEvent(self,event):
        if not self.node:
            self.setSelectionStatus()
        return True

    def mouseReleaseEvent(self,event):
        '''
        Execute the buttons' self.function (str)
        '''
        if not self.node:
            showHotbox(True, resetPosition = False)
        return True

#----------------------------------------------------------------------------------------------------------
#Buttons
#----------------------------------------------------------------------------------------------------------

class hotboxButton(QtGui.QLabel):
    '''
    Button class
    '''

    def __init__(self, name, function = None):

        super(hotboxButton, self).__init__()

        self.filePath = name
        self.bgColor = '#525252'

        self.borderColor = '#000000'

        #set the border color to grey for buttons from an additional repository
        for index,i in enumerate(extraRepositories):
            if name.startswith(i[1]):
                self.borderColor = '#959595'
                break

        if function != None:
            self.function = function

        else:

            #----------------------------------------------------------------------------------------------
            #Button linked to folder
            #----------------------------------------------------------------------------------------------

            if os.path.isdir(self.filePath):

                name = open(self.filePath+'/_name.json').read()
                self.function = 'showHotboxSubMenu("%s","%s")'%(self.filePath,name)
                self.bgColor = '#333333'

            #----------------------------------------------------------------------------------------------
            #Button linked to file
            #----------------------------------------------------------------------------------------------

            else:

                self.openFile = open(name).readlines()
                nameTag = '# NAME: '

                for index, line in enumerate(self.openFile):

                    if line.startswith(nameTag):

                        name = line.split(nameTag)[-1].replace('\n','')

                    if not line.startswith('#'):
                        self.function = ''.join(self.openFile[index:])
                        break

            #----------------------------------------------------------------------------------------------

        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMouseTracking(True)
        self.setFixedWidth(105)
        self.setFixedHeight(35)
        fontSize = preferencesNode.knob('hotboxFontSize').value()
        font = QtGui.QFont(preferencesNode.knob('UIFont').value(), fontSize, QtGui.QFont.Bold)
        self.setFont(font)
        self.setWordWrap(True)
        self.setTextFormat(QtCore.Qt.RichText)

        self.setText(name)


        self.setAlignment(QtCore.Qt.AlignCenter)

        self.selected = False
        self.setSelectionStatus()

    def setSelectionStatus(self, selected = False):
        '''
        Define the style of the button for different states
        '''

        if selected:
            self.setStyleSheet("""
                                border: 1px solid black;
                                background:%s;
                                color:#eeeeee;
                                """%getSelectionColor())
        else:
            self.setStyleSheet("""
                                border: 1px solid %s;
                                background:%s;
                                color:#eeeeee;
                                """%(self.borderColor, self.bgColor))

        self.selected = selected

    def enterEvent(self, event):
        '''
        Change color of the button when the mouse starts hovering over it
        '''
        self.setSelectionStatus(True)
        return True

    def leaveEvent(self,event):
        '''
        Change color of the button when the mouse stops hovering over it
        '''
        self.setSelectionStatus()
        return True

    def mouseReleaseEvent(self,event):
        '''
        Execute the buttons' self.function (str)
        '''
        if self.selected:
            nuke.Undo().name(self.text())
            nuke.Undo().begin()
            try:
                exec self.function
            except:
                pass
            nuke.Undo().end()
        return True

#----------------------------------------------------------------------------------------------------------
#Preferences
#----------------------------------------------------------------------------------------------------------

def addToPreferences(knobObject):
    '''
    Add a knob to the preference panel.
    Save current preferences to the prefencesfile in the .nuke folder.
    '''
    preferencesNode = nuke.toNode('preferences')

    if knobObject.name() not in preferencesNode.knobs().keys():

        preferencesNode.addKnob(knobObject)
        savePreferencesToFile()
        return preferencesNode.knob(knobObject.name())

def savePreferencesToFile():
    '''
    Save current preferences to the prefencesfile in the .nuke folder.
    Pythonic alternative to the 'ok' button of the preferences panel.
    '''

    nukeFolder = os.path.expanduser('~') + '/.nuke/'
    preferencesFile = nukeFolder + 'preferences%i.%i.nk' %(nuke.NUKE_VERSION_MAJOR,nuke.NUKE_VERSION_MINOR)

    preferencesNode = nuke.toNode('preferences')

    customPrefences = preferencesNode.writeKnobs( nuke.WRITE_USER_KNOB_DEFS | nuke.WRITE_NON_DEFAULT_ONLY | nuke.TO_SCRIPT | nuke.TO_VALUE )
    customPrefences = customPrefences.replace('\n','\n  ')

    preferencesCode = 'Preferences {\n inputs 0\n name Preferences%s\n}' %customPrefences

    # write to file
    openPreferencesFile = open( preferencesFile , 'w' )
    openPreferencesFile.write( preferencesCode )
    openPreferencesFile.close()

def deletePreferences():
    '''
    Delete all the W_hotbox related items in the properties panel.
    '''

    firstLaunch = True
    for i in preferencesNode.knobs().keys():
        if 'hotbox' in i:
            preferencesNode.removeKnob(preferencesNode.knob(i))
            firstLaunch = False

    #remove TabKnob
    try:
        preferencesNode.removeKnob(preferencesNode.knob('hotboxLabel'))
    except:
        pass

    if not firstLaunch:
        savePreferencesToFile()

def addPreferences():
    '''
    Add knobs to the preferences needed for this module to work properly.
    '''
    
    homeFolder = os.getenv('HOME').replace('\\','/') + '/.nuke'
    
    addToPreferences(nuke.Tab_Knob('hotboxLabel','W_hotbox'))
    addToPreferences(nuke.Text_Knob('hotboxGeneralLabel','<b>General</b>'))

    #version knob to check whether the hotbox was updated
    versionKnob = nuke.String_Knob('hotboxVersion','version')
    versionKnob.setValue(version)
    addToPreferences(versionKnob)
    preferencesNode.knob('hotboxVersion').setVisible(False)

    #location knob
    locationKnob = nuke.File_Knob('hotboxLocation','Hotbox location')
    locationKnobAdded = addToPreferences(locationKnob)
    if locationKnobAdded != None:
        locationKnob.setValue(homeFolder + '/W_hotbox')

    #icons knob
    iconLocationKnob = nuke.File_Knob('hotboxIconLocation','Icons location')
    iconLocationKnob.setValue(homeFolder +'/icons/W_hotbox')
    addToPreferences(iconLocationKnob)

    #shortcut knob
    shortcutKnob = nuke.String_Knob('hotboxShortcut','shortcut')
    shortcutKnob.setValue('`')
    addToPreferences(shortcutKnob)
    global shortcut
    shortcut = preferencesNode.knob('hotboxShortcut').value()

    #transparency knob
    opaqueKnob = nuke.Boolean_Knob('hotboxOpaqueBackground', 'Disable transparancy')
    opaqueKnob.setValue(False)
    opaqueKnob.setFlag(nuke.STARTLINE)
    addToPreferences(opaqueKnob)

    #Check if the compositing manager is running. If thats not the case, disable the transparancy.
    if not preferencesNode.knob('hotboxOpaqueBackground').value():
        try:
            if not QtGui.QX11Info.isCompositingManagerRunning():
                preferencesNode.knob('hotBoxOpaqueBackground').setValue(True)
        except:
            pass

    #open manager button
    openManagerKnob = nuke.PyScript_Knob('hotboxOpenManager','open hotbox manager','W_hotboxManager.showHotboxManager()')
    openManagerKnob.setFlag(nuke.STARTLINE)
    addToPreferences(openManagerKnob)

    #open in file system button
    openFolderKnob = nuke.PyScript_Knob('hotboxOpenFolder','open hotbox folder','W_hotbox.revealInBrowser(True)')
    addToPreferences(openFolderKnob)

    #delete preferences button
    deletePreferencesKnob = nuke.PyScript_Knob('hotboxDeletePreferences','delete preferences','W_hotbox.deletePreferences()')
    addToPreferences(deletePreferencesKnob)

    addToPreferences(nuke.Text_Knob('hotboxAppearanceLabel','<b>Appearance</b>'))

    colorDropdownKnob = nuke.Enumeration_Knob('hotboxColorDropdown', 'Color scheme',['Maya','Nuke','Custom'])
    addToPreferences(colorDropdownKnob)

    colorCustomKnob = nuke.ColorChip_Knob('hotboxColorCustom','')
    colorCustomKnob.clearFlag(nuke.STARTLINE)
    addToPreferences(colorCustomKnob)

    colorHotboxCenterKnob = nuke.Boolean_Knob('hotboxColorCenter','Colorize hotbox center')
    colorHotboxCenterKnob.setValue(True)
    colorHotboxCenterKnob.clearFlag(nuke.STARTLINE)
    addToPreferences(colorHotboxCenterKnob)

    #fontsize knob
    fontSizeKnob = nuke.Int_Knob('hotboxFontSize','Font size')
    fontSizeKnob.setValue(9)
    addToPreferences(fontSizeKnob)

    addToPreferences(nuke.Text_Knob('hotboxItemsLabel','<b>Items per Row</b>'))

    rowAmountSelectionKnob = nuke.Int_Knob('hotboxRowAmountSelection', 'Selection specific')
    rowAmountSelectionAll = nuke.Int_Knob('hotboxRowAmountAll','All')

    for knob in [rowAmountSelectionKnob,rowAmountSelectionAll]:
        knob.setValue(3)
        addToPreferences(knob)
    
    stepSizeKnob = nuke.Int_Knob('hotboxRowStepSize','Step size')
    stepSizeKnob.setValue(1)
    addToPreferences(stepSizeKnob)

    spawnModeKnob = nuke.Boolean_Knob('hotboxButtonSpawnMode','Add new buttons to the sides')
    spawnModeKnob.setValue(True)
    spawnModeKnob.setFlag(nuke.STARTLINE)
    addToPreferences(spawnModeKnob)

    #hide the iconLocation knob if environment varible called 'W_HOTBOX_HIDE_ICON_LOC' is set to 'true' or '1'
    preferencesNode.knob('hotboxIconLocation').setVisible(True)
    if 'W_HOTBOX_HIDE_ICON_LOC' in os.environ.keys():
        if os.environ['W_HOTBOX_HIDE_ICON_LOC'].lower() in ['true','1']:
            preferencesNode.knob('hotboxIconLocation').setVisible(False)

    savePreferencesToFile()

def updatePreferences():
    '''
    Check whether the hotbox was updated since the last launch. If so refresh the preferences.
    '''


    allKnobs = preferencesNode.knobs().keys()

    #Older versions of the hotbox had a knob called 'iconLocation'.
    #This was a mistake and the knob was supposed to be called
    #'hotboxIconLocation', similar to the rest of the knobs.

    forceUpdate = False

    if 'iconLocation' in allKnobs and 'hotboxIconLocation' not in allKnobs:

        currentSetting = preferencesNode.knob('iconLocation').value()

        #delete 'iconLocation'
        preferencesNode.removeKnob(preferencesNode.knob('iconLocation'))

        #re-add 'hotboxIconLocation'
        iconLocationKnob = nuke.File_Knob('hotboxIconLocation','Icons location')
        iconLocationKnob.setValue(currentSetting)
        addToPreferences(iconLocationKnob)

        forceUpdate = True

    allKnobs = preferencesNode.knobs().keys()
    proceedUpdate = True

    if 'hotboxVersion' in allKnobs or forceUpdate:

        if not forceUpdate:
            if float(version) == float(preferencesNode.knob('hotboxVersion').value()):
                proceedUpdate = False
                
        if proceedUpdate:
            currentSettings = {knob:preferencesNode.knob(knob).value() for knob in allKnobs if knob.startswith('hotbox') and knob != 'hotboxVersion'}

            #delete all the preferences
            deletePreferences()

            #re-add all the knobs
            addPreferences()

            #Restore
            for knob in currentSettings.keys():
                try:
                    preferencesNode.knob(knob).setValue(currentSettings[knob])
                except:
                    pass

            #save to file
            savePreferencesToFile()

#----------------------------------------------------------------------------------------------------------
#Color
#----------------------------------------------------------------------------------------------------------

def interface2rgb(hexValue, normalize = True):
    '''
    Convert a color stored as a 32 bit value as used by nuke for interface colors to normalized rgb values.

    '''
    return [(0xFF & hexValue >>  i) / 255.0 for i in [24,16,8]]


def rgb2hex(rgbaValues):
    '''
    Convert a color stored as normalized rgb values to a 32 bit value as used by nuke for interface colors.
    '''
    if len(rgbaValues) < 3:
        return
    return '#%02x%02x%02x' % (rgbaValues[0]*255,rgbaValues[1]*255,rgbaValues[2]*255)

def getTileColor(node = ''):
    '''
    If a node has it's color set automatically, the 'tile_color' knob will return 0.
    If so, this function will scan through the preferences to find the correct color value.
    '''

    if node == '':
        node = nuke.selectedNode()

    interfaceColor = node.knob('tile_color').value()

    if interfaceColor == 0:
        interfaceColor = nuke.defaultNodeColor(node.Class())

    return interfaceColor

def getSelectionColor():
    '''
    Return color to be used for the selected items of the hotbox.
    '''

    customColor = rgb2hex(interface2rgb(preferencesNode.knob('hotboxColorCustom').value()))
    colorMode = int(preferencesNode.knob('hotboxColorDropdown').getValue())
    
    return['#5285a6','#f7931e',customColor][colorMode]

#----------------------------------------------------------------------------------------------------------

def showHotbox(force = False, resetPosition = True):

    global hotboxInstance
    if force:
        hotboxInstance.active = False
        hotboxInstance.close()

    if resetPosition:
        global lastPosition
        lastPosition = ''

    if hotboxInstance == None or not hotboxInstance.active:
        hotboxInstance = hotbox(position = lastPosition)
        hotboxInstance.show()

def showHotboxSubMenu(path, name):
    global hotboxInstance
    hotboxInstance.active = False
    if hotboxInstance == None or not hotboxInstance.active:
        hotboxInstance = hotbox(True, path, name)
        hotboxInstance.show()

def showHotboxManager():
    '''
    Open the hotbox manager from the hotbox
    '''
    hotboxInstance.closeHotbox()
    W_hotboxManager.showHotboxManager()

#----------------------------------------------------------------------------------------------------------

def revealInBrowser(startFolder = False):
    '''
    Reveal the hotbox folder in a filebrowser
    '''
    if startFolder:
        path = preferencesNode.knob('hotboxLocation').value()

    else:
        try:
            path =  hotboxInstance.topLayout.folderList[0]
        except:
            path = hotboxInstance.topLayout.path + hotboxInstance.mode

    if not os.path.exists(path):
        path = os.path.dirname(path)

    operatingSystem = platform.system()

    if operatingSystem == "Windows":
        os.startfile(path)
    elif operatingSystem == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

def getFileBrowser():
    '''
    Determine the name of the file browser on the current system.
    '''
    operatingSystem = platform.system()

    if operatingSystem == "Windows":
        fileBrowser = 'Explorer'
    elif operatingSystem == "Darwin":
        fileBrowser = 'Finder'
    else:
        fileBrowser = 'file browser'

    return fileBrowser


#----------------------------------------------------------------------------------------------------------

nuke.tprint('W_hotbox v%s, built %s.\nCopyright (c) 2016 Wouter Gilsing. All Rights Reserved.'%(version,releaseDate))

#add knobs to preferences
preferencesNode = nuke.toNode('preferences')
updatePreferences()
addPreferences()

#----------------------------------------------------------------------------------------------------------

#make sure the archive folders are present, if not, create them

hotboxLocationPath = preferencesNode.knob('hotboxLocation').value().replace('\\','/')
if hotboxLocationPath[-1] != '/':
    hotboxLocationPath += '/'

for subFolder in ['','Single','Multiple','All','Single/No Selection']:
    subFolderPath = hotboxLocationPath + subFolder
    if not os.path.isdir(subFolderPath):
        try:
            os.mkdir(subFolderPath)
        except:
            pass

#----------------------------------------------------------------------------------------------------------

#check for environment variables to add extra repositories
'''
add them line this:
NUKE_HOTBOX_REPO_PATHS=/path1:/path2:/path3
NUKE_HOTBOX_REPO_NAMES=name1:name2:name3
'''

extraRepositories = []

if 'W_HOTBOX_REPO_PATHS' in os.environ and 'W_HOTBOX_REPO_NAMES' in os.environ.keys():

    extraRepositoriesPaths = os.environ['W_HOTBOX_REPO_PATHS'].split(os.pathsep)
    extraRepositoriesNames = os.environ['W_HOTBOX_REPO_NAMES'].split(os.pathsep)

    for index, i in enumerate(range(min(len(extraRepositoriesPaths),len(extraRepositoriesNames)))):
        path = extraRepositoriesPaths[index].replace('\\','/')

        #make sure last character is a '/'
        if path[-1] != '/':
            path += '/'

        name = extraRepositoriesNames[index]
        if name not in [i[0] for i in extraRepositories] and path not in [i[1] for i in extraRepositories]:
            extraRepositories.append([name,path])

#----------------------------------------------------------------------------------------------------------

import W_hotboxManager

hotboxInstance = None
lastPosition = ''

#---------------------------------------------------------------------------------------------------------- 
#add menu items

nuke.menu('Nuke').addCommand('Edit/W_hotbox/Open W_hotbox',showHotbox, shortcut)
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Open Hotbox Manager', 'W_hotboxManager.showHotboxManager()')
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Open in %s'%getFileBrowser(), revealInBrowser)
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Repair', 'W_hotboxManager.repairHotbox()')
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Clear/Clear Everything', 'W_hotboxManager.clearHotboxManager()')
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Clear/Clear Section/Single', 'W_hotboxManager.clearHotboxManager(["Single"])')
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Clear/Clear Section/Multiple', 'W_hotboxManager.clearHotboxManager(["Multiple"])')
nuke.menu('Nuke').addCommand('Edit/W_hotbox/Clear/Clear Section/All', 'W_hotboxManager.clearHotboxManager(["All"])')

if len(extraRepositories) > 0:
    for i in extraRepositories:
        nuke.menu('Nuke').addCommand('Edit/W_hotbox/Special/Open Hotbox Manager - %s'%i[0], 'W_hotboxManager.showHotboxManager(path="%s")'%i[1])