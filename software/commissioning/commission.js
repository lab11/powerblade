#!/usr/bin/env node

/*********************************************************
*
* This is the commissioning script for PowerBlades
* The script performs three functions, each of which can be suppressed:
*
*	1. Program the MSP430 with the newest software image
*
*	2. Program the nRF with the newest software image
*		2.1 Determine if the PowerBlade already has a Device ID
*		2.2 If no, query AWS for next lowest available Device ID. Proceed to 2.3 and 2.4
*		2.3 Program with specified ID
*		2.4 Insert entry in AWS specifying date and version
*
*	3. Calibrate the MSP430
*		3.1 Run calibration procedure 
*		3.1 Insert entry in AWS specifying date, version, 
*
**********************************************************/

// MSP430 programming












