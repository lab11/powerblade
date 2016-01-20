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

// state machine for configuration
typedef enum {
    CONF_NONE=0,
    CONF_SET_VALUES,
} ConfigurationState_t;

// state machine for startup
typedef enum {
    STARTUP_NONE=0,
    STARTUP_NOP,
    STARTUP_SET_SEQ,
    STARTUP_GET_CONF,
} StartupState_t;

// device status codes
typedef enum {
    STATUS_NONE=0,
    STATUS_BAD_CONFIG_SIZE,
    STATUS_NO_RS_START,
    STATUS_NO_RS_DATA,
    STATUS_NO_RS_QUIT,
} StatusCode_t;

#endif

