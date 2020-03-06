## Dimmer Default

If you have triggers to turn on lights, but would like them to turn on at a different brightness at different time of the day, this plugin makes that relatively easy to accomplish.

1. Use a schedule (or some other logic) to run "Set Default Dimmer Level" actions to set your preferred brightness.
2. When you turn the light on, use a "Dim To Default Level" action instead of the built-in "Turn On" action.
3. Profit.

The plugin will optionally change the current brightness if the dimmer is already on when the default level changes.  It will also optionally update INSTEON hardware so that manually turning on the light will also use the default level (for directly-controlled loads only).
