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
    # Config and Validate
    #-------------------------------------------------------------------------------
    def validateActionConfigUi(self, valuesDict, typeId, devId):
        errorsDict = indigo.Dict()

        if typeId == 'setDefaultDimmerLevel':
            defaultDimmerLevel = zint(valuesDict.get('defaultLevel',""))
            if not (0 < defaultDimmerLevel <= 100):
                errorsDict['defaultLevel'] = "Must be integer between 1 and 100"
            if not indigo.devices[devId].protocol == indigo.kProtocol.Insteon:
                valuesDict['setHardwareDefault'] = False
            if len(errorsDict) > 0:
                return (False, valuesDict, errorsDict)
            else:
                valuesDict['description'] = u'set "{}" default level to {}'.format(indigo.devices[devId].name, defaultDimmerLevel)
                return (True, valuesDict)

    #-------------------------------------------------------------------------------
    # Action Methods
    #-------------------------------------------------------------------------------
    def setDefaultDimmerLevel(self, action, device):
        sharedProps = device.sharedProps
        defaultLevel = zint(action.props['defaultLevel'])
        if defaultLevel:
            sharedProps["defaultDimmerLevel"] = defaultLevel
            device.replaceSharedPropsOnServer(sharedProps)
            self.logger.info(f'"{device.name}" default level set to {defaultLevel}')
            if action.props['liveUpdate'] and device.onState:
                self.dimToDefaultLevel(action, device)
            if action.props['setHardwareDefault']:
                try:
                    rawCmd = [
                        0x2E, 0x00,
                        0x01,                                  # unused
                        0x06,                                  # change default brightness
                        int(float(defaultLevel)/100*255),      # brightness
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
                        ]
                    indigo.insteon.sendRawExtended(device.address, rawCmd)
                    self.logger.info(f'"{device.name}" default level set to {defaultLevel}')
                except:
                    self.logger.error(f'Unable to set insteon hardware default level for "{device.name}"')
        else:
            self.logger.error(f'Unable to set default level for "{device.name}". Check action config.')


    #-------------------------------------------------------------------------------
    def dimToDefaultLevel(self, action, device):
        defaultLevel = zint(device.sharedProps.get('defaultDimmerLevel',''))
        if defaultLevel:
            indigo.dimmer.setBrightness(device, value=defaultLevel)
        else:
            self.logger.error(f'"{device.name}" default level is not set (or is zero)')


###############################################################################
# Utilitites
################################################################################
def zint(value):
    try: return int(value)
    except: return 0
