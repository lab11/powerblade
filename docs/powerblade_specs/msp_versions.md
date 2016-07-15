PowerBlade MSP430 Versions
==========================

In PowerBlade, the nRF51822 can query software version from the MSP430. This is seperate from the powerblade_id transmitted 
with each packet, which only increments if the over-the-wire protocol has changed. The MSP430 software version reflects the
particular state of the MSP430 code when it was installed on the node, and increments whenever a change has been made that 
affects functionality. Therefore incrementing powerblade_id (in response to a protocol change) will also cause a change in MSP430 
version, but a change in MSP430 version will not necessarily require a change in powerblade_id. 

For example, the MSP430 version could reflect whether the node is running a 8-bit or 10-bit analog to digital converter, or whether
the WDT (watchdog timer) is enabled. 

## MSP Version List

| Version	| PB_ID 	| Notes		|
|:----------|:----------|:----------|
| 0  		| Multiple	| This is the default, the first MSP430 code that responds to the version request will respond '1' |
| 1			| 2			| 10 bit ADC, watchdog timer enabled |
| 2			| 2			| Local calibration, SET SEQ (0x1C) and RST WH (0x1D) no longer valid |


