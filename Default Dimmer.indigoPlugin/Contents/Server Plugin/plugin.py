#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2014, Perceptive Automation, LLC. All rights reserved.
# http://www.indigodomo.com

import indigo

# Note the "indigo" module is automatically imported and made available inside
# our global name space by the host process.

###############################################################################
# globals


################################################################################
class Plugin(indigo.PluginBase):

    #-------------------------------------------------------------------------------
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

    #-------------------------------------------------------------------------------
    def __del__(self):
        indigo.PluginBase.__del__(self)

    #-------------------------------------------------------------------------------
    # Start and Stop
    #-------------------------------------------------------------------------------
    def startup(self):
        self.logger.debug(u'startup')
        self.debug = self.pluginPrefs.get('showDebugInfo',False)
        if self.debug:
            self.logger.debug("Debug logging enabled")
        self.deviceDict = dict()
        indigo.devices.subscribeToChanges()

    #-------------------------------------------------------------------------------
    def shutdown(self):
        self.logger.debug(u'shutdown')
        self.pluginPrefs['showDebugInfo'] = self.debug

    #-------------------------------------------------------------------------------
    # Config and Validate
    #-------------------------------------------------------------------------------
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        self.logger.debug(u'closedPrefsConfigUi: {}'.format(userCancelled))
        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo',False)
            self.logger.debug("Debug logging {}".format(["disabled","enabled"][self.debug]))

    #-------------------------------------------------------------------------------
    def validatePrefsConfigUi(self, valuesDict):
        self.logger.debug(u'validatePrefsConfigUi')
        errorsDict = indigo.Dict()

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        return (True, valuesDict)

    #-------------------------------------------------------------------------------
    def validateDeviceConfigUi(self, valuesDict, typeId, devId, runtime=False):
        self.logger.debug(u'validateDeviceConfigUi: {}'.format(typeId))
        errorsDict = indigo.Dict()

        if not valuesDict.get('dimmerDevice',''):
            errorsDict['dimmerDevice'] = "Select a dimmer device"

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        else:
            return (True, valuesDict)

    #-------------------------------------------------------------------------------
    def validateActionConfigUi(self, valuesDict, typeId, devId):
        self.logger.debug(u'validateActionConfigUi: {}'.format(typeId))
        errorsDict = indigo.Dict()

        level = zint(valuesDict.get('defaultLevel',""))
        if not (0 < level <= 100):
            errorsDict['defaultLevel'] = "Must be integer between 1 and 100"

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        else:
            name = indigo.devices[devId].name
            value = valuesDict['defaultLevel']
            valuesDict['description'] = u'set "{}" default brightness to {}'.format(name, value)
            return (True, valuesDict)

    #-------------------------------------------------------------------------------
    # Device Methods
    #-------------------------------------------------------------------------------
    def deviceStartComm(self, device):
        self.logger.debug(u'deviceStartComm: {}'.format(device.name))

        if device.version != self.pluginVersion:
            self.updateDeviceVersion(device)

        if device.configured:
            self.deviceDict[device.id] = DefautDimmer(device, self.logger)

    #-------------------------------------------------------------------------------
    def deviceStopComm(self, device):
        self.logger.debug(u'deviceStopComm: {}'.format(device.name))
        if device.id in self.deviceDict:
            del self.deviceDict[device.id]

    #-------------------------------------------------------------------------------
    def updateDeviceVersion(self, device):
        self.logger.debug(u'updateDeviceVersion: {}'.format(device.name))
        theProps = device.pluginProps
        # update states
        device.stateListOrDisplayStateIdChanged()
        # check for changed props

        # push to server
        theProps["version"] = self.pluginVersion
        device.replacePluginPropsOnServer(theProps)

    #-------------------------------------------------------------------------------
    def deviceUpdated(self, oldDev, newDev):

        # device belongs to plugin
        if newDev.pluginId == self.pluginId or oldDev.pluginId == self.pluginId:
            indigo.PluginBase.deviceUpdated(self, oldDev, newDev)

        if isinstance(newDev, indigo.DimmerDevice):
            for device in self.deviceDict.values():
                device.deviceChanged(newDev)

    #-------------------------------------------------------------------------------
    # Action Methods
    #-------------------------------------------------------------------------------
    def actionControlDevice(self, action, device):
        self.logger.debug(u'actionControlDevice: {}'.format(action.deviceAction))
        pluginDevice = self.deviceDict[device.id]
        # ON
        if action.deviceAction == indigo.kDeviceAction.TurnOn:
            pluginDevice.onState = True
        # OFF
        elif action.deviceAction == indigo.kDeviceAction.TurnOff:
            pluginDevice.onState = False
        # TOGGLE
        elif action.deviceAction == indigo.kDeviceAction.Toggle:
            pluginDevice.onState = not pluginDevice.onState
        # BRIGHTNESS
        elif action.deviceAction == indigo.kDeviceAction.SetBrightness:
            pluginDevice.brightness = action.actionValue
        # STATUS
        elif action.deviceAction == indigo.kUniversalAction.RequestStatus:
            pluginDevice.status(True)
        # UNKNOWN
        else:
            self.logger.debug(u'"{}" {} request ignored'.format(device.name, action.deviceAction))

    #-------------------------------------------------------------------------------
    def setDimmerDefault(self, action):
        self.logger.debug(u'setDimmerDefault: {}'.format(action.pluginTypeId))
        pluginDevice = self.deviceDict[zint(action.props['deviceId'])]
        pluginDevice.default = zint(action.props['defaultLevel'])

    #-------------------------------------------------------------------------------
    # Menu Methods
    #-------------------------------------------------------------------------------
    def manualDefault(self, valuesDict, typeId):
        self.logger.debug(u'manualDefault: {}'.format(typeId))
        errorsDict = indigo.Dict()

        if valuesDict['pluginDevice'] == "":
            errorsDict['pluginDevice'] = "Select a device"

        level = zint(valuesDict.get('defaultLevel',""))
        if not (0 < level <= 100):
            errorsDict['defaultLevel'] = "Must be integer between 1 and 100"

        if len(errorsDict) > 0:
            return (False, valuesDict, errorsDict)
        else:
            pluginDevice = self.deviceDict[int(valuesDict['pluginDevice'])]
            pluginDevice.default = level
            return (True, valuesDict, errorsDict)

    #-------------------------------------------------------------------------------
    def toggleDebug(self):
        if self.debug:
            self.logger.debug("Debug logging disabled")
            self.debug = False
        else:
            self.debug = True
            self.logger.debug("Debug logging enabled")

    #-------------------------------------------------------------------------------
    # Menu Callbacks
    #-------------------------------------------------------------------------------
    def getDimmerDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        self.logger.debug(u'getDimmerDeviceList: {}'.format(targetId))
        excludeList  = [dev.id for dev in indigo.devices.iter(filter='self')]
        return [(dev.id, dev.name) for dev in indigo.devices.iter(filter='indigo.dimmer') if (dev.id not in excludeList)]

    #-------------------------------------------------------------------------------
    def loadHardwareFields(self, valuesDict=None, typeId='', targetId=0):
        self.logger.debug(u'loadHardwareFields: {}'.format(targetId))
        try:
            device = indigo.devices[int(valuesDict['dimmerDevice'])]
            if device.protocol == indigo.kProtocol.Insteon:
                valuesDict['showHardwareFields'] = True
            else:
                valuesDict['showHardwareFields'] = False
            return valuesDict
        except:
            pass

