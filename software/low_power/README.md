PowerBlade MSP430 Software
==========================


Installation
------------

1. Download [Code Composer Studio](http://www.ti.com/tool/ccstudio). Click the buttons
in the "Download" section. This will require you to have an account and go through
TI's export disclaimer headache. I'm sorry about this, TI is still pretty backwards.

2. Install Code Composer Studio. Make sure you check the boxes related to low power
MSP430 platforms. The install process took a while for me (10 minutes).

3. Open CCS and load the project. To do this:

    1. Select Project -> Import CCS Project from the menu.
    2. Near "Select search-directory" choose "Browse..." and choose
    this folder.
    3. Check "Automatically import referenced projects found in same search-directory"
    for good luck.
    4. Select "Finish".
    
4. Add paths to ../common/include in the compiler settings.

5. Change target device to MSP430FR5738.

6. Manually add define for `VERSION33` to the build.

7. Build should work.

