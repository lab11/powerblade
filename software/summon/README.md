PowerBlade Summon App
=================

Mobile phone user interface for PowerBlade. Works with
[Summon](https://github.com/lab11/summon) on Android and iOS.
This app can be pointed to from an Eddystone packet to serve the user
interface. The link is [goo.gl/9aD6Wi](goo.gl/9aD6Wi)

To rebuild everything:

    ./init_cordova.sh

To build and run on attached phone:
```
    cd _build/
    cordova run android
```

To debug an attached android phone:
```
    adb logcat chromium:D *:S
```

