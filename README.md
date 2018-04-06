## Dimmer Default

Creates simple 'wrapper' type devices that exactly mirror real dimmer devices except:
1. A default brightness level can be set via action
2. When the plugin device is turned on, the real dimmer will be set to the default brightness
3. For Insteon dimmers, the plugin will also (optionally) update the hardware so that manual operation will also use the default brightness.

Otherwise the plugin device will always bi-directionally sync with the real dimmer.

Obviously this plugin has no effect on Insteon scenes/links or Z-wave associations.
