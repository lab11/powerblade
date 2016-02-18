// select which cordova_*.js to load based on the platform
if (navigator.platform.startsWith("iP")) {
    // iOS (iPhone, iPad, iPod)
    console.log("Loading iOS-specific cordova");
    $.getScript('cordova_ios.js', load_after);
} else {
    // android or bust
    console.log("Loading android-specific cordova");
    $.getScript('cordova_android.js', load_after);
}

// don't load the user's index.js until cordova is loaded
function load_after () {
    console.log("Loading user's index.js file");
    $.getScript('js/index.js');
}

