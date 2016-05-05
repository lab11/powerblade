#ifndef __POWERBLADE_STATES_H
#define __POWERBLADE_STATES_H

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

// state machine for local calibration
typedef enum {
    CALIB_NONE=0,
    CALIB_START,
    CALIB_WAIT_START,
    CALIB_CONTINUE,
    CALIB_WAIT_CONTINUE,
    CALIB_GET_CONFIG,
    CALIB_WAIT_GET_CONFIG,
    CALIB_STOP,
    CALIB_WAIT_STOP,
} CalibrationState_t;

// state machine for configuration
typedef enum {
    CONF_NONE=0,
    CONF_SET_VALUES,
    CONF_CLEAR_WH,
} ConfigurationState_t;

// state machine for startup
typedef enum {
    STARTUP_NONE=0,
    STARTUP_NOP,
    STARTUP_GET_CONFIG,
    STARTUP_GET_VERSION,
} StartupState_t;

// device status codes
typedef enum {
    STATUS_NONE=0,
    STATUS_BAD_CONFIG_SIZE,
    STATUS_BAD_CHECKSUM,
    STATUS_GOT_NAK,
    STATUS_NO_RS_START,
    STATUS_NO_RS_DATA,
    STATUS_NO_RS_QUIT,
    STATUS_NO_CALIB_START,
    STATUS_NO_CALIB_CONTINUE,
    STATUS_NO_CALIB_GET_CONFIG,
    STATUS_NO_CALIB_STOP,
} StatusCode_t;

#endif