###############################################################################
# Classes
################################################################################
class DefautDimmer(object):

    #-------------------------------------------------------------------------------
    def __init__(self, instance, logger):
        self.logger = logger
        self.logger.debug(u'__init__: {}'.format(instance.name))

        self.device = instance
        self.dimmer = indigo.devices[int(instance.pluginProps['dimmerDevice'])]
        self.liveUpdate = instance.pluginProps['liveUpdate']
        self.insteonUpdate = False
        if instance.pluginProps['updateHardware']:
            if self.dimmer.protocol == indigo.kProtocol.Insteon:
                self.insteonUpdate = True

        if self.device.states['defaultBrightness'] == 0: # new device
            self.device.updateStateOnServer('defaultBrightness', 100)

        self.status()

    #-------------------------------------------------------------------------------
    def deviceChanged(self, newDev):
        if newDev.id == self.device.id:
            self.logger.debug(u'deviceChanged (self): {}'.format(newDev.name))
            self.device = newDev
        elif newDev.id == self.dimmer.id:
            self.logger.debug(u'deviceChanged (dimmer): {}'.format(newDev.name))
            self.dimmer = newDev
            if self.device.states['brightnessLevel'] != self.dimmer.states['brightnessLevel']:
                self.status()

    #-------------------------------------------------------------------------------
    def status(self, updateFromServer=False):
        self.logger.debug(u'status: {}'.format(self.device.name))
        if updateFromServer:
            self.dimmer = indigo.devices[self.dimmer.id]
        states = [
            {'key': 'onOffState',       'value': self.dimmer.states['onOffState']},
            {'key': 'brightnessLevel',  'value': self.dimmer.states['brightnessLevel']},
            ]
        self.device.updateStatesOnServer(states)

    #-------------------------------------------------------------------------------
    # properties
    #-------------------------------------------------------------------------------
    def _defaultGet(self):
        return self.device.states['defaultBrightness']
    def _defaultSet(self, defaultBrightness):
        self.device.updateStateOnServer(key='defaultBrightness', value=defaultBrightness)
        if self.liveUpdate and self.onState:
            indigo.dimmer.setBrightness(self.dimmer.id, value=defaultBrightness)
        if self.insteonUpdate:
            rawCmd = [
                0x2E, 0x00,
                0x01,                                       # unused
                0x06,                                       # change default brightness
                int(float(defaultBrightness)/100*255),      # brightness
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
                ]
            indigo.insteon.sendRawExtended(self.dimmer.address, rawCmd)
        self.logger.info(u'"{}" default brightness set to {}'.format(self.device.name,defaultBrightness))
    default = property(_defaultGet,_defaultSet)

    #-------------------------------------------------------------------------------
    def _onStateGet(self):
        return self.device.states['onOffState']
    def _onStateSet(self, onOffState):
        if onOffState:
            indigo.dimmer.setBrightness(self.dimmer.id, self.default)
        else:
            indigo.device.turnOff(self.dimmer.id)
        self.logger.debug(u'"{}" onState set to {}'.format(self.device.name,onOffState))
    onState = property(_onStateGet,_onStateSet)

    #-------------------------------------------------------------------------------
    def _brightnessGet(self):
        return self.device.states['brightnessLevel']
    def _brightnessSet(self, brightnessLevel):
        if brightnessLevel:
            indigo.dimmer.setBrightness(self.dimmer.id, brightnessLevel)
        else:
            indigo.device.turnOff(self.dimmer.id)
        self.logger.debug(u'"{}" brightness set to {}'.format(self.device.name,brightnessLevel))
    brightness = property(_brightnessGet,_brightnessSet)

###############################################################################
# Utilitites
################################################################################
def zint(value):
    try: return int(value)
    except: return 0
