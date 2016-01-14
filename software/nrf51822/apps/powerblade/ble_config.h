#ifndef __BLE_CONFIG_H
#define __BLE_CONFIG_H

#define UMICH_COMPANY_IDENTIFIER    0x02E0
#define POWERBLADE_SERVICE_IDENTIFIER 0x11

// state machine for acknowledgements
typedef enum {
    NAK_NONE=0,
    NAK_CHECKSUM,
    NAK_RESEND,
} NakState_t;

// state machine for raw sample collection
typedef enum {
    RS_NONE=0,
    RS_START,
    RS_WAIT_START,
    RS_NEXT,
    RS_WAIT_DATA,
    RS_QUIT,
    RS_WAIT_QUIT,
    RS_IDLE,
} RawSampleState_t;

// state machine for calibration
typedef enum {
    CAL_NONE=0,
    CAL_START,
    CAL_GROUNDTRUTH,
    CAL_SETSEQ,
} CalibrationState_t;

// state machine for startup
typedef enum {
    STARTUP_NONE=0,
    STARTUP_SEQ,
} StartupState_t;

#endif

